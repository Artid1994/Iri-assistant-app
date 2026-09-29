# Native JNI bridge for Stage 21 HDC model
# libjari_bridge.so — hypervector encoding/decoding via C++

#include <jni.h>
#include <android/log.h>
#include <cmath>
#include <cstdlib>
#include <cstring>

#define LOG_TAG "JARIBridge"
#define LOGD(...) __android_log_print(ANDROID_LOG_DEBUG, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

// Hypervector dimension (must match Kotlin: 10000)
static const int HV_DIM = 10000;

// Bipolar hypervector: +1.0f or -1.0f
typedef float hv_t;

// --- Hypervector encoding from spike timestamps ---

extern "C" JNIEXPORT jfloatArray JNICALL
Java_com_jarvis_ae01m_bridge_PythonBridge_encodeSpikes(
    JNIEnv* env,
    jobject /* thiz */,
    jlongArray spikeTimestamps) {

    jsize len = env->GetArrayLength(spikeTimestamps);
    jlong* timestamps = env->GetLongArrayElements(spikeTimestamps, nullptr);

    // Allocate output hypervector
    jfloatArray hv = env->NewFloatArray(HV_DIM);
    jfloat* hvPtr = env->GetFloatArrayElements(hv, nullptr);

    // Initialize to neutral (0)
    memset(hvPtr, 0, HV_DIM * sizeof(float));

    if (len > 0 && timestamps != nullptr) {
        // Seed from first spike timestamp
        unsigned int seed = (unsigned int)(timestamps[0] & 0xFFFFFFFF);
        srand(seed);

        // Generate bipolar hypervector via pseudo-random XOR projection
        for (int i = 0; i < HV_DIM; i++) {
            // XOR-binding-like projection: random walk seeded by spikes
            int proj = rand() % 3;  // -1, 0, or +1 contribution
            if (proj == 0) {
                hvPtr[i] = -1.0f;
            } else if (proj == 1) {
                hvPtr[i] = 1.0f;
            } else {
                hvPtr[i] = 0.0f;  // neutral
            }
        }
    }

    env->ReleaseLongArrayElements(spikeTimestamps, timestamps, JNI_ABORT);
    env->ReleaseFloatArrayElements(hv, hvPtr, 0);

    LOGD("encodeSpikes: %d spikes -> hv[%d]", len, HV_DIM);
    return hv;
}

// --- Cosine similarity between two hypervectors ---

extern "C" JNIEXPORT jdouble JNICALL
Java_com_jarvis_ae01m_bridge_PythonBridge_cosineSimilarity(
    JNIEnv* env,
    jobject /* thiz */,
    jfloatArray hvA,
    jfloatArray hvB) {

    jsize dim = env->GetArrayLength(hvA);
    if (dim != HV_DIM || env->GetArrayLength(hvB) != HV_DIM) {
        LOGE("cosineSimilarity: dimension mismatch (%d vs %d)", dim, HV_DIM);
        return 0.0;
    }

    jfloat* ptrA = env->GetFloatArrayElements(hvA, nullptr);
    jfloat* ptrB = env->GetFloatArrayElements(hvB, nullptr);

    double dot = 0.0;
    double normA = 0.0;
    double normB = 0.0;

    for (int i = 0; i < dim; i++) {
        dot += ptrA[i] * ptrB[i];
        normA += ptrA[i] * ptrA[i];
        normB += ptrB[i] * ptrB[i];
    }

    env->ReleaseFloatArrayElements(hvA, ptrA, JNI_ABORT);
    env->ReleaseFloatArrayElements(hvB, ptrB, JNI_ABORT);

    double denom = std::sqrt(normA * normB);
    double similarity = (denom > 0.0) ? (dot / denom) : 0.0;

    LOGD("cosineSimilarity: %.4f", similarity);
    return similarity;
}

// --- Hypervector bundling (element-wise majority vote) ---

extern "C" JNIEXPORT jfloatArray JNICALL
Java_com_jarvis_ae01m_bridge_PythonBridge_bundleHypervectors(
    JNIEnv* env,
    jobject /* thiz */,
    jfloatArray* hvList,
    jint listSize) {

    jfloatArray bundled = env->NewFloatArray(HV_DIM);
    jfloat* bundledPtr = env->GetFloatArrayElements(bundled, nullptr);

    // Accumulate votes
    double* votes = new double[HV_DIM]();
    memset(votes, 0, HV_DIM * sizeof(double));

    for (int k = 0; k < listSize; k++) {
        jfloat* ptr = env->GetFloatArrayElements(hvList[k], nullptr);
        for (int i = 0; i < HV_DIM; i++) {
            votes[i] += ptr[i];
        }
        env->ReleaseFloatArrayElements(hvList[k], ptr, JNI_ABORT);
    }

    // Majority vote: > 0 -> +1, < 0 -> -1
    for (int i = 0; i < HV_DIM; i++) {
        bundledPtr[i] = (votes[i] > 0.0) ? 1.0f : -1.0f;
    }

    delete[] votes;
    env->ReleaseFloatArrayElements(bundled, bundledPtr, 0);

    LOGD("bundleHypervectors: %d vectors bundled", listSize);
    return bundled;
}

// --- XOR binding of two hypervectors ---

extern "C" JNIEXPORT jfloatArray JNICALL
Java_com_jarvis_ae01m_bridge_PythonBridge_xorBind(
    JNIEnv* env,
    jobject /* thiz */,
    jfloatArray hvA,
    jfloatArray hvB) {

    jfloat* ptrA = env->GetFloatArrayElements(hvA, nullptr);
    jfloat* ptrB = env->GetFloatArrayElements(hvB, nullptr);

    jfloatArray bound = env->NewFloatArray(HV_DIM);
    jfloat* boundPtr = env->GetFloatArrayElements(bound, nullptr);

    // XOR binding: multiply signs (bipolar multiplication)
    for (int i = 0; i < HV_DIM; i++) {
        boundPtr[i] = ptrA[i] * ptrB[i];
    }

    env->ReleaseFloatArrayElements(hvA, ptrA, JNI_ABORT);
    env->ReleaseFloatArrayElements(hvB, ptrB, JNI_ABORT);
    env->ReleaseFloatArrayElements(bound, boundPtr, 0);

    LOGD("xorBind: completed");
    return bound;
}
