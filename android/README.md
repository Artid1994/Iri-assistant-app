# Stage 21 Android Integration Bridge
#
# Links the Stage 21 SNN+HDC runtime with Android Accessibility/Sensory inputs.
# Provides:
#   - JNI native library (libjari_bridge.so) for hypervector encoding/decoding
#   - Chaquopy Python 3 runtime for fallback processing
#   - Accessibility service bridge for system event capture
#   - Sensory input adapters (accelerometer, location, battery, app state)

## Architecture

```
Android App (Kotlin)
    ├── PythonBridge (JNI/C++)
    │   ├── libjari_bridge.so (native hypervector ops)
    │   └── Chaquopy Python runtime (fallback)
    ├── AndroidAccessibilityBridge (system events)
    └── MobileSensoryBridge (hardware sensors)
```

## Components

### JNI Native Library (libjari_bridge.so)
- Located: android/jni/
- Provides: encodeSpikes(), decodeHypervector(), cosineSimilarity()
- Build: CMake + NDK r27+

### Chaquopy Python Runtime
- Python 3.8+ bundled via Chaquopy plugin
- Scripts: mobile_sensory_bridge.py, hdc_memory_core.py
- Used when JNI unavailable or for Python-based HDC ops

### Accessibility Service
- Captures: app foreground/background, notification events, battery low
- Bridges to HDC context vectors via PythonBridge

### Sensory Input Adapters
- Accelerometer, gyroscope (movement context)
- Battery manager (battery_low events)
- Location (geofence context)
- App usage stats (foreground/background transitions)
