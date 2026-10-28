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

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.NumberFormat;
import java.util.Calendar;
import java.util.Locale;

public class NewTempoCollectionReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "cobrancas_novo_tempo_v1";
    private static final int REQUEST_CODE = 6819;
    private static final int NOTIFICATION_ID = 6820;
    private static final int[] HORARIOS = {8, 12, 16, 20};

    @Override public void onReceive(Context context, Intent intent) {
        if (intent != null && Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction())) {
            if (MainActivity.tokenAdminParaAlertas(context).isEmpty()) cancelar(context);
            else agendar(context);
            return;
        }
        String token = MainActivity.tokenAdminParaAlertas(context);
        if (token.isEmpty()) {
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
        alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, proximoHorario().getTimeInMillis(), pending);
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
            if (base == null || base.trim().isEmpty()) return;
            connection = (HttpURLConnection) new URL(base + "/api/mobile/new-tempo/collections").openConnection();
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(20000);
            connection.setRequestProperty("x-token", token);
            if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) return;
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
            if (due > 0 && token.equals(MainActivity.tokenAdminParaAlertas(context))) notificar(context, due, total, branches.toString(), token);
        } catch (Exception ignored) {
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private static void notificar(Context context, int quantidade, double total, String filiais, String token) {
        if (Build.VERSION.SDK_INT >= 33 && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return;
        NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, "Cobranças Novo Tempo", NotificationManager.IMPORTANCE_HIGH);
            channel.setDescription("Lembretes de vendas Novo Tempo ainda pendentes");
            manager.createNotificationChannel(channel);
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
        if (token.equals(MainActivity.tokenAdminParaAlertas(context))) manager.notify(NOTIFICATION_ID, notification.build());
    }
}
