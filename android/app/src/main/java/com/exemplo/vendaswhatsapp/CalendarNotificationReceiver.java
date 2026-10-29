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
import android.media.AudioAttributes;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

public class CalendarNotificationReceiver extends BroadcastReceiver {
    private static final String CHANNEL_ID = "calendario_monteiro_push_v2";
    private static final int REQUEST_CODE = 2207;
    private static final int NOTIFICATION_BASE_ID = 770100;
    private static final String ACTION_STOP_TODAY = "br.com.meninadosraios.vendas.STOP_CALENDAR_TODAY";
    private static final String EXTRA_EVENT_ID = "event_id";
    private static final String ALL_EVENTS = "__all__";
    private static final int[] HORARIOS = {9, 13, 17, 21};

    @Override public void onReceive(Context context, Intent intent) {
        String action = intent == null ? null : intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action)
            || Intent.ACTION_USER_UNLOCKED.equals(action)
            || Intent.ACTION_TIME_CHANGED.equals(action)
            || Intent.ACTION_TIMEZONE_CHANGED.equals(action)
            || Intent.ACTION_MY_PACKAGE_REPLACED.equals(action)) {
            if (MainActivity.tokenAdminParaAlertas(context).isEmpty()) cancelar(context);
            else agendar(context);
            return;
        }
        String token = MainActivity.tokenAdminParaAlertas(context);
        if (token.isEmpty()) { cancelar(context); return; }
        if (intent != null && ACTION_STOP_TODAY.equals(intent.getAction())) {
            pararHoje(context, intent.getStringExtra(EXTRA_EVENT_ID));
            return;
        }
        agendar(context);
        final PendingResult pending = goAsync();
        new Thread(() -> {
            try {
                JSONArray eventos = baixarEventos(token);
                JSONArray filtrados = filtrarEventosNotificaveis(context, eventos);
                if (filtrados.length() > 0) {
                    notificar(context, filtrados, token);
                    registrarEnvios(context, filtrados);
                }
            } catch (Exception ignored) { }
            finally { pending.finish(); }
        }).start();
    }

    public static void agendar(Context context) {
        if (MainActivity.tokenAdminParaAlertas(context).isEmpty()) { cancelar(context); return; }
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarm == null) return;
        Intent i = new Intent(context, CalendarNotificationReceiver.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, REQUEST_CODE, i,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Calendar agora = Calendar.getInstance();
        Calendar proximo = (Calendar) agora.clone();
        for (int hora : HORARIOS) {
            proximo.set(Calendar.HOUR_OF_DAY, hora);
            proximo.set(Calendar.MINUTE, 0);
            proximo.set(Calendar.SECOND, 0);
            proximo.set(Calendar.MILLISECOND, 0);
            if (proximo.after(agora)) break;
        }
        if (!proximo.after(agora)) {
            proximo.add(Calendar.DAY_OF_MONTH, 1);
            proximo.set(Calendar.HOUR_OF_DAY, HORARIOS[0]);
            proximo.set(Calendar.MINUTE, 0);
            proximo.set(Calendar.SECOND, 0);
            proximo.set(Calendar.MILLISECOND, 0);
        }
        alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, proximo.getTimeInMillis(), pi);
    }

    public static void cancelar(Context context) {
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        PendingIntent pi = PendingIntent.getBroadcast(context, REQUEST_CODE,
            new Intent(context, CalendarNotificationReceiver.class),
            PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
        if (pi != null) {
            if (alarm != null) alarm.cancel(pi);
            pi.cancel();
        }
        NotificationManager nm = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null) for (android.service.notification.StatusBarNotification aviso : nm.getActiveNotifications()) {
            int id = aviso.getId();
            if (id >= NOTIFICATION_BASE_ID && id < NOTIFICATION_BASE_ID + 100000) nm.cancel(id);
        }
    }

    private static JSONArray baixarEventos(String token) throws Exception {
        HttpURLConnection conexao = null;
        try {
            conexao = (HttpURLConnection) new URL(MainActivity.APP_CALENDAR_URL).openConnection();
            conexao.setRequestMethod("GET");
            conexao.setConnectTimeout(12000);
            conexao.setReadTimeout(30000);
            conexao.setRequestProperty("Cache-Control", "no-cache");
            conexao.setRequestProperty("x-token", token);
            int status = conexao.getResponseCode();
            if (status < 200 || status >= 300) return new JSONArray();
            String json = new String(ler(conexao), "UTF-8");
            JSONObject body = new JSONObject(json);
            JSONArray eventos = body.optJSONArray("events");
            return eventos == null ? new JSONArray() : eventos;
        } finally {
            if (conexao != null) conexao.disconnect();
        }
    }

    private static byte[] ler(HttpURLConnection conexao) throws Exception {
        try (BufferedInputStream entrada = new BufferedInputStream(conexao.getInputStream());
             ByteArrayOutputStream saida = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int lidos;
            while ((lidos = entrada.read(buffer)) != -1) saida.write(buffer, 0, lidos);
            return saida.toByteArray();
        }
    }

    private static void notificar(Context context, JSONArray eventos, String token) throws Exception {
        if (!token.equals(MainActivity.tokenAdminParaAlertas(context))) return;
        NotificationManager nm = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm == null) return;
        if (Build.VERSION.SDK_INT >= 33 &&
            context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return;

        Uri som = Settings.System.DEFAULT_NOTIFICATION_URI;
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel canal = new NotificationChannel(CHANNEL_ID, "Calendario Monteiro - avisos", NotificationManager.IMPORTANCE_HIGH);
            canal.setDescription("Avisos sonoros do calendario interno do Monteiro");
            canal.enableVibration(true);
            canal.setVibrationPattern(new long[]{0, 350, 180, 350});
            canal.setSound(som, new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .build());
            canal.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
            nm.createNotificationChannel(canal);
        }

        for (int i = 0; i < eventos.length(); i++) {
            JSONObject evento = eventos.optJSONObject(i);
            if (evento == null) continue;
            String eventId = evento.optString("id", "");
            if (eventId.isEmpty()) continue;
            int notificationId = notificationId(eventId);
            String titulo = evento.optString("title", "Notificacao do calendario");
            String texto = resumo(evento);

            Intent abrir = new Intent(context, MainActivity.class);
            abrir.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            abrir.putExtra(MainActivity.EXTRA_OPEN_CALENDAR_NOTIFICATIONS, true);
            PendingIntent abrirPi = PendingIntent.getActivity(context, 3307 + Math.abs(eventId.hashCode() % 100000), abrir,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

            Intent parar = new Intent(context, CalendarNotificationReceiver.class);
            parar.setAction(ACTION_STOP_TODAY);
            parar.putExtra(EXTRA_EVENT_ID, eventId);
            PendingIntent pararPi = PendingIntent.getBroadcast(context, 4407 + Math.abs(eventId.hashCode() % 100000), parar,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

            Intent abrirCalendario = new Intent(context, MainActivity.class);
            abrirCalendario.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            abrirCalendario.putExtra(MainActivity.EXTRA_OPEN_CALENDAR_NOTIFICATIONS, true);
            PendingIntent abrirCalendarioPi = PendingIntent.getActivity(context, 5507 + Math.abs(eventId.hashCode() % 100000), abrirCalendario,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

            android.app.Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new android.app.Notification.Builder(context, CHANNEL_ID)
                : new android.app.Notification.Builder(context);
            b.setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(titulo)
                .setContentText(texto)
                .setStyle(new android.app.Notification.BigTextStyle().setBigContentTitle(titulo).bigText(texto).setSummaryText("Calendário · lembrete"))
                .setContentIntent(abrirPi)
                .setAutoCancel(true)
                .setOngoing(false)
                .setOnlyAlertOnce(false)
                .setPriority(Notification.PRIORITY_HIGH)
                .setDefaults(Notification.DEFAULT_SOUND | Notification.DEFAULT_VIBRATE | Notification.DEFAULT_LIGHTS)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .addAction(android.R.drawable.ic_menu_view, "Abrir calendário", abrirCalendarioPi)
                .addAction(android.R.drawable.ic_menu_close_clear_cancel, "Parar hoje", pararPi);
            if (!token.equals(MainActivity.tokenAdminParaAlertas(context))) return;
            nm.notify(notificationId, b.build());
        }
    }

    private static String resumo(JSONObject e) {
        String data = dataLegivel(e.optString("due_date", ""));
        String detalhes = e.optString("details", "").trim();
        String dias = e.optInt("days_left", 0) == 0 ? "Hoje" : "Faltam " + e.optInt("days_left", 0) + " dia(s)";
        String texto = (data.isEmpty() ? dias : data + " - " + dias);
        if (!detalhes.isEmpty()) texto += "\n" + detalhes;
        return texto;
    }

    private static String dataLegivel(String valor) {
        if (valor == null || valor.trim().isEmpty()) return "";
        try {
            Date data = new SimpleDateFormat("yyyy-MM-dd", Locale.US).parse(valor.trim());
            return data == null ? valor : new SimpleDateFormat("dd/MM/yyyy", new Locale("pt", "BR")).format(data);
        } catch (Exception ignored) {
            return valor;
        }
    }

    private static JSONArray filtrarEventosNotificaveis(Context context, JSONArray eventos) throws Exception {
        JSONArray saida = new JSONArray();
        for (int i = 0; i < eventos.length(); i++) {
            JSONObject e = eventos.optJSONObject(i);
            if (e == null) continue;
            String id = e.optString("id", "");
            if (id.isEmpty()) continue;
            if (estaParadoHoje(context, id) || estaParadoHoje(context, ALL_EVENTS)) continue;
            int limite = Math.max(1, Math.min(12, e.optInt("reminders_per_day", 4)));
            if (enviosHoje(context, id) >= limite) continue;
            saida.put(e);
        }
        return saida;
    }

    private static void registrarEnvios(Context context, JSONArray eventos) {
        String hoje = hoje();
        android.content.SharedPreferences.Editor ed = context.getSharedPreferences("calendario_notificacoes", Context.MODE_PRIVATE).edit();
        for (int i = 0; i < eventos.length(); i++) {
            JSONObject e = eventos.optJSONObject(i);
            if (e == null) continue;
            String id = e.optString("id", "");
            if (id.isEmpty()) continue;
            String key = "sent_" + hoje + "_" + id;
            ed.putInt(key, enviosHoje(context, id) + 1);
        }
        ed.apply();
    }

    private static int enviosHoje(Context context, String id) {
        return context.getSharedPreferences("calendario_notificacoes", Context.MODE_PRIVATE)
            .getInt("sent_" + hoje() + "_" + id, 0);
    }

    private static boolean estaParadoHoje(Context context, String id) {
        return context.getSharedPreferences("calendario_notificacoes", Context.MODE_PRIVATE)
            .getBoolean("stop_" + hoje() + "_" + id, false);
    }

    private static void pararHoje(Context context, String id) {
        if (id == null || id.trim().isEmpty()) id = ALL_EVENTS;
        context.getSharedPreferences("calendario_notificacoes", Context.MODE_PRIVATE).edit()
            .putBoolean("stop_" + hoje() + "_" + id, true)
            .apply();
        NotificationManager nm = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (nm != null) {
            if (ALL_EVENTS.equals(id)) nm.cancelAll();
            else nm.cancel(notificationId(id));
        }
    }

    private static String hoje() {
        return new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
    }

    private static int notificationId(String eventId) {
        return NOTIFICATION_BASE_ID + Math.abs(eventId.hashCode() % 100000);
    }
}
