// Stage 21: JNI Bridge Header
// HDC Hypervector Operations JNI Interface

#ifndef JARI_BRIDGE_H
#define JARI_BRIDGE_H

#include <jni.h>
#include <cstdint>

// HDC hypervector dimension
#define HV_DIM 10000

// Encode sensory input into hypervector
jlong* encode_hypervector(jfloat* input, jint dim);

// Decode hypervector to float representation
jfloat* decode_hypervector(jlong* hv, jint dim);

// Cosine similarity between two hypervectors
jdouble cosine_similarity(jlong* hv1, jlong* hv2, jint dim);

// Hamming distance between two hypervectors
jint hamming_distance(jlong* hv1, jlong* hv2, jint dim);

// XOR binding of two hypervectors
void xor_bind(jlong* a, jlong* b, jlong* result, jint dim);

// Bundling (majority vote) of multiple hypervectors
void bundle(jlong** hvs, jint count, jlong* result, jint dim);

#endif // JARI_BRIDGE_H
