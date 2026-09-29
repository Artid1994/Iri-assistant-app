package com.jarvis.ae01m.bridge

import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationManager
import android.os.BatteryManager
import android.content.Intent
import android.content.IntentFilter

/**
 * SensoryInputAdapter — hardware sensor bridge for HDC context.
 *
 * Captures:
 *   - Accelerometer (movement/gesture context)
 *   - Gyroscope (orientation context)
 *   - Location (geofence/region context)
 *   - Battery state (battery_low events)
 *
 * Bridges sensor data to HDC context vectors via PythonBridge.
 */
class SensoryInputAdapter(
    private val context: Context
) {

    companion object {
        private const val ACCELERATION_THRESHOLD = 1.5f  // g-force threshold for movement
        private const val LOCATION_UPDATE_MIN_TIME = 60000L  // 1 minute
        private const val LOCATION_UPDATE_MIN_DISTANCE = 10f  // 10 meters
    }

    private val sensorManager: SensorManager =
        context.getSystemService(Context.SENSOR_SERVICE) as SensorManager

    private val locationManager: LocationManager =
        context.getSystemService(Context.LOCATION_SERVICE) as LocationManager

    private var pythonBridge: PythonBridge? = null

    private val batteryReceiver = object : android.content.BroadcastReceiver() {
        override fun onReceive(ctx: Context, intent: Intent) {
            val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            val scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
            val batteryPct = if (scale > 0) (level / scale.toFloat() * 100) else 0f

            if (batteryPct <= 15f) {
                // Battery low — trigger HDC context
                pythonBridge?.encodeBatteryLow()
            }
        }
    }

    /**
     * Connect to PythonBridge for HDC event encoding.
     */
    fun setPythonBridge(bridge: PythonBridge) {
        this.pythonBridge = bridge
    }

    /**
     * Start accelerometer monitoring.
     */
    fun startAccelerometerMonitoring() {
        val accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        accelerometer?.let { sensor ->
            sensorManager.registerListener(
                accelerometerListener,
                sensor,
                SensorManager.SENSOR_DELAY_NORMAL
            )
        }
    }

    /**
     * Start gyroscope monitoring.
     */
    fun startGyroscopeMonitoring() {
        val gyroscope = sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)
        gyroscope?.let { sensor ->
            sensorManager.registerListener(
                gyroscopeListener,
                sensor,
                SensorManager.SENSOR_DELAY_NORMAL
            )
        }
    }

    /**
     * Start location monitoring (requires ACCESS_FINE_LOCATION or ACCESS_COARSE_LOCATION).
     */
    fun startLocationMonitoring() {
        if (locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER) ||
            locationManager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {

            val locationListener = object : android.location.LocationListener {
                override fun onLocationChanged(location: Location) {
                    pythonBridge?.encodeLocation(location.latitude, location.longitude)
                }

                override fun onStatusChanged(provider: String?, status: Int, extras: android.os.Bundle?) {}
                override fun onProviderEnabled(provider: String) {}
                override fun onProviderDisabled(provider: String) {}
            }

            try {
                locationManager.requestLocationUpdates(
                    LocationManager.GPS_PROVIDER,
                    LOCATION_UPDATE_MIN_TIME,
                    LOCATION_UPDATE_MIN_DISTANCE,
                    locationListener
                )
            } catch (e: SecurityException) {
                // Location permission not granted
            }
        }
    }

    /**
     * Register battery state receiver.
     */
    fun registerBatteryReceiver() {
        context.registerReceiver(
            batteryReceiver,
            IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        )
    }

    /**
     * Unregister battery receiver.
     */
    fun unregisterBatteryReceiver() {
        try {
            context.unregisterReceiver(batteryReceiver)
        } catch (e: Exception) {
            // Already unregistered
        }
    }

    /**
     * Clean up sensor listeners.
     */
    fun cleanup() {
        sensorManager.unregisterListener(accelerometerListener)
        sensorManager.unregisterListener(gyroscopeListener)
        unregisterBatteryReceiver()
    }

    // --- Sensor listeners ---

    private val accelerometerListener = object : SensorEventListener {
        override fun onSensorChanged(event: SensorEvent) {
            if (event.sensor.type == Sensor.TYPE_ACCELEROMETER) {
                val x = event.values[0]
                val y = event.values[1]
                val z = event.values[2]
                val magnitude = Math.sqrt(x*x + y*y + z*z).toFloat()

                // Detect significant movement
                if (magnitude > ACCELERATION_THRESHOLD) {
                    pythonBridge?.encodeMovementEvent(magnitude)
                }
            }
        }

        override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    }

    private val gyroscopeListener = object : SensorEventListener {
        override fun onSensorChanged(event: SensorEvent) {
            if (event.sensor.type == Sensor.TYPE_GYROSCOPE) {
                val rotation = Math.sqrt(
                    event.values[0].pow(2) +
                    event.values[1].pow(2) +
                    event.values[2].pow(2)
                ).toFloat()

                // Detect significant rotation
                if (rotation > 1.0f) {
                    pythonBridge?.encodeRotationEvent(rotation)
                }
            }
        }

        override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
    }
}
