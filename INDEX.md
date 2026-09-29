# Stage 21: HDC Cognitive Integration — Index

## Overview
Stage 21 implements Hyperdimensional Computing (HDC) cognitive integration, connecting the Stage 20 mobile pipeline (Sensory Bridge → Model C SNN → Action Decoder) with a 10,000-dimensional Bipolar Hypervector Memory for one-shot context-action association learning and retrieval.

## Directory Structure
```
scaffold/stage21/
├── model/                    # Trained brain model checkpoint
│   └── iri_brain_v6_1m_trained_phase1_phase2.bin  (308 MB)
├── scripts/                  # Core pipeline scripts
│   ├── mobile_sensory_bridge.py         # Stage 20: Mobile sensory input
│   ├── mobile_action_decoder.py         # Stage 20: Motor action decoding
│   ├── hdc_memory_core.py              # Stage 21: HDC memory core (10K-dim)
│   └── test_stage21_hdc_pipeline.py    # Integration test harness
├── results/                  # Benchmark results
│   └── locked_stage21_hdc_benchmark.json  # Locked baseline metrics
├── INDEX.md                  # This file
└── MANIFEST.json             # Machine-readable file registry
```

## Components

### Model
- **iri_brain_v6_1m_trained_phase1_phase2.bin** — Trained brain model (307.99 MB)
  - Source: Stage 19 trained checkpoint
  - Copy in stage21/model/ for consolidation

### Scripts
| File | Description | Size |
|------|-------------|------|
| mobile_sensory_bridge.py | Stage 20 MobileSensoryBridge — 20K sensory neurons, event injection | 9,621 bytes |
| mobile_action_decoder.py | Stage 20 MobileActionDecoder — 80K motor neurons, 14 action types | 11,469 bytes |
| hdc_memory_core.py | Stage 21 HDC Memory Core — 10K-dim bipolar hypervectors, XOR binding, bundling, cosine similarity retrieval | 23,101 bytes |
| test_stage21_hdc_pipeline.py | Integration test: 10s simulation, RAM gate, recall accuracy | 13,102 bytes |

### Benchmark Results
- **locked_stage21_hdc_benchmark.json** — Locked baseline metrics
  - Peak RSS: 38.06 MB (limit 1000 MB)
  - Firing rate: 0.0043 Hz
  - Total spikes: 217,082
  - Recall accuracy: PASS (battery_low→notify, app_in_background→speak)

## Pipeline Flow
```
MobileSensoryBridge (Stage 20)
    → ThetaGammaOscillator (Model C, 5K neurons, float32)
    → HdcCognitiveIntegrator (Stage 21, 10K-dim HDC)
    → MobileActionDecoder (Stage 20)
```

## Verification
- Integration test: PASS
- RAM gate: PASS (38.06 MB < 1000 MB)
- HDC recall: PASS (2/2 rules retrieved correctly)
- Model checkpoint: consolidated (308 MB)

## Branch
LAB_ONLY
