# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.kts.

# Keep HDC cognitive engine model classes
-keep class com.jarvis.ae01m.hdc.** { *; }
-keep class com.jarvis.ae01m.bridge.** { *; }

# Keep JNI native methods
-keepclasseswithmembernames,includedescriptorclasses
-keep class * {
    native <methods>;
}

# Python bridge reflection
-keep class com.jarvis.ae01m.bridge.PythonBridge { *; }
