package com.jarvis.ae01m

import android.os.Bundle
import android.widget.TextView
import androidx.activity.ComponentActivity
import com.jarvis.ae01m.bridge.PythonBridge
import com.jarvis.ae01m.hdc.HdcCognitiveEngine

/**
 * MainActivity — JARVIS Mobile (AE01M Stage 21).
 *
 * Entry point for the Android APK. Initializes the Python/C++ JNI bridge
 * that loads the Stage 21 HDC Cognitive Model (10K-dim hypervectors) and
 * connects to the MobileSensoryBridge / MobileActionDecoder pipeline.
 */
class MainActivity : ComponentActivity() {

    private lateinit var statusText: TextView
    private var pythonBridge: PythonBridge? = null
    private var hdcEngine: HdcCognitiveEngine? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.status_text)

        // Initialize JNI bridge to Stage 21 model
        try {
            pythonBridge = PythonBridge(this)
            statusText.text = "AE01M Brain: JNI bridge connected"
        } catch (e: Exception) {
            statusText.text = "AE01M Brain: JNI bridge failed — $e"
            e.printStackTrace()
        }

        // Initialize HDC cognitive engine
        try {
            hdcEngine = HdcCognitiveEngine(hvDim = 10000)
            hdcEngine?.learnRule("battery_low", "notify")
            hdcEngine?.learnRule("app_in_background", "speak")
            statusText.text = "AE01M HDC: Rules loaded"
        } catch (e: Exception) {
            statusText.text = "AE01M HDC: Init failed — $e"
        }
    }

    override fun onResume() {
        super.onResume()
        // Trigger HDC context retrieval on resume
        hdcEngine?.retrieveContext("app_in_background")
    }
}
