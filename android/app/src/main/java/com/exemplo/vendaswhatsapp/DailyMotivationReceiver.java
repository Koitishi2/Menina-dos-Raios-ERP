package com.exemplo.vendaswhatsapp;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

/** Shows the ERP's existing daily message once per local day. */
public final class DailyMotivationReceiver extends BroadcastReceiver {
    private static final String PREFS = "daily_motivation";
    private static final int REQUEST_ID = 7401;
    private static final String ACTION_DAILY = "com.exemplo.vendaswhatsapp.DAILY_MOTIVATION";

    @Override public void onReceive(Context context, Intent intent) {
        android.content.SharedPreferences prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (MainActivity.tokenAdminParaAlertas(context).isEmpty()) {
            cancelar(context);
            return;
        }
        String action = intent == null ? "" : intent.getAction();
        if (!ACTION_DAILY.equals(action)) {
            agendar(context, prefs.getString("time", "07:00"));
            return;
        }
        android.content.BroadcastReceiver.PendingResult pending = goAsync();
        new Thread(() -> {
            try { buscarEExibir(context, prefs); }
            catch (Exception e) { Log.w("DailyMotivation", "Não foi possível atualizar a mensagem diária", e); }
            finally { pending.finish(); agendar(context, prefs.getString("time", "07:00")); }
        }).start();
    }

    private static void buscarEExibir(Context context, android.content.SharedPreferences prefs) throws Exception {
        String token = tokenSistema(context);
        if (token.isEmpty()) return;
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) new URL(BuildConfig.SERVER_BASE_URL + "/api/mobile/daily-motivation").openConnection();
            connection.setRequestMethod("GET"); connection.setConnectTimeout(8000); connection.setReadTimeout(12000);
            connection.setRequestProperty("x-token", token); connection.setRequestProperty("Accept", "application/json");
            int status = connection.getResponseCode();
            if (status < 200 || status >= 300) return;
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (InputStream input = connection.getInputStream()) { byte[] buffer = new byte[2048]; int count; while ((count = input.read(buffer)) > 0) bytes.write(buffer, 0, count); }
            org.json.JSONObject json = new org.json.JSONObject(bytes.toString("UTF-8"));
            String message = json.optString("message", "").trim();
            String today = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(new Date());
            String time = json.optString("time", "07:00");
            prefs.edit().putString("message", message).putString("title", json.optString("title", "Mensagem do dia"))
                    .putString("date", today).putString("time", time).putBoolean("enabled", json.optBoolean("enabled", false)).apply();
            if (!json.optBoolean("enabled", false) || message.isEmpty() || today.equals(prefs.getString("last_sent", ""))) return;
            NotificationManager manager = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            if (manager == null || (Build.VERSION.SDK_INT >= 33 && context.checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) != android.content.pm.PackageManager.PERMISSION_GRANTED)) return;
            if (Build.VERSION.SDK_INT >= 26) manager.createNotificationChannel(new NotificationChannel("motivacao_diaria", "Mensagem motivacional", NotificationManager.IMPORTANCE_DEFAULT));
            Intent open = new Intent(context, MainActivity.class);
            PendingIntent content = PendingIntent.getActivity(context, REQUEST_ID, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder builder = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(context, "motivacao_diaria") : new Notification.Builder(context);
            manager.notify(REQUEST_ID, builder.setSmallIcon(android.R.drawable.ic_dialog_info).setContentTitle("Menina dos Raios · " + json.optString("title", "Mensagem do dia"))
                    .setContentText(message.length() > 110 ? message.substring(0, 107) + "..." : message)
                    .setStyle(new Notification.BigTextStyle().bigText(message)).setAutoCancel(true).setContentIntent(content).build());
            prefs.edit().putString("last_sent", today).apply();
        } finally { if (connection != null) connection.disconnect(); }
    }

    private static String tokenSistema(Context context) {
        try {
            MasterKey key = new MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build();
            android.content.SharedPreferences secure = EncryptedSharedPreferences.create(context, "auth_sistema_seguro", key,
                    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV, EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM);
            String token = secure.getString("token", ""); if (token != null && !token.trim().isEmpty()) return token.trim();
        } catch (Exception ignored) { }
        return context.getSharedPreferences("auth_sistema", Context.MODE_PRIVATE).getString("token", "").trim();
    }

    public static void agendar(Context context, String horario) {
        if (MainActivity.tokenAdminParaAlertas(context).isEmpty()) {
            cancelar(context);
            return;
        }
        int hora = 7, minuto = 0;
        try { String[] partes = (horario == null ? "07:00" : horario).split(":"); hora = Integer.parseInt(partes[0]); minuto = Integer.parseInt(partes[1]); }
        catch (Exception ignored) { }
        Calendar proximo = Calendar.getInstance();
        proximo.set(Calendar.HOUR_OF_DAY, hora); proximo.set(Calendar.MINUTE, minuto);
        proximo.set(Calendar.SECOND, 0); proximo.set(Calendar.MILLISECOND, 0);
        if (proximo.getTimeInMillis() <= System.currentTimeMillis()) proximo.add(Calendar.DAY_OF_YEAR, 1);
        Intent intent = new Intent(context, DailyMotivationReceiver.class).setAction(ACTION_DAILY);
        PendingIntent pi = PendingIntent.getBroadcast(context, REQUEST_ID, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarm == null) return;
        if (Build.VERSION.SDK_INT >= 23) alarm.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, proximo.getTimeInMillis(), pi);
        else alarm.set(AlarmManager.RTC_WAKEUP, proximo.getTimeInMillis(), pi);
    }

    public static void cancelar(Context context) {
        AlarmManager alarm = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        Intent intent = new Intent(context, DailyMotivationReceiver.class).setAction(ACTION_DAILY);
        PendingIntent pi = PendingIntent.getBroadcast(context, REQUEST_ID, intent,
                PendingIntent.FLAG_NO_CREATE | PendingIntent.FLAG_IMMUTABLE);
        if (pi != null) {
            if (alarm != null) alarm.cancel(pi);
            pi.cancel();
        }
    }
}
