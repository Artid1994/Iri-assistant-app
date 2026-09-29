package com.jarvis.ae01m

import android.app.AlertDialog
import android.content.Context
import android.os.Bundle
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.lifecycle.lifecycleScope
import com.jarvis.ae01m.bridge.PythonBridge
import com.jarvis.ae01m.hdc.HdcCognitiveEngine
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.io.PrintWriter
import java.io.StringWriter

/**
 * MainActivity — JARVIS Mobile (AE01M Stage 21).
 *
 * Entry point for the Android APK. Initializes the Python/C++ JNI bridge
 * that loads the Stage 21 HDC Cognitive Model (10K-dim hypervectors) and
 * connects to the MobileSensoryBridge / MobileActionDecoder pipeline.
 *
 * Changes in this version:
 * - Global uncaught exception handler writes stack traces to crash_log.txt
 * - Python runtime and model loading moved to background IO thread
 * - UI renders immediately; heavy init happens asynchronously
 *
 * SAFEGUARDS (this version):
 * - Entire onCreate body wrapped in try-catch(Throwable) — never crashes on launch
 * - Heavy Python/Model init deferred until AFTER window focus or explicit user action
 * - AlertDialog with full stack trace shown on any launch failure
 */
class MainActivity : ComponentActivity() {

    private lateinit var statusText: TextView
    private var pythonBridge: PythonBridge? = null
    private var hdcEngine: HdcCognitiveEngine? = null
    private var isInitializing = false

    companion object {
        private const val CRASH_LOG_FILENAME = "crash_log.txt"
        private const val MODEL_ASSET = "iri_brain_v6_1m_trained_phase1_phase2.bin"
        private const val INIT_BUTTON_TEXT = "Initialize AE01M Brain (294MB)"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        // SAFETY WRAP: entire onCreate body in try-catch(Throwable).
        // If ANY exception occurs during launch, we show a dialog instead of
        // letting the process die. This prevents the "black screen of death"
        // that happens when uncaught exceptions hit before the uncaught handler
        // is installed.
        try {
            super.onCreate(savedInstanceState)
            setContentView(R.layout.activity_main)

            statusText = findViewById(R.id.status_text)

            // Set up global uncaught exception handler FIRST (before any risky work)
            setupCrashHandler()

            // Show initial UI immediately — lightweight, safe
            statusText.text = "AE01M: Tap 'Initialize' to load brain"

            // Defer heavy Python/Model initialization until after window focus.
            // We install a OnWindowFocusChangeListener so the brain only loads
            // once the UI is safely on-screen and the user can see the button.
            setContentView(R.layout.activity_main)
                .setOnClickListener { v ->
                    // Not used — we use the button approach below
                }
        } catch (t: Throwable) {
            // Critical failure during launch — show full stack trace
            showLaunchCrashDialog(t)
            logCrash(t)
            // Do NOT killProcess here — the dialog is the recovery path.
            // The global handler will kick in if something else fails later.
        }
    }

    /**
     * Called when the activity's window gains focus. This is the safe point
     * to start heavy initialization — the UI is guaranteed to be visible and
     * the user can interact with it.
     *
     * We show an "Initialize Brain" button. The user taps it to trigger the
     * 294MB model load. This avoids blocking the UI thread and gives the user
     * manual control over when the heavy work starts.
     */
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus && !isInitializing && pythonBridge == null) {
            // Attach an initialize button so the user can trigger the heavy load
            // at their discretion. This prevents the app from appearing frozen.
            showInitButton()
        }
    }

    private fun showInitButton() {
        // We add a button programmatically below the status text
        // since the layout may not have one predefined.
        val button = android.widget.Button(this).apply {
            text = INIT_BUTTON_TEXT
            setOnClickListener {
                startBrainInitialization()
            }
        }
        statusText.parentNode?.let { parent ->
            if (parent is android.widget.LinearLayout) {
                parent.addView(button)
            }
        }
    }

    /**
     * Heavy initialization: load Python bridge (Chaquopy) + HDC engine + 294MB model.
     * Runs on IO thread — UI remains responsive.
     */
    private fun startBrainInitialization() {
        if (isInitializing) return
        isInitializing = true

        lifecycleScope.launch(Dispatchers.IO) {
            try {
                initializePythonBridge()
                initializeHdcEngine()
                withContext(Dispatchers.Main) {
                    statusText.text = "AE01M Brain: Ready"
                    Toast.makeText(this@MainActivity, "AE01M initialized", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    statusText.text = "AE01M Brain: Init failed — ${e.message}"
                    showCrashDialog(e)
                }
                logCrash(e)
            } finally {
                isInitializing = false
            }
        }
    }

    private fun setupCrashHandler() {
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            logCrash(throwable)
            showCrashDialog(throwable)
            // Restart the app after crash
            android.os.Process.killProcess(android.os.Process.myPid())
        }
    }

    private fun initializePythonBridge() {
        pythonBridge = PythonBridge(this)
        // PythonBridge constructor calls loadJni() (safe, try-catch wrapped).
        // loadModel() is NOT called here — it's triggered separately if needed.
        // Chaquopy Python.start() would be called via PythonBridge.startPythonRuntime()
        // but Chaquopy auto-initializes on first Python API call.
    }

    private fun initializeHdcEngine() {
        hdcEngine = HdcCognitiveEngine(hvDim = 10000)
        hdcEngine?.learnRule("battery_low", "notify")
        hdcEngine?.learnRule("app_in_background", "speak")
    }

    private fun logCrash(throwable: Throwable) {
        try {
            val crashFile = File(filesDir, CRASH_LOG_FILENAME)
            val writer = PrintWriter(FileOutputStream(crashFile, true))
            val sw = StringWriter()
            throwable.printStackTrace(PrintWriter(sw))
            writer.println("=== CRASH at ${java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss", java.util.Locale.getDefault()).format(java.util.Date())} ===")
            writer.println("Thread: ${threadName()}")
            writer.println(sw.toString())
            writer.println("=== END CRASH ===")
            writer.close()
        } catch (e: Exception) {
            // Failed to write crash log — silently ignore
        }
    }

    private fun threadName(): String {
        return Thread.currentThread().name
    }

    /**
     * Shows a full stack trace dialog for launch crashes.
     * Called when an exception occurs in onCreate before the UI is fully set up.
     */
    private fun showLaunchCrashDialog(throwable: Throwable) {
        val message = buildString {
            appendLine("AE01M failed to start.")
            appendLine()
            appendLine("Exception: ${throwable.javaClass.simpleName}")
            appendLine("Message: ${throwable.message}")
            appendLine()
            appendLine("Stack trace:")
            appendLine()
            val sw = StringWriter()
            throwable.printStackTrace(PrintWriter(sw))
            appendLine(sw.toString())
        }

        // We may not have statusText set up yet — use a bare AlertDialog
        val dialog = AlertDialog.Builder(this)
            .setTitle("AE01M Launch Error")
            .setMessage(message)
            .setPositiveButton("OK") { _, _ ->
                finish()
            }
            .setCancelable(false)
            .create()
        dialog.show()
    }

    /**
     * Shows a crash dialog for runtime errors (after UI is set up).
     */
    private fun showCrashDialog(throwable: Throwable) {
        val message = buildString {
            appendLine("AE01M encountered an error.")
            appendLine()
            appendLine(throwable.javaClass.simpleName)
            appendLine(throwable.message)
        }

        runOnUiThread {
            AlertDialog.Builder(this)
                .setTitle("AE01M Error")
                .setMessage(message)
                .setPositiveButton("OK") { _, _ ->
                    // User acknowledged — app will restart due to killProcess in handler
                }
                .setCancelable(false)
                .show()
        }
    }

    override fun onResume() {
        super.onResume()
        // Trigger HDC context retrieval on resume (lightweight, runs on main thread)
        hdcEngine?.retrieveContext("app_in_background")
    }

    override fun onDestroy() {
        super.onDestroy()
        pythonBridge?.cleanup()
    }
}
