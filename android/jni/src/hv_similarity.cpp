// Stage 21: HDC Hypervector Similarity
// Stub implementation - to be replaced with full similarity metrics

#include <jni.h>
#include <android/log.h>
#include <cstdint>

#define LOG_TAG "HDC_Similarity"

extern "C" {

// Compute cosine similarity between two hypervectors
JNIEXPORT jdouble JNICALL
Java_com_jarvis_ae01m_hdc_HdcCognitiveEngine_cosineSimilarity(
        JNIEnv* env, jobject thiz, jlongArray hv1, jlongArray hv2, jint dim) {
    // Stub: returns random similarity
    // TODO: implement proper cosine similarity
    jlong* a = env->GetLongArrayElements(hv1, nullptr);
    jlong* b = env->GetLongArrayElements(hv2, nullptr);
    
    double dot = 0.0, norm_a = 0.0, norm_b = 0.0;
    for (int i = 0; i < dim; i++) {
        dot += a[i] * b[i];
        norm_a += a[i] * a[i];
        norm_b += b[i] * b[i];
    }
    
    env->ReleaseLongArrayElements(hv1, a, 0);
    env->ReleaseLongArrayElements(hv2, b, 0);
    
    if (norm_a == 0.0 || norm_b == 0.0) return 0.0;
    return dot / (sqrt(norm_a) * sqrt(norm_b));
}

// Compute Hamming distance between two hypervectors
JNIEXPORT jint JNICALL
Java_com_jarvis_ae01m_hdc_HdcCognitiveEngine_hammingDistance(
        JNIEnv* env, jobject thiz, jlongArray hv1, jlongArray hv2, jint dim) {
    jlong* a = env->GetLongArrayElements(hv1, nullptr);
    jlong* b = env->GetLongArrayElements(hv2, nullptr);
    
    jint dist = 0;
    for (int i = 0; i < dim; i++) {
        if (a[i] != b[i]) dist++;
    }
    
    env->ReleaseLongArrayElements(hv1, a, 0);
    env->ReleaseLongArrayElements(hv2, b, 0);
    return dist;
}

}  // extern "C"
