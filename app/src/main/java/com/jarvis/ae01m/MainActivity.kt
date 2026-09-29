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
 */
class MainActivity : ComponentActivity() {

    private lateinit var statusText: TextView
    private var pythonBridge: PythonBridge? = null
    private var hdcEngine: HdcCognitiveEngine? = null
    private var isInitializing = false

    companion object {
        private const val CRASH_LOG_FILENAME = "crash_log.txt"
        private const val MODEL_ASSET = "iri_brain_v6_1m_trained_phase1_phase2.bin"
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.status_text)

        // Set up global uncaught exception handler
        setupCrashHandler()

        // Show initial UI immediately
        statusText.text = "AE01M: Initializing..."

        // Initialize Python bridge and HDC engine asynchronously on IO thread
        lifecycleScope.launch(Dispatchers.IO) {
            isInitializing = true
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
        // PythonBridge.init() would call Python.start() via Chaquopy if needed
        // The model loading happens inside PythonBridge constructor (loadModel())
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
