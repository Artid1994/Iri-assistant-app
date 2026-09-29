package com.jarvis.ae01m.bridge

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.view.accessibility.AccessibilityEvent
import android.content.Context
import android.content.Intent
import android.os.BatteryManager
import android.content.ComponentName

/**
 * AndroidAccessibilityBridge — captures system-level events for HDC context.
 *
 * Monitors:
 *   - App foreground/background transitions
 *   - Notification events
 *   - Battery low state
 *   - Screen on/off
 *
 * Bridges events to HDC context vectors via PythonBridge.
 */
class AndroidAccessibilityBridge(
    private val service: AccessibilityService
) {

    companion object {
        private const val EVENT_TYPE_NOTIFICATION = 0x00000001
        private const val EVENT_TYPE_BATTERY_LOW = 0x00000002
        private const val EVENT_TYPE_APP_FOREGROUND = 0x00000004
        private const val EVENT_TYPE_APP_BACKGROUND = 0x00000008
    }

    private val context: Context = service.applicationContext
    private var pythonBridge: PythonBridge? = null

    init {
        // Configure accessibility service
        configureAccessibility()
    }

    private fun configureAccessibility() {
        val info = AccessibilityServiceInfo().apply {
            eventTypeFilter = AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED or
                    AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED or
                    AccessibilityEvent.TYPE_ANNOUNCEMENT

            // Listen to all apps for context events
            canRetrieveWindowContent = true
        }
        service.info = info
    }

    /**
     * Connect to PythonBridge for HDC event encoding.
     */
    fun setPythonBridge(bridge: PythonBridge) {
        this.pythonBridge = bridge
    }

    /**
     * Handle accessibility events.
     */
    fun onAccessibilityEvent(event: AccessibilityEvent) {
        when (event.eventType) {
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED -> {
                handleNotificationEvent(event)
            }
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                handleWindowStateChange(event)
            }
            AccessibilityEvent.TYPE_ANNOUNCEMENT -> {
                handleAnnouncement(event)
            }
        }
    }

    private fun handleNotificationEvent(event: AccessibilityEvent) {
        // Extract notification content for HDC context
        val pkgName = event.packageName ?: return
        val notificationText = event.contentDescription?.toString() ?: ""

        // Encode as HDC context
        pythonBridge?.let { bridge ->
            // bridge.encodeNotification(pkgName, notificationText)
        }
    }

    private fun handleWindowStateChange(event: AccessibilityEvent) {
        // Detect app foreground/background transitions
        val isResumed = event.className?.contains("com.android.server.policy") != true
        if (isResumed) {
            // App came to foreground
            pythonBridge?.let { bridge ->
                // bridge.encodeAppForeground(event.packageName)
            }
        }
    }

    private fun handleAnnouncement(event: AccessibilityEvent) {
        // Screen reader announcements — may indicate UI context changes
        val text = event.contentDescription?.toString() ?: return
        pythonBridge?.let { bridge ->
            // bridge.encodeScreenReaderAnnouncement(text)
        }
    }

    /**
     * Monitor battery state for "battery_low" context.
     */
    fun registerBatteryReceiver() {
        val receiver = object : android.content.BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
                val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
                val batteryPct = if (scale > 0) (level / scale.toFloat() * 100) else 0f

                if (batteryPct <= 15f) {
                    // Battery low — trigger HDC context
                    pythonBridge?.let { bridge ->
                        // bridge.encodeBatteryLow()
                    }
                }
            }
        }

        context.registerReceiver(
            receiver,
            IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        )
    }

    /**
     * Enable accessibility service programmatically (requires user consent).
     */
    fun enableAccessibilityService() {
        val serviceComponent = ComponentName(context, AndroidAccessibilityBridge::class.java)
        val enabled = android.provider.Settings.Secure.getString(
            context.contentResolver,
            android.provider.Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        )

        if (enabled != serviceComponent.flattenToString()) {
            // Prompt user to enable (cannot do programmatically without consent)
            val intent = Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)
            context.startActivity(intent)
        }
    }
}
