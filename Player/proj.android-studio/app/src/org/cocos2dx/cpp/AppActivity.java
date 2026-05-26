package org.cocos2dx.cpp;

import org.cocos2dx.lib.Cocos2dxActivity;
import android.os.Bundle;
import android.util.Log;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import java.io.File;
import java.io.FileOutputStream;
import java.io.PrintWriter;
import java.io.StringWriter;

public class AppActivity extends Cocos2dxActivity {
    private static final String TAG = "HellAfterSchool";

    private File getDiagDir() {
        File d = getExternalFilesDir(null);
        if (d == null) d = getFilesDir();
        return d;
    }

    private void writeDiag(String fname, String content) {
        try {
            File f = new File(getDiagDir(), fname);
            FileOutputStream fos = new FileOutputStream(f, true);
            fos.write((System.currentTimeMillis() + " " + content + "\n").getBytes());
            fos.close();
            Log.i(TAG, "diag-> " + f.getAbsolutePath() + ": " + content);
        } catch (Throwable t) {
            Log.e(TAG, "writeDiag failed", t);
        }
    }

    @Override
    protected void onLoadNativeLibraries() {
        writeDiag("boot.log", "onLoadNativeLibraries: ENTER");
        String libName = "MyGame";
        try {
            ApplicationInfo ai = getPackageManager().getApplicationInfo(getPackageName(), PackageManager.GET_META_DATA);
            Bundle bundle = ai.metaData;
            libName = bundle.getString("android.app.lib_name");
            writeDiag("boot.log", "lib_name=" + libName);
        } catch (Throwable e) {
            writeDiag("boot.log", "metadata failed: " + e);
        }
        try {
            writeDiag("boot.log", "before System.loadLibrary(" + libName + ")");
            System.loadLibrary(libName);
            writeDiag("boot.log", "after loadLibrary: SUCCESS");
        } catch (Throwable t) {
            StringWriter sw = new StringWriter();
            t.printStackTrace(new PrintWriter(sw));
            writeDiag("boot.log", "loadLibrary FAILED: " + t);
            writeDiag("crash.log", "LOAD_FAILURE:\n" + sw.toString());
            throw new RuntimeException("native lib load failed", t);
        }
    }

    @Override
    protected void onCreate(final Bundle savedInstanceState) {
        writeDiag("boot.log", "onCreate ENTER");
        try {
            super.onCreate(savedInstanceState);
            writeDiag("boot.log", "onCreate super.onCreate done");
        } catch (Throwable t) {
            StringWriter sw = new StringWriter();
            t.printStackTrace(new PrintWriter(sw));
            writeDiag("boot.log", "onCreate FAILED: " + t);
            writeDiag("crash.log", "ONCREATE_FAILURE:\n" + sw.toString());
            throw new RuntimeException("onCreate failed", t);
        }
    }
}
