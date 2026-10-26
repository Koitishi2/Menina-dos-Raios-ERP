package com.exemplo.vendaswhatsapp;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;

import java.io.File;
import java.io.FileNotFoundException;

public class CsvProvider extends ContentProvider {
    @Override public boolean onCreate() { return true; }

    private File arquivo(Uri uri) throws FileNotFoundException {
        String nome = uri.getLastPathSegment();
        if (nome == null || nome.contains("/") || nome.contains("\\") || nome.contains(".."))
            throw new FileNotFoundException("Arquivo inválido");
        String pasta = uri.getPathSegments().size() > 1 ? uri.getPathSegments().get(0) : "pedidos";
        if (!pasta.equals("pedidos") && !pasta.equals("updates"))
            throw new FileNotFoundException("Pasta inválida");
        File file = new File(new File(getContext().getCacheDir(), pasta), nome);
        if (!file.exists()) throw new FileNotFoundException(nome);
        return file;
    }

    @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        return ParcelFileDescriptor.open(arquivo(uri), ParcelFileDescriptor.MODE_READ_ONLY);
    }

    @Override public String getType(Uri uri) {
        String nome = uri.getLastPathSegment();
        return nome != null && nome.toLowerCase().endsWith(".apk")
            ? "application/vnd.android.package-archive" : "text/csv";
    }

    @Override public Cursor query(Uri uri, String[] projection, String selection,
                                  String[] selectionArgs, String sortOrder) {
        try {
            File file = arquivo(uri);
            MatrixCursor cursor = new MatrixCursor(new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE});
            cursor.addRow(new Object[]{file.getName(), file.length()});
            return cursor;
        } catch (FileNotFoundException e) { return null; }
    }

    @Override public int delete(Uri uri, String s, String[] a) { return 0; }
    @Override public int update(Uri uri, ContentValues v, String s, String[] a) { return 0; }
    @Override public Uri insert(Uri uri, ContentValues v) { return null; }
}
