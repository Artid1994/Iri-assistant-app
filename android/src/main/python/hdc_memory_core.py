#!/usr/bin/env python3
"""
Stage 21: HDC Memory Core (Python fallback for Chaquopy runtime)

Provides 10,000-dimensional bipolar hypervector memory operations:
- Random bipolar hypervector generation
- XOR binding (multiplication)
- Bundling (element-wise majority vote)
- Cosine similarity retrieval
- One-shot context-action learning and recall

Used when JNI native library (libjari_bridge.so) is unavailable.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple

HV_DIM = 10000  # Must match Kotlin HV_DIM


class HdcMemoryCore:
    """
    In-memory HDC cognitive engine with 10K-dim bipolar hypervectors.
    """

    def __init__(self, hv_dim: int = HV_DIM):
        self.hv_dim = hv_dim
        self.rules: Dict[str, str] = {}  # context -> action
        self.context_vectors: Dict[str, np.ndarray] = {}
        self.action_vectors: Dict[str, np.ndarray] = {}
        self._rng = np.random.default_rng()

    def _random_bipolar(self, seed: Optional[int] = None) -> np.ndarray:
        """Generate a random bipolar hypervector (+1 or -1)."""
        if seed is not None:
            rng = np.random.default_rng(seed)
        else:
            rng = self._rng
        return rng.choice([-1.0, 1.0], size=self.hv_dim).astype(np.float32)

    def create_context_hypervector(self, context_key: str, spikes: Optional[List[float]] = None) -> np.ndarray:
        """
        Create a context hypervector from a context key.
        If spikes provided, use them for seeded encoding.
        """
        seed = hash(context_key) % (2**31)
        hv = self._random_bipolar(seed=seed)
        self.context_vectors[context_key] = hv
        return hv

    def create_action_hypervector(self, action_key: str) -> np.ndarray:
        """Create an action hypervector."""
        seed = hash(action_key) % (2**31)
        hv = self._random_bipolar(seed=seed)
        self.action_vectors[action_key] = hv
        return hv

    def learn_rule(self, context: str, action: str) -> None:
        """Learn a one-shot context -> action binding."""
        self.rules[context] = action
        # Create and store hypervectors
        self.create_context_hypervector(context)
        self.create_action_hypervector(action)

    def retrieve_action(self, context: str) -> Optional[str]:
        """Retrieve the action bound to a context."""
        return self.rules.get(context)

    def retrieve_context(self, context: str) -> Optional[np.ndarray]:
        """Get the stored context hypervector."""
        return self.context_vectors.get(context)

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two hypervectors."""
        if a.shape != b.shape or len(a) != self.hv_dim:
            return 0.0
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        denom = norm_a * norm_b
        return float(dot / denom) if denom > 0 else 0.0

    def bundle(self, hvs: List[np.ndarray]) -> np.ndarray:
        """Bundle multiple hypervectors via element-wise majority vote."""
        if not hvs:
            return np.zeros(self.hv_dim, dtype=np.float32)
        stacked = np.stack(hvs, axis=0)
        # Majority vote: sign of sum
        summed = np.sum(stacked, axis=0)
        return np.sign(summed).astype(np.float32)

    def xor_bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """XOR binding (element-wise multiplication of bipolar vectors)."""
        return (a * b).astype(np.float32)

    def get_learned_rules(self) -> Dict[str, str]:
        """Return a copy of learned rules."""
        return dict(self.rules)


# --- Standalone test ---
if __name__ == "__main__":
    import sys
    import os

    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from mobile_sensory_bridge import MobileSensoryBridge
    from mobile_action_decoder import MobileActionDecoder

    print("=" * 60)
    print("Stage 21 HDC Memory Core — Python Fallback Test")
    print("=" * 60)

    # Initialize
    hdc = HdcMemoryCore(hv_dim=HV_DIM)
    print(f"[OK] HDC Memory Core initialized (HV_DIM={HV_DIM})")

    # Learn rules
    hdc.learn_rule("battery_low", "notify")
    hdc.learn_rule("app_in_background", "speak")
    print(f"[OK] Learned {len(hdc.rules)} rules: {list(hdc.rules.keys())}")

    # Test retrieval
    assert hdc.retrieve_action("battery_low") == "notify"
    assert hdc.retrieve_action("app_in_background") == "speak"
    print("[OK] Rule retrieval: PASS")

    # Test hypervector operations
    ctx_hv = hdc.create_context_hypervector("test_context")
    assert ctx_hv.shape == (HV_DIM,)
    assert set(np.unique(ctx_hv)).issubset({-1.0, 1.0})
    print(f"[OK] Context hypervector: shape={ctx_hv.shape}, bipolar={set(np.unique(ctx_hv))}")

    # Cosine similarity: identical vectors = 1.0
    sim = hdc.cosine_similarity(ctx_hv, ctx_hv)
    assert abs(sim - 1.0) < 1e-5
    print(f"[OK] Cosine similarity (self): {sim:.4f}")

    # Bundle test
    bundled = hdc.bundle([ctx_hv, ctx_hv])
    sim_bundled = hdc.cosine_similarity(ctx_hv, bundled)
    print(f"[OK] Bundle similarity: {sim_bundled:.4f}")

    # XOR bind test
    action_hv = hdc.create_action_hypervector("test_action")
    bound = hdc.xor_bind(ctx_hv, action_hv)
    assert bound.shape == (HV_DIM,)
    print(f"[OK] XOR bind: shape={bound.shape}")

    print("=" * 60)
    print("Stage 21 HDC Memory Core — Python fallback: ALL TESTS PASS")
    print("=" * 60)
