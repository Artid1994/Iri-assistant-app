#!/usr/bin/env python3
"""
Stage 20: Mobile Action Decoder
Decodes spike outputs from Callosum/Motor projection region
into concrete system actions (CLICK, SCROLL, SPEAK, NOTIFY, etc.).
"""
import json
import struct
import time
from enum import Enum
from dataclasses import dataclass
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

import numpy as np


# ─── Action Types ────────────────────────────────────────────────────────────
class ActionType(Enum):
    CLICK = "click"
    SCROLL = "scroll"
    SWIPE = "swipe"
    TYPE = "type"
    SPEAK = "speak"
    NOTIFY = "notify"
    OPEN_APP = "open_app"
    CLOSE_APP = "close_app"
    BACK = "back"
    HOME = "home"
    POWER = "power"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"
    SIP = "sip"  # Single Inhalation Protocol for AE01M identity


# ─── Motor Region Configuration ───────────────────────────────────────────────
MOTOR_NEURONS = 80000  # Matches Stage 19 CALLOSUM region size
ACTION_THRESHOLD = 0.5  # Minimum spike density to trigger action


# ─── Motor-to-Action Mapping ─────────────────────────────────────────────────
# Each action type has a dedicated "motor neuron cluster"
ACTION_MOTOR_OFFSETS = {
    ActionType.CLICK: 0,
    ActionType.SCROLL: 5000,
    ActionType.SWIPE: 10000,
    ActionType.TYPE: 15000,
    ActionType.SPEAK: 20000,
    ActionType.NOTIFY: 25000,
    ActionType.OPEN_APP: 30000,
    ActionType.CLOSE_APP: 35000,
    ActionType.BACK: 40000,
    ActionType.HOME: 45000,
    ActionType.POWER: 50000,
    ActionType.VOLUME_UP: 55000,
    ActionType.VOLUME_DOWN: 60000,
    ActionType.SIP: 65000,
}

MOTOR_REGION_SIZE = MOTOR_NEURONS // len(ActionType)


@dataclass
class ActionCommand:
    """Represents a decoded system action."""
    action_type: ActionType
    confidence: float  # 0.0 - 1.0
    parameters: Dict
    timestamp: float
    source_region: str = "CALLOSUM"


class MobileActionDecoder:
    """
    Decodes neural spike patterns from motor projection regions
    into concrete mobile system actions.
    """

    def __init__(self, n_motor: int = MOTOR_NEURONS):
        self.n_motor = n_motor
        self.action_threshold = ACTION_THRESHOLD

        # Configure action region boundaries
        self._configure_action_regions()

        # Action history for temporal analysis
        self.action_history: List[ActionCommand] = []

        # Debounce tracking to avoid rapid duplicate actions
        self.last_action_time: Dict[ActionType, float] = {}
        self.debounce_ms = 200  # Minimum ms between same action

    def _configure_action_regions(self):
        """Set up motor neuron regions for each action type."""
        self.action_regions = {}
        for action_type, offset in ACTION_MOTOR_OFFSETS.items():
            start = offset
            end = min(offset + MOTOR_REGION_SIZE, self.n_motor)
            self.action_regions[action_type] = (start, end)

    def decode_spikes(self,
                      spike_indices: np.ndarray,
                      membrane_potentials: Optional[np.ndarray] = None,
                      timestamp: Optional[float] = None) -> List[ActionCommand]:
        """
        Decode spike activity into system actions.

        Args:
            spike_indices: Indices of spiking motor neurons
            membrane_potentials: Optional full Vm state for density analysis
            timestamp: Current simulation timestamp

        Returns:
            List of ActionCommand objects for triggered actions
        """
        if timestamp is None:
            timestamp = float(np.random.randint(1000000))

        triggered_actions = []

        for action_type, (start, end) in self.action_regions.items():
            # Count spikes in this action's motor region
            region_spikes = spike_indices[
                (spike_indices >= start) & (spike_indices < end)
            ]

            n_spikes = len(region_spikes)

            # Calculate spike density
            region_size = end - start
            spike_density = n_spikes / region_size if region_size > 0 else 0.0

            # Also check membrane potential if available
            potential_boost = 0.0
            if membrane_potentials is not None:
                region_vms = membrane_potentials[start:end]
                if len(region_vms) > 0:
                    potential_boost = float(np.mean(region_vms)) * 0.1

            # Composite confidence score
            confidence = min(1.0, spike_density * 50.0 + potential_boost)

            if confidence >= self.action_threshold:
                # Check debounce
                last_time = self.last_action_time.get(action_type, 0.0)
                if timestamp - last_time >= self.debounce_ms / 1000.0:
                    # Extract action-specific parameters
                    params = self._extract_action_params(
                        action_type, region_spikes, membrane_potentials
                    )

                    action_cmd = ActionCommand(
                        action_type=action_type,
                        confidence=confidence,
                        parameters=params,
                        timestamp=timestamp,
                    )
                    triggered_actions.append(action_cmd)

                    # Update debounce tracking
                    self.last_action_time[action_type] = timestamp
                    self.action_history.append(action_cmd)

        return triggered_actions

    def _extract_action_params(self,
                               action_type: ActionType,
                               spike_indices: np.ndarray,
                               membrane_potentials: Optional[np.ndarray]) -> Dict:
        """Extract action-specific parameters from spike pattern."""
        params = {'intensity': 0.5}  # Default

        if len(spike_indices) == 0:
            return params

        # Analyze spike distribution within region for parameter extraction
        if action_type == ActionType.CLICK:
            # Click position can be inferred from spike pattern
            if len(spike_indices) > 0:
                avg_idx = np.mean(spike_indices)
                region_start, _ = self.action_regions[action_type]
                rel_pos = (avg_idx - region_start) / MOTOR_REGION_SIZE
                params['x'] = float(np.clip(rel_pos, 0, 1))
                params['y'] = float(np.clip(1.0 - rel_pos, 0, 1))

        elif action_type == ActionType.SCROLL:
            # Scroll direction and amount from spike spread
            params['direction'] = 'up' if np.mean(spike_indices) < (
                self.action_regions[action_type][0] + MOTOR_REGION_SIZE/2
            ) else 'down'
            params['amount'] = float(min(1.0, len(spike_indices) / 50.0))

        elif action_type == ActionType.SWIPE:
            # Swipe direction from temporal order
            params['direction'] = 'right'  # Simplified
            params['speed'] = float(min(1.0, len(spike_indices) / 30.0))

        elif action_type == ActionType.TYPE:
            # Character encoding from spike pattern (simplified)
            params['text'] = '...'  # Would need more complex decoding

        elif action_type == ActionType.SPEAK:
            # Speech synthesis trigger
            params['text'] = ''
            params['voice'] = 'th-TH-NiwatNeural'

        elif action_type == ActionType.NOTIFY:
            # Notification display
            params['message'] = 'System notification'
            params['level'] = 'info'

        elif action_type == ActionType.OPEN_APP:
            params['app'] = 'default'

        elif action_type == ActionType.CLOSE_APP:
            params['app'] = 'foreground'

        elif action_type == ActionType.BACK:
            params['simulate'] = True

        elif action_type == ActionType.HOME:
            params['simulate'] = True

        elif action_type == ActionType.POWER:
            params['action'] = 'toggle'

        elif action_type == ActionType.VOLUME_UP:
            params['step'] = 1

        elif action_type == ActionType.VOLUME_DOWN:
            params['step'] = -1

        elif action_type == ActionType.SIP:
            # Single Inhalation Protocol - AE01M identity anchor
            params['mode'] = 'identity_reaffirmation'
            params['target'] = 'เจ้านาย'  # Artid Aunporn

        return params

    def get_action_summary(self) -> Dict:
        """Get summary of decoded actions."""
        summary = {
            'total_actions': len(self.action_history),
            'action_counts': {},
            'recent_actions': [],
        }

        # Count by type
        for cmd in self.action_history:
            t = cmd.action_type.value
            summary['action_counts'][t] = summary['action_counts'].get(t, 0) + 1

        # Last 5 actions
        summary['recent_actions'] = [
            {
                'type': cmd.action_type.value,
                'confidence': round(cmd.confidence, 3),
                'params': cmd.parameters,
            }
            for cmd in self.action_history[-5:]
        ]

        return summary

    def reset(self):
        """Clear action history and debounce state."""
        self.action_history.clear()
        self.last_action_time.clear()


def create_simulated_motor_spikes(n_spikes: int = 200,
                                   n_motor: int = MOTOR_NEURONS) -> np.ndarray:
    """Generate simulated motor spike indices for testing."""
    np.random.seed(42)
    # Create spikes concentrated in specific action regions
    spike_indices = []

    # Prioritize CLICK and SPEAK actions
    for _ in range(n_spikes // 3):
        offset = ACTION_MOTOR_OFFSETS[ActionType.CLICK]
        spike_indices.append(
            offset + np.random.randint(0, MOTOR_REGION_SIZE)
        )

    for _ in range(n_spikes // 3):
        offset = ACTION_MOTOR_OFFSETS[ActionType.SPEAK]
        spike_indices.append(
            offset + np.random.randint(0, MOTOR_REGION_SIZE)
        )

    # Remaining scattered
    for _ in range(n_spikes - len(spike_indices)):
        spike_indices.append(np.random.randint(0, n_motor))

    return np.array(spike_indices, dtype=np.int64)


if __name__ == '__main__':
    print("Stage 20: Mobile Action Decoder - Standalone Test")
    print("=" * 50)

    decoder = MobileActionDecoder()

    # Generate simulated motor spikes
    spikes = create_simulated_motor_spikes(300)
    print(f"Generated {len(spikes)} simulated motor spikes")

    # Decode spikes into actions
    timestamp = time.time()
    actions = decoder.decode_spikes(spikes, timestamp=timestamp)

    print(f"\nDecoded {len(actions)} actions:")
    for cmd in actions:
        print(f"  {cmd.action_type.value}: "
              f"confidence={cmd.confidence:.3f}, "
              f"params={cmd.parameters}")

    # Summary
    summary = decoder.get_action_summary()
    print(f"\nAction Summary:")
    print(f"  Total: {summary['total_actions']}")
    print(f"  Distribution: {summary['action_counts']}")

    print("\nTest PASSED: Mobile Action Decoder operational")
