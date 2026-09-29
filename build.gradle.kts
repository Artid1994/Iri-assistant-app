// Top-level build file for JARVIS Mobile (AE01M Stage 21)
plugins {
    id("com.android.application") version "8.2.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
    id("com.google.protobuf") version "0.9.4" apply false
}

tasks.register("clean", JacocoReport::class) {
    // placeholder for clean
}
