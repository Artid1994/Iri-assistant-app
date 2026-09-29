package com.jarvis.ae01m

import android.app.Application
import android.util.Log

/**
 * JARVISApplication — Global application entry point.
 *
 * AndroidManifest.xml references this class via android:name=".JARVISApplication".
 * This is called BEFORE any Activity starts, so we must be extremely careful
 * NOT to do heavy initialization here (no System.loadLibrary, no Python.start()).
 *
 * All heavy work is deferred to MainActivity's onWindowFocusChanged + user button tap.
 */
class JARVISApplication : Application() {

    companion object {
        private const val TAG = "JARVISApp"
    }

    override fun onCreate() {
        super.onCreate()
        // Only lightweight, safe operations here:
        // - No JNI library loading
        // - No Python runtime start
        // - No model loading
        Log.d(TAG, "JARVISApplication created — deferring all heavy init to MainActivity")
    }
}
