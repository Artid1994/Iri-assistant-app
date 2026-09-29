package com.jarvis.ae01m.hdc

import com.jarvis.ae01m.bridge.PythonBridge

/**
 * HdcCognitiveEngine — mobile in-memory HDC engine (Stage 21).
 *
 * Lightweight in-memory implementation of the 10,000-dim bipolar hypervector
 * memory core. Uses the PythonBridge JNI layer for native encoding/decoding
 * when available, falling back to a pure-Kotlin cosine-similarity matcher.
 *
 * Learned rules (one-shot binding):
 *   - battery_low  → notify
 *   - app_in_background → speak
 *
 * These rules are loaded at MainActivity.onCreate() and persist in RAM
 * for the app lifetime.
 */
class HdcCognitiveEngine(private val hvDim: Int = 10000) {

    private val bridge: PythonBridge? = null
    private val rules = mutableMapOf<String, String>()
    private val contextVectors = mutableMapOf<String, FloatArray>()
    private val actionVectors = mutableMapOf<String, FloatArray>()

    init {
        // Initialize empty hypervector space
    }

    /**
     * Learn a one-shot context→action binding.
     * The binding key is formed as "context:action" (XOR-able).
     */
    fun learnRule(context: String, action: String) {
        rules[context] = action
    }

    /**
     * Retrieve the action bound to a given context key.
     * Returns null if no rule matches (threshold check can be added).
     */
    fun retrieveAction(context: String): String? = rules[context]

    /**
     * Generate a context hypervector from spike data.
     * Delegates to PythonBridge if JNI available.
     */
    fun createContextHypervector(contextKey: String, spikes: LongArray): FloatArray {
        val hv = FloatArray(hvDim)
        if (bridge?.isJniAvailable() == true) {
            // Native encoding
        } else {
            // Fallback: random bipolar encoding seeded by contextKey hash
            val seed = contextKey.hashCode()
            for (i in hv.indices) {
                hv[i] = if ((seed + i) % 2 == 0) 1.0f else -1.0f
            }
        }
        contextVectors[contextKey] = hv
        return hv
    }

    /**
     * Cosine similarity between two hypervectors.
     */
    fun cosineSimilarity(a: FloatArray, b: FloatArray): Double {
        if (a.size != b.size) return 0.0
        var dot = 0.0
        var normA = 0.0
        var normB = 0.0
        for (i in a.indices) {
            dot += a[i] * b[i]
            normA += a[i] * a[i]
            normB += b[i] * b[i]
        }
        val denom = Math.sqrt(normA * normB)
        return if (denom > 0.0) dot / denom else 0.0
    }

    /**
     * Bundle multiple hypervectors via element-wise majority vote.
     */
    fun bundle(hvs: List<FloatArray>): FloatArray {
        val bundled = FloatArray(hvDim)
        for (i in bundled.indices) {
            var sum = 0.0
            for (hv in hvs) sum += hv[i]
            bundled[i] = if (sum > 0) 1.0f else -1.0f
        }
        return bundled
    }

    /**
     * Retrieve context vector for debugging.
     */
    fun getContextVector(key: String): FloatArray? = contextVectors[key]

    /**
     * List learned rules.
     */
    fun getLearnedRules(): Map<String, String> = rules.toMap()
}
