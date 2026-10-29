package com.exemplo.vendaswhatsapp;

import android.Manifest;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.NumberFormat;
import java.util.Calendar;
import java.util.Locale;
import java.text.SimpleDateFormat;
import java.util.Date;

public class NewTempoCollectionReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "cobrancas_novo_tempo_v1";
    private static final int REQUEST_CODE = 6819;
    private static final int NOTIFICATION_ID = 6820;
    private static final int[] HORARIOS = {8, 12, 16, 20};
    private static final String PREFS = "new_tempo_notification_status";
    private static final String TAG = "NovoTempoAlerts";

    @Override public void onReceive(Context context, Intent intent) {
        String action = intent == null ? null : intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action)
            || Intent.ACTION_USER_UNLOCKED.equals(action)
            || Intent.ACTION_TIME_CHANGED.equals(action)
            || Intent.ACTION_TIMEZONE_CHANGED.equals(action)) {
            if (MainActivity.tokenAdminParaAlertas(context).isEmpty()) cancelar(context);
            else agendar(context);
            return;
        }
        String token = MainActivity.tokenAdminParaAlertas(context);
        if (token.isEmpty()) {
            registrarEstado(context, "Verificação ignorada: requer sessão de administrador ativa.");
            cancelar(context);
            return;
        }
        agendar(context);
        final PendingResult pending = goAsync();
        new Thread(() -> {
            try { consultarECriarAviso(context, token); }
            finally { pending.finish(); }
        }).start();
    }

    public static void agendar(Context context) {
        if (MainActivity.tokenAdminParaAlertas(context).isEmpty()) { cancelar(context); return; }
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarm == null) return;
        Intent intent = new Intent(context, NewTempoCollectionReceiver.class);
        PendingIntent pending = PendingIntent.getBroadcast(context, REQUEST_CODE, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Calendar proximo = proximoHorario();
        alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, proximo.getTimeInMillis(), pending);
        Log.i(TAG, "Próxima verificação agendada para " + new SimpleDateFormat("dd/MM HH:mm", new Locale("pt", "BR")).format(proximo.getTime()));
    }

    public static void cancelar(Context context) {
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarm == null) return;
        Intent intent = new Intent(context, NewTempoCollectionReceiver.class);
        PendingIntent pending = PendingIntent.getBroadcast(context, REQUEST_CODE, intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        alarm.cancel(pending);
        pending.cancel();
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager != null) manager.cancel(NOTIFICATION_ID);
    }

    private static Calendar proximoHorario() {
        Calendar agora = Calendar.getInstance();
        Calendar proximo = (Calendar) agora.clone();
        for (int hora : HORARIOS) {
            proximo.set(Calendar.HOUR_OF_DAY, hora);
            proximo.set(Calendar.MINUTE, 0);
            proximo.set(Calendar.SECOND, 0);
            proximo.set(Calendar.MILLISECOND, 0);
            if (proximo.after(agora)) return proximo;
        }
        proximo.add(Calendar.DAY_OF_MONTH, 1);
        proximo.set(Calendar.HOUR_OF_DAY, HORARIOS[0]);
        proximo.set(Calendar.MINUTE, 0);
        proximo.set(Calendar.SECOND, 0);
        proximo.set(Calendar.MILLISECOND, 0);
        return proximo;
    }

    private static void consultarECriarAviso(Context context, String token) {
        HttpURLConnection connection = null;
        try {
            String base = BuildConfig.SERVER_BASE_URL;
            if (base == null || base.trim().isEmpty()) {
                registrarEstado(context, "Não foi possível verificar: endereço do servidor ausente no APK.");
                return;
            }
            connection = (HttpURLConnection) new URL(base + "/api/mobile/new-tempo/collections").openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(20000);
            connection.setRequestProperty("x-token", token);
            int responseCode = connection.getResponseCode();
            if (responseCode != HttpURLConnection.HTTP_OK) {
                registrarEstado(context, responseCode == HttpURLConnection.HTTP_FORBIDDEN || responseCode == HttpURLConnection.HTTP_UNAUTHORIZED
                    ? "Não foi possível verificar: a sessão admin expirou. Entre novamente no APK."
                    : "Não foi possível consultar o servidor (HTTP " + responseCode + ").");
                Log.w(TAG, "A API de cobranças respondeu HTTP " + responseCode);
                return;
            }
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            try (InputStream input = connection.getInputStream()) {
                byte[] buffer = new byte[4096];
                int count;
                while ((count = input.read(buffer)) != -1) output.write(buffer, 0, count);
            }
            JSONArray rows = new JSONArray(output.toString("UTF-8"));
            int due = 0;
            double total = 0;
            StringBuilder branches = new StringBuilder();
            for (int i = 0; i < rows.length(); i++) {
                JSONObject row = rows.optJSONObject(i);
                if (row == null || !row.optBoolean("notifications_due", false)
                    || "pago".equalsIgnoreCase(row.optString("status", "pendente"))) continue;
                due++;
                total += row.optDouble("total", 0);
                if (branches.length() < 130) {
                    if (branches.length() > 0) branches.append(" · ");
                    branches.append(row.optString("client", "Novo Tempo"));
                }
            }
            if (due == 0) {
                registrarEstado(context, "Verificado em " + horarioAgora() + ": nenhuma cobrança entregue está no horário de aviso.");
            } else if (token.equals(MainActivity.tokenAdminParaAlertas(context))) {
                notificar(context, due, total, branches.toString(), token);
            } else {
                registrarEstado(context, "Aviso cancelado: a sessão admin mudou durante a consulta.");
            }
        } catch (Exception error) {
            registrarEstado(context, "Falha ao consultar o servidor em " + horarioAgora() + ". Confira a conexão e a sessão admin.");
            Log.e(TAG, "Falha ao consultar cobranças Novo Tempo", error);
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static void notificar(Context context, int quantidade, double total, String filiais, String token) {
        if (Build.VERSION.SDK_INT >= 33 && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            registrarEstado(context, "Aviso não enviado: permissão de notificações desativada no Android.");
            Log.w(TAG, "Permissão POST_NOTIFICATIONS não concedida");
            return;
        }
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) {
            registrarEstado(context, "Aviso não enviado: serviço de notificações indisponível.");
            return;
        }
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "Cobranças Novo Tempo", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Lembretes de vendas Novo Tempo ainda pendentes");
            manager.createNotificationChannel(channel);
        }
        if (!manager.areNotificationsEnabled()) {
            registrarEstado(context, "Aviso não enviado: notificações do APK estão bloqueadas nas configurações do celular.");
            Log.w(TAG, "Notificações do aplicativo desativadas no sistema");
            return;
        }
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = manager.getNotificationChannel(CHANNEL_ID);
            if (channel != null && channel.getImportance() == NotificationManager.IMPORTANCE_NONE) {
                registrarEstado(context, "Aviso não enviado: canal Cobranças Novo Tempo está bloqueado nas configurações.");
                Log.w(TAG, "Canal de notificações Novo Tempo desativado no sistema");
                return;
            }
        }
        Intent abrir = new Intent(context, MainActivity.class);
        abrir.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent abrirApp = PendingIntent.getActivity(context, REQUEST_CODE + 1, abrir,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        String valor = NumberFormat.getCurrencyInstance(new Locale("pt", "BR")).format(total);
        String texto = quantidade + (quantidade == 1 ? " venda entregue pendente" : " vendas entregues pendentes") + " · " + valor;
        Notification.Builder notification = Build.VERSION.SDK_INT >= 26
            ? new Notification.Builder(context, CHANNEL_ID) : new Notification.Builder(context);
        notification.setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("Cobrança Novo Tempo · notas entregues")
            .setContentText(texto)
            .setStyle(new Notification.BigTextStyle().bigText(texto + (filiais.isEmpty() ? "" : "\n" + filiais)))
            .setContentIntent(abrirApp).setAutoCancel(true)
            .setPriority(Notification.PRIORITY_HIGH)
            .setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_VIBRATE);
        if (token.equals(MainActivity.tokenAdminParaAlertas(context))) {
            manager.notify(NOTIFICATION_ID, notification.build());
            registrarEstado(context, "Aviso enviado em " + horarioAgora() + ": " + quantidade + (quantidade == 1 ? " cobrança pendente." : " cobranças pendentes."));
            Log.i(TAG, "Notificação enviada para " + quantidade + " cobrança(s) pendente(s)");
        }
    }

    static String estadoUltimaVerificacao(Context context) {
        long timestamp = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getLong("last_check", 0L);
        String resultado = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getString("last_result", "Ainda não há uma verificação de notificação registrada neste celular.");
        if (timestamp == 0L) return resultado;
        return "Última verificação " + new SimpleDateFormat("dd/MM HH:mm", new Locale("pt", "BR")).format(new Date(timestamp)) + " · " + resultado;
    }

    private static String horarioAgora() {
        return new SimpleDateFormat("dd/MM HH:mm", new Locale("pt", "BR")).format(new Date());
    }

    private static void registrarEstado(Context context, String resultado) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putLong("last_check", System.currentTimeMillis())
            .putString("last_result", resultado)
            .apply();
    }
}
