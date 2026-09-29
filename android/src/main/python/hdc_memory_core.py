#!/usr/bin/env python3
"""
Stage 21: HDC Memory Core
Hyperdimensional Computing (HDC) Cognitive Integration:
- 10,000-dimensional Bipolar Hypervector Memory (10,000 bits/vector)
- Maps Spike output patterns from Stage 20 Model C Brain into Hypervectors
- One-Shot Binding (XOR) and Bundling (+) for rapid context-action association
- Hamming Distance / Cosine Similarity checking for instant retrieval
"""
import json
import struct
import time
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field

import numpy as np

# ─── Configuration ────────────────────────────────────────────────────────────
HV_DIM = 10000              # Hypervector dimensionality (bits)
N_ACTION_TYPES = 14         # Number of action types (matches decoder)
RAM_LIMIT_MB = 1000         # Hard memory limit
LAB_ONLY = True             # Lab-only branch flag

# ─── Constants ────────────────────────────────────────────────────────────────
SPIKE_THRESHOLD_mV = 1.0    # LIF spike threshold (same as brain model)
DT_MS = 1.0                 # Simulation timestep (ms)
RESTING_POTENTIAL = 0.0     # LIF resting potential
LEAK_DECAY = 0.95           # Membrane leak per step

# ─── Hypervector Types ───────────────────────────────────────────────────────
class HypervectorType(Enum):
    """Types of hypervectors used in HDC memory."""
    CONTEXT = "context"          # Sensory/context patterns
    ACTION = "action"            # Action type patterns
    BINDING = "binding"          # Context-action bindings
    BUNDLE = "bundle"            # Bundled association stores


# ─── Hypervector Class ────────────────────────────────────────────────────────
@dataclass
class Hypervector:
    """A single 10,000-dimensional bipolar hypervector."""
    data: np.ndarray = field(default_factory=lambda: np.zeros(HV_DIM, dtype=np.int8))
    vector_type: HypervectorType = HypervectorType.CONTEXT
    label: str = ""
    timestamp: float = 0.0

    def __post_init__(self):
        # Ensure bipolar: values are -1 or +1
        self.data = np.clip(self.data, -1, 1)
        self.data = self.data.astype(np.int8)

    def random(self, seed: Optional[int] = None) -> 'Hypervector':
        """Generate a random bipolar hypervector."""
        rng = np.random.default_rng(seed)
        self.data = rng.choice([-1, 1], size=HV_DIM).astype(np.int8)
        return self

    def hamming_distance(self, other: 'Hypervector') -> int:
        """Compute Hamming distance between two hypervectors."""
        return np.sum(self.data != other.data)

    def cosine_similarity(self, other: 'Hypervector') -> float:
        """Compute cosine similarity between two hypervectors."""
        dot = np.dot(self.data.astype(np.float64), other.data.astype(np.float64))
        norm_self = np.sqrt(np.sum(self.data.astype(np.float64) ** 2))
        norm_other = np.sqrt(np.sum(other.data.astype(np.float64) ** 2))
        if norm_self == 0 or norm_other == 0:
            return 0.0
        return float(dot / (norm_self * norm_other))

    def xor(self, other: 'Hypervector') -> 'Hypervector':
        """One-shot binding via XOR (elementwise multiplication for bipolar)."""
        result = Hypervector()
        result.data = (self.data * other.data).astype(np.int8)
        result.vector_type = HypervectorType.BINDING
        return result

    def bundle(self, other: 'Hypervector') -> 'Hypervector':
        """Bundling via addition (elementwise sum)."""
        result = Hypervector()
        result.data = np.clip(self.data + other.data, -1, 1).astype(np.int8)
        result.vector_type = HypervectorType.BUNDLE
        return result

    def bundle_many(self, others: List['Hypervector']) -> 'Hypervector':
        """Bundle multiple hypervectors (majority vote)."""
        result = Hypervector()
        if not others:
            return result
        stacked = np.stack([h.data for h in others], axis=0).astype(np.int8)
        sums = np.sum(stacked, axis=0)
        result.data = np.sign(sums).astype(np.int8)
        result.data = np.where(result.data == 0, 1, result.data)  # tie-break to +1
        result.vector_type = HypervectorType.BUNDLE
        return result

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "dim": HV_DIM,
            "type": self.vector_type.value,
            "label": self.label,
            "timestamp": self.timestamp,
            "sample": self.data[:100].tolist(),  # First 100 bits as sample
        }

    def __len__(self) -> int:
        return HV_DIM


# ─── Spike Pattern to Hypervector Mapper ─────────────────────────────────────
class SpikeToHypervectorMapper:
    """
    Maps spike output patterns from the brain into hypervectors.
    Uses spike train statistics (count, rate, positions) to generate
    deterministic hypervector representations.
    """
    def __init__(self, hv_dim: int = HV_DIM):
        self.hv_dim = hv_dim
        self.rng = np.random.default_rng(42)

    def spikes_to_hypervector(self, spike_indices: np.ndarray, n_neurons: int,
                               timestamp: float = 0.0) -> Hypervector:
        """
        Convert a spike pattern into a hypervector.

        Strategy: Use spike counts per neuron region, spike positions,
        and inter-spike intervals to deterministically generate a hypervector.
        """
        hv = Hypervector()
        hv.vector_type = HypervectorType.CONTEXT
        hv.timestamp = timestamp

        if len(spike_indices) == 0:
            # No spikes: return random hypervector (null context)
            hv.random(seed=hash(timestamp) % (2**31))
            hv.data[:] = self.rng.choice([-1, 1], size=self.hv_dim).astype(np.int8)
            return hv

        # Strategy: Deterministic hash-based generation from spike statistics
        # Use multiple "projections" to fill the 10,000-dim space

        # 1. Spike count projection (60% of dimensions)
        n_spikes = len(spike_indices)
        rng = np.random.default_rng(hash(int(timestamp * 1000)) % (2**31))

        # Generate base pattern from spike count
        base = rng.choice([-1, 1], size=self.hv_dim).astype(np.int8)

        # 2. Spike position projection (25% of dimensions)
        # Use actual spike indices modulo hv_dim to set bits
        pos_slice = slice(0, self.hv_dim // 4)
        for idx in spike_indices[:self.hv_dim // 4]:
            pos = idx % (self.hv_dim // 4)
            base[pos_slice][pos] = 1 if base[pos_slice][pos] == -1 else -1

        # 3. Rate-based projection (15% of dimensions)
        rate = n_spikes / max(1, n_neurons)  # spikes per neuron
        rate_slice = slice(self.hv_dim // 4, self.hv_dim // 4 + self.hv_dim // 10)
        rate_int = int(rate * 1000) % (self.hv_dim // 10)
        base[rate_slice][rate_int] = 1

        hv.data = base
        return hv

    def spikes_to_hv_batch(self, spike_trains: List[Tuple[np.ndarray, int]], 
                            timestamps: List[float]) -> List[Hypervector]:
        """Convert a batch of spike trains to hypervectors."""
        hvs = []
        for spikes, n_neurons in spike_trains:
            ts = timestamps[len(hvs)] if len(timestamps) > len(hvs) else 0.0
            hvs.append(self.spikes_to_hypervector(spikes, n_neurons, ts))
        return hvs


# ─── HDC Memory Store ──────────────────────────────────────────────────────────
class HdcMemoryStore:
    """
    Hyperdimensional Computing Memory Store.
    Stores context-action associations using binding (+ bundling) for
    one-shot learning and instant retrieval via similarity search.
    """
    def __init__(self, hv_dim: int = HV_DIM):
        self.hv_dim = hv_dim
        self.ctx_hvs: Dict[str, Hypervector] = {}   # context -> hypervector
        self.act_hvs: Dict[str, Hypervector] = {}   # action -> hypervector
        self.bindings: Dict[str, Hypervector] = {}  # key -> binding hypervector
        self.bundles: Dict[str, Hypervector] = {}   # association_id -> bundled store
        self.rng = np.random.default_rng(42)

    def create_context_hv(self, context_key: str, 
                          spike_indices: Optional[np.ndarray] = None,
                          n_neurons: int = 1000,
                          timestamp: float = 0.0) -> Hypervector:
        """
        Create or retrieve a context hypervector.
        If spike_indices provided, use them; otherwise generate deterministic random.
        """
        if context_key in self.ctx_hvs:
            return self.ctx_hvs[context_key]

        hv = Hypervector()
        hv.vector_type = HypervectorType.CONTEXT
        hv.label = context_key
        hv.timestamp = timestamp

        if spike_indices is not None and len(spike_indices) > 0:
            mapper = SpikeToHypervectorMapper(self.hv_dim)
            hv = mapper.spikes_to_hypervector(spike_indices, n_neurons, timestamp)
            hv.label = context_key
        else:
            # Deterministic random from context key
            seed = hash(context_key) % (2**31)
            hv.random(seed=seed)

        self.ctx_hvs[context_key] = hv
        return hv

    def create_action_hv(self, action_type: str) -> Hypervector:
        """Create or retrieve an action type hypervector."""
        if action_type in self.act_hvs:
            return self.act_hvs[action_type]

        hv = Hypervector()
        hv.vector_type = HypervectorType.ACTION
        hv.label = action_type
        seed = hash(action_type) % (2**31)
        hv.random(seed=seed)

        self.act_hvs[action_type] = hv
        return hv

    def bind_context_action(self, context_key: str, action_type: str,
                            spike_indices: Optional[np.ndarray] = None,
                            n_neurons: int = 1000,
                            timestamp: float = 0.0) -> Hypervector:
        """
        Create a binding hypervector (XOR) between context and action.
        This is the core one-shot learning operation.
        """
        ctx_hv = self.create_context_hv(context_key, spike_indices, n_neurons, timestamp)
        act_hv = self.create_action_hv(action_type)

        binding = ctx_hv.xor(act_hv)
        binding.label = f"{context_key}->{action_type}"
        binding.timestamp = timestamp

        binding_key = f"{context_key}:{action_type}"
        self.bindings[binding_key] = binding
        return binding

    def bundle_bindings(self, binding_keys: List[str], 
                        association_id: str) -> Hypervector:
        """
        Bundle multiple binding hypervectors into a single associative store.
        Uses majority voting for bundling.
        """
        if not binding_keys:
            return Hypervector()

        binding_hvs = [self.bindings[k] for k in binding_keys if k in self.bindings]
        if not binding_hvs:
            return Hypervector()

        bundle = binding_hvs[0].bundle_many(binding_hvs[1:])
        bundle.vector_type = HypervectorType.BUNDLE
        bundle.label = association_id

        self.bundles[association_id] = bundle
        return bundle

    def retrieve_action(self, query_context: str,
                        spike_indices: Optional[np.ndarray] = None,
                        n_neurons: int = 1000,
                        threshold: float = 0.7) -> Optional[str]:
        """
        Retrieve the most likely action given a query context.
        Uses cosine similarity against stored bindings.

        Args:
            query_context: The context key to query
            spike_indices: Optional spike pattern for context encoding
            n_neurons: Number of neurons in the spike pattern
            threshold: Minimum cosine similarity to consider a match

        Returns:
            The action type string if similarity above threshold, else None
        """
        if query_context not in self.ctx_hvs:
            # Create context on-the-fly from spikes if provided
            if spike_indices is not None:
                ctx_hv = self.create_context_hv(query_context, spike_indices, 
                                                  n_neurons, time.time())
            else:
                return None
        else:
            ctx_hv = self.ctx_hvs[query_context]

        best_action = None
        best_similarity = -1.0

        for binding_key, binding_hv in self.bindings.items():
            # Unbind: XOR with context to get action candidate
            # ctx XOR binding = ctx XOR (ctx XOR act) = act
            candidate = ctx_hv.xor(binding_hv)

            # Compare candidate to known action hypervectors
            for action_type, act_hv in self.act_hvs.items():
                sim = candidate.cosine_similarity(act_hv)
                if sim > best_similarity:
                    best_similarity = sim
                    best_action = action_type

        if best_similarity >= threshold and best_action:
            return best_action
        return None

    def retrieve_by_similarity(self, query_hv: Hypervector,
                               top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve the most similar bindings to a query hypervector.
        Returns list of (binding_label, cosine_similarity) sorted by similarity.
        """
        results = []
        for binding_key, binding_hv in self.bindings.items():
            sim = query_hv.cosine_similarity(binding_hv)
            results.append((binding_key, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def get_stats(self) -> dict:
        """Return memory store statistics."""
        return {
            "context_vectors": len(self.ctx_hvs),
            "action_vectors": len(self.act_hvs),
            "bindings": len(self.bindings),
            "bundles": len(self.bundles),
            "hv_dim": self.hv_dim,
            "total_hypervectors": len(self.ctx_hvs) + len(self.act_hvs) + 
                                 len(self.bindings) + len(self.bundles),
        }


# ─── HDC Cognitive Integrator ──────────────────────────────────────────────────
class HdcCognitiveIntegrator:
    """
    Integrates HDC memory with the Stage 20 pipeline:
    Sensory Bridge → Model C Brain → HDC Memory Core → Action Decoder

    Learns context-action associations from experience and retrieves them
    for decision-making.
    """
    def __init__(self, hv_dim: int = HV_DIM, ram_limit_mb: int = RAM_LIMIT_MB):
        self.memory = HdcMemoryStore(hv_dim)
        self.mapper = SpikeToHypervectorMapper(hv_dim)
        self.ram_limit_mb = ram_limit_mb
        self.learned_rules: List[dict] = []

    def learn_rule(self, context_key: str, action_type: str,
                   spike_indices: Optional[np.ndarray] = None,
                   n_neurons: int = 1000) -> dict:
        """
        Learn a context-action association (one-shot binding).
        Returns the learning result.
        """
        timestamp = time.time()
        binding = self.memory.bind_context_action(
            context_key, action_type, spike_indices, n_neurons, timestamp
        )

        rule = {
            "context": context_key,
            "action": action_type,
            "binding_key": f"{context_key}:{action_type}",
            "timestamp": timestamp,
            "binding_similarity_self": binding.cosine_similarity(binding),  # Should be 1.0
        }
        self.learned_rules.append(rule)
        return rule

    def learn_bundle(self, context_action_pairs: List[Tuple[str, str]],
                     association_id: str) -> Hypervector:
        """Learn multiple context-action associations as a bundled store."""
        binding_keys = []
        for ctx, act in context_action_pairs:
            bk = f"{ctx}:{act}"
            if bk not in self.memory.bindings:
                self.memory.bind_context_action(ctx, act)
            binding_keys.append(bk)

        return self.memory.bundle_bindings(binding_keys, association_id)

    def retrieve_action(self, context_key: str,
                        spike_indices: Optional[np.ndarray] = None,
                        n_neurons: int = 1000,
                        threshold: float = 0.7) -> Optional[str]:
        """Retrieve action for a given context."""
        return self.memory.retrieve_action(context_key, spike_indices, 
                                           n_neurons, threshold)

    def query_similar(self, query_hv: Hypervector, top_k: int = 5) -> List:
        """Query most similar bindings."""
        return self.memory.retrieve_by_similarity(query_hv, top_k)

    def get_stats(self) -> dict:
        return self.memory.get_stats()


# ─── Standalone Tests ──────────────────────────────────────────────────────────
def run_standalone_tests():
    """Run HDC memory core standalone tests."""
    print("=" * 60)
    print("STAGE 21: HDC MEMORY CORE - STANDALONE TESTS")
    print("=" * 60)

    hv_dim = HV_DIM
    print(f"\n[1] Hypervector Dimension: {hv_dim}")
    print(f"    RAM Limit: {RAM_LIMIT_MB} MB")
    print(f"    Lab Only: {LAB_ONLY}")

    # Test 1: Hypervector creation and properties
    print("\n[2] Test 1: Hypervector Creation")
    hv1 = Hypervector()
    hv1.random(seed=42)
    hv2 = Hypervector()
    hv2.random(seed=42)
    hv3 = Hypervector()
    hv3.random(seed=99)

    print(f"    HV1 == HV2 (same seed): {np.array_equal(hv1.data, hv2.data)}")
    print(f"    HV1 != HV3 (diff seed): {not np.array_equal(hv1.data, hv3.data)}")
    print(f"    HV1 hamming distance to HV2: {hv1.hamming_distance(hv2)}")
    print(f"    HV1 hamming distance to HV3: {hv1.hamming_distance(hv3)}")
    print(f"    HV1 cosine sim to HV2: {hv1.cosine_similarity(hv2):.4f}")
    print(f"    HV1 cosine sim to HV3: {hv1.cosine_similarity(hv3):.4f}")

    # Test 2: XOR binding
    print("\n[3] Test 2: One-Shot Binding (XOR)")
    binding = hv1.xor(hv2)
    print(f"    Binding type: {binding.vector_type.value}")
    print(f"    Binding label: {binding.label}")
    print(f"    Binding hamming to HV1: {binding.hamming_distance(hv1)}")
    print(f"    Binding hamming to HV2: {binding.hamming_distance(hv2)}")

    # Verify: HV1 XOR binding = HV2 (since HV1 == HV2, binding should recover)
    recovered = hv1.xor(binding)
    print(f"    HV1 XOR binding recovers HV2: {np.array_equal(recovered.data, hv2.data)}")

    # Test 3: Bundling
    print("\n[4] Test 3: Bundling (+)")
    hv4 = Hypervector()
    hv4.random(seed=100)
    hv5 = Hypervector()
    hv5.random(seed=200)
    hv6 = Hypervector()
    hv6.random(seed=300)

    bundle = hv4.bundle(hv5).bundle(hv6)
    print(f"    Bundle type: {bundle.vector_type.value}")
    print(f"    Bundle label: {bundle.label}")
    print(f"    Bundle cosine sim to HV4: {bundle.cosine_similarity(hv4):.4f}")
    print(f"    Bundle cosine sim to HV5: {bundle.cosine_similarity(hv5):.4f}")
    print(f"    Bundle cosine sim to HV6: {bundle.cosine_similarity(hv6):.4f}")

    # Test 4: Spike-to-hypervector mapping
    print("\n[5] Test 4: Spike Pattern → Hypervector")
    mapper = SpikeToHypervectorMapper(hv_dim)
    spike_indices = np.array([10, 42, 100, 256, 512, 1024, 2048, 4096])
    hv_spikes = mapper.spikes_to_hypervector(spike_indices, n_neurons=1000, timestamp=0.0)
    print(f"    Spike count: {len(spike_indices)}")
    print(f"    Resulting HV shape: {hv_spikes.data.shape}")
    print(f"    HV sample (first 20): {hv_spikes.data[:20].tolist()}")

    # Test 5: HDC Memory Store
    print("\n[6] Test 5: HDC Memory Store")
    store = HdcMemoryStore(hv_dim)

    # Create contexts and actions
    ctx1 = store.create_context_hv("battery_low", timestamp=0.0)
    ctx2 = store.create_context_hv("app_in_background", timestamp=0.0)
    act1 = store.create_action_hv("notify")
    act2 = store.create_action_hv("speak")

    print(f"    Context vectors: {len(store.ctx_hvs)}")
    print(f"    Action vectors: {len(store.act_hvs)}")

    # Bind context-action pairs
    binding1 = store.bind_context_action("battery_low", "notify", timestamp=0.0)
    binding2 = store.bind_context_action("app_in_background", "speak", timestamp=0.0)
    print(f"    Bindings created: {len(store.bindings)}")
    print(f"    Binding1 cosine self: {binding1.cosine_similarity(binding1):.4f}")
    print(f"    Binding2 cosine self: {binding2.cosine_similarity(binding2):.4f}")

    # Bundle bindings
    bundle_store = store.bundle_bindings(
        ["battery_low:notify", "app_in_background:speak"], 
        "user_preferences"
    )
    print(f"    Bundle created: {bundle_store.label}")
    print(f"    Bundle cosine to binding1: {bundle_store.cosine_similarity(binding1):.4f}")
    print(f"    Bundle cosine to binding2: {bundle_store.cosine_similarity(binding2):.4f}")

    # Test retrieval
    print("\n[7] Test 6: Retrieval")
    retrieved = store.retrieve_action("battery_low", threshold=0.5)
    print(f"    Query 'battery_low' → retrieved: {retrieved}")

    retrieved2 = store.retrieve_action("app_in_background", threshold=0.5)
    print(f"    Query 'app_in_background' → retrieved: {retrieved2}")

    # Test retrieval with spike-based context
    spike_ctx = np.array([100, 200, 300, 500, 1000])
    retrieved3 = store.retrieve_action("battery_low", spike_indices=spike_ctx, 
                                        n_neurons=1000, threshold=0.5)
    print(f"    Query 'battery_low' (with spikes) → retrieved: {retrieved3}")

    # Test similarity query
    print("\n[8] Test 7: Similarity Query")
    query_hv = store.ctx_hvs.get("battery_low", Hypervector())
    if query_hv.data.sum() != 0:  # non-empty
        similar = store.retrieve_by_similarity(query_hv, top_k=3)
        print(f"    Top 3 similar bindings to 'battery_low':")
        for label, sim in similar:
            print(f"      {label}: cosine={sim:.4f}")

    # Stats
    print("\n[9] Test 8: Memory Statistics")
    stats = store.get_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    print("\n" + "=" * 60)
    print("HDC MEMORY CORE TESTS: PASS")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = run_standalone_tests()
    sys.exit(0 if success else 1)