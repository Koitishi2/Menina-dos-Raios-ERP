package com.exemplo.vendaswhatsapp;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.content.pm.PackageInstaller;
import android.os.Build;
import android.widget.Toast;

import java.io.File;

/** Recebe apenas o resultado do PackageInstaller enviado à PendingIntent desta instalação. */
public class AppInstallStatusReceiver extends BroadcastReceiver {
    @Override public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        int status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirmation;
            if (Build.VERSION.SDK_INT >= 33) {
                confirmation = intent.getParcelableExtra(Intent.EXTRA_INTENT, Intent.class);
            } else {
                // O instalador do Android fornece o Intent de confirmação nesta resposta.
                confirmation = intent.getParcelableExtra(Intent.EXTRA_INTENT);
            }
            if (confirmation != null) {
                confirmation.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(confirmation);
            } else {
                Toast.makeText(context, "Abra o instalador do Android para confirmar a atualização.", Toast.LENGTH_LONG).show();
            }
            return;
        }
        if (status == PackageInstaller.STATUS_SUCCESS) {
            Toast.makeText(context, "Atualização instalada com sucesso.", Toast.LENGTH_LONG).show();
            return;
        }
        String detail = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
        String error = "Falha na instalação (código Android " + status + ")";
        if (detail != null && !detail.trim().isEmpty()) error += ": " + detail.trim();
        String apkName = intent.getStringExtra("update_apk_name");
        if (abrirInstaladorPadrao(context, apkName)) {
            Toast.makeText(context, error + ". Abrimos a confirmação padrão do Android.", Toast.LENGTH_LONG).show();
            return;
        }
        Toast.makeText(context, error, Toast.LENGTH_LONG).show();
    }

    private boolean abrirInstaladorPadrao(Context context, String apkName) {
        if (apkName == null || apkName.contains("/") || apkName.contains("\\") || apkName.contains("..")) return false;
        File apk = new File(new File(context.getCacheDir(), "updates"), apkName);
        if (!apk.isFile() || apk.length() == 0) return false;
        Uri uri = new Uri.Builder()
            .scheme("content")
            .authority(context.getPackageName() + ".files")
            .appendPath("updates")
            .appendPath(apkName)
            .build();
        Intent install = new Intent(Intent.ACTION_INSTALL_PACKAGE);
        install.setData(uri);
        install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
        try {
            context.startActivity(install);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }
}
