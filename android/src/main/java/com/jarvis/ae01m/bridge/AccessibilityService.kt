package com.jarvis.ae01m.bridge

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.view.accessibility.AccessibilityEvent
import android.content.Context
import android.content.Intent
import android.os.BatteryManager

/**
 * AccessibilityService — Android accessibility service implementation.
 *
 * Listens to system accessibility events and forwards them to
 * AndroidAccessibilityBridge for HDC context encoding.
 *
 * Must be declared in AndroidManifest.xml with BIND_ACCESSIBILITY_SERVICE permission.
 */
class AccessibilityService : AccessibilityService() {

    private var accessibilityBridge: AndroidAccessibilityBridge? = null
    private var sensoryAdapter: SensoryInputAdapter? = null

    override fun onServiceConnected() {
        super.onServiceConnected()

        // Initialize bridges
        accessibilityBridge = AndroidAccessibilityBridge(this)
        sensoryAdapter = SensoryInputAdapter(applicationContext)

        // Configure accessibility service info
        val info = AccessibilityServiceInfo().apply {
            eventTypeFilter = AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                    AccessibilityEvent.TYPE_ANNOUNCEMENT

            feedbackType = AccessibilityServiceInfo.FEEDBACK_VISUAL
            canRetrieveWindowContent = true
        }
        serviceInfo = info
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent) {
        accessibilityBridge?.onAccessibilityEvent(event)
    }

    override fun onInterrupt() {
        // Clean up resources on interruption
        sensoryAdapter?.cleanup()
    }

    /**
     * Start sensory monitoring (call after user grants permissions).
     */
    fun startSensoryMonitoring() {
        sensoryAdapter?.let { adapter ->
            adapter.setPythonBridge(PythonBridge(applicationContext))
            adapter.startAccelerometerMonitoring()
            adapter.startGyroscopeMonitoring()
            adapter.registerBatteryReceiver()
        }
    }

    /**
     * Start location monitoring (call after user grants location permission).
     */
    fun startLocationMonitoring() {
        sensoryAdapter?.startLocationMonitoring()
    }
}
