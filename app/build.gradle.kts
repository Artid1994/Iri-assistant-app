plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python") version "15.0.0"
}

android {
    namespace = "com.jarvis.ae01m"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.jarvis.ae01m"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0-stage21"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // JNI / Python bridge native library — isolate arm64-v8a for Android 15 16KB page alignment
        ndk {
            abiFilters += listOf("arm64-v8a")
        }

        // Stage 21 model assets
        assetPacks = listOf()
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("debug")
        }
        debug {
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        viewBinding = true
    }

    // Packaging: use legacy packaging for native library alignment (Android 15 16KB pages)
    packaging {
        jniLibs {
            useLegacyPackaging = true
        }
    }

    // Stage 21 brain model asset configuration
    aaptOptions {
        noCompress += listOf("bin", "onnx", "tflite", "zip")
    }

    // NDK external build configuration for JNI library
    externalNativeBuild {
        cmake {
            path = file("CMakeLists.txt")
            // Pass 16KB page size flags to CMake for Android 15 compatibility
            arguments += listOf(
                "-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON",
                "-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,max-page-size=16384",
                "-DCMAKE_SHARED_LINKER_FLAGS=-Wl,-z,common-page-size=16384"
            )
        }
    }

    // Chaquopy Python configuration
    sourceSets {
        getByName("main") {
            python {
                srcDirs += listOf("src/main/python")
            }
            assets.srcDirs += listOf("src/main/assets")
        }
    }
}

chaquopy {
    // Python version for Chaquopy
    pythonVersion = "3.8"
    // Enable numpy for HDC hypervector math
    pip {
        install("numpy")
        install("scipy")
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-ktx:1.8.2")
    implementation("org.jetbrains.kotlin:kotlin-stdlib:1.9.22")

    // JNI native bridge to Stage 21 model
    implementation("net.zetetic:android-database-sqlcipher:4.5.4")
    implementation("jnr:jnr-ffi:3.1.6")

    // HDC hypervector math helpers
    implementation("org.nd4j:nd4j-native-platform:1.0.0-M2.1")

    // Kotlin Coroutines for async initialization
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")

    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
