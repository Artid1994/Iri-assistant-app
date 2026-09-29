#!/usr/bin/env python3
"""
Stage 20: Mobile Sensory Bridge
Converts mobile system events (Notifications, App State, Battery, Touch)
into LIF sensory voltage spikes for the brain model.
"""
import json
import time
import numpy as np
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


# ─── Mobile Event Types ──────────────────────────────────────────────────────
class MobileEventType(Enum):
    NOTIFICATION = "notification"
    APP_STATE = "app_state"
    BATTERY = "battery"
    TOUCH = "touch"
    LOCATION = "location"
    SMS = "sms"
    CALL = "call"


# ─── Sensory Encoding Parameters ─────────────────────────────────────────────
SENSORY_NEURONS = 20000  # Matches Stage 19 SENSORY region size
SPIKE_THRESHOLD_mV = 1.0
LEAK_DECAY = 0.95
RESTING_POTENTIAL = 0.0
DT_MS = 1.0

# Sensory encoding base voltage per event type (scaled for reliable spiking)
EVENT_VOLTAGE = {
    MobileEventType.NOTIFICATION: 0.50,
    MobileEventType.APP_STATE: 0.40,
    MobileEventType.BATTERY: 0.35,
    MobileEventType.TOUCH: 0.55,
    MobileEventType.LOCATION: 0.35,
    MobileEventType.SMS: 0.50,
    MobileEventType.CALL: 0.60,
}


@dataclass
class MobileEvent:
    """Represents a mobile system event."""
    event_type: MobileEventType
    timestamp: float
    payload: Dict
    priority: int = 1  # 1-10, higher = more urgent


class MobileSensoryBridge:
    """
    Translates mobile events into sensory neuron activations.
    Each event type maps to a specific region of the SENSORY layer.
    """

    def __init__(self, n_sensory: int = SENSORY_NEURONS):
        self.n_sensory = n_sensory
        self.sensory_state = np.zeros(n_sensory, dtype=np.float32)
        self.event_history: List[MobileEvent] = []

        # Define sensory region offsets for each event type
        self.type_offsets = self._compute_type_offsets()

    def _compute_type_offsets(self) -> Dict[MobileEventType, int]:
        """Divide SENSORY layer into regions for each event type."""
        n_types = len(MobileEventType)
        region_size = self.n_sensory // n_types
        offsets = {}
        for i, event_type in enumerate(MobileEventType):
            offsets[event_type] = i * region_size
        return offsets

    def encode_event(self, event: MobileEvent) -> np.ndarray:
        """
        Convert a mobile event into a sensory voltage pattern.
        Returns a voltage vector to inject into the sensory layer.
        """
        event_type = event.event_type
        offset = self.type_offsets.get(event_type, 0)
        region_size = self.n_sensory // len(MobileEventType)

        # Base voltage from event type
        base_voltage = EVENT_VOLTAGE.get(event_type, 0.20)

        # Priority multiplier (higher priority = stronger signal)
        priority_scale = 0.5 + (event.priority / 10.0) * 0.5

        # Payload-specific modulation
        payload_mod = self._extract_payload_modulation(event)

        # Construct voltage pattern
        voltage_pattern = np.zeros(self.n_sensory, dtype=np.float32)

        # Activate neurons in this event type's region
        region_start = offset
        region_end = min(offset + region_size, self.n_sensory)

        # Create distributed activation within region
        n_active = max(10, int(region_size * 0.1))  # 10% of region
        active_indices = np.random.choice(
            region_end - region_start, n_active, replace=False
        ) + region_start

        for idx in active_indices:
            # Add some temporal structure
            phase = (idx % 100) / 100.0
            temporal_mod = 0.8 + 0.2 * np.sin(phase * 2 * np.pi)
            voltage_pattern[idx] = base_voltage * priority_scale * payload_mod * temporal_mod

        return voltage_pattern

    def _extract_payload_modulation(self, event: MobileEvent) -> float:
        """Extract modulation from event payload."""
        payload = event.payload
        mod = 1.0

        if event.event_type == MobileEventType.NOTIFICATION:
            # Urgent notifications get higher modulation
            if payload.get('urgent', False):
                mod = 1.5
            elif payload.get('sound', False):
                mod = 1.2

        elif event.event_type == MobileEventType.BATTERY:
            # Low battery = urgent signal
            level = payload.get('level', 100) / 100.0
            if level < 0.2:
                mod = 1.8
            elif level < 0.5:
                mod = 1.3

        elif event.event_type == MobileEventType.TOUCH:
            # Touch pressure/position affects signal
            pressure = payload.get('pressure', 0.5)
            mod = 0.8 + pressure * 0.4

        elif event.event_type == MobileEventType.APP_STATE:
            # Foreground apps have higher weight
            if payload.get('foreground', False):
                mod = 1.3

        return mod

    def inject_events(self, events: List[MobileEvent]) -> np.ndarray:
        """
        Process multiple events and return combined sensory voltage.
        Events closer in time have temporal summation.
        """
        combined = np.zeros(self.n_sensory, dtype=np.float32)

        for event in events:
            pattern = self.encode_event(event)
            combined += pattern
            self.event_history.append(event)

        # Apply leak to previous state
        self.sensory_state *= LEAK_DECAY

        # Add new injections
        self.sensory_state += combined

        # Clamp to valid range
        self.sensory_state = np.clip(
            self.sensory_state, -2.0, SPIKE_THRESHOLD_mV * 1.5
        )

        return self.sensory_state.copy()

    def get_spikes(self, threshold: float = SPIKE_THRESHOLD_mV) -> np.ndarray:
        """Return indices of sensory neurons that would fire."""
        return np.where(self.sensory_state >= threshold)[0]

    def get_spike_count(self) -> int:
        """Return number of sensory neurons above threshold."""
        return int((self.sensory_state >= SPIKE_THRESHOLD_mV).sum())

    def get_mean_voltage(self) -> float:
        """Return mean sensory voltage."""
        return float(self.sensory_state.mean())

    def reset(self):
        """Reset sensory state."""
        self.sensory_state[:] = RESTING_POTENTIAL
        self.event_history.clear()


def create_simulated_events(n_events: int = 10) -> List[MobileEvent]:
    """Generate simulated mobile events for testing."""
    event_types = list(MobileEventType)
    events = []

    for i in range(n_events):
        event_type = event_types[i % len(event_types)]

        # Create typical payloads
        if event_type == MobileEventType.NOTIFICATION:
            payload = {
                'title': f'Notification {i+1}',
                'body': f'Sample notification body text',
                'sound': i % 3 == 0,
                'urgent': i % 5 == 0,
            }
        elif event_type == MobileEventType.BATTERY:
            payload = {
                'level': max(5, 100 - i * 10),
                'charging': i % 4 == 0,
            }
        elif event_type == MobileEventType.TOUCH:
            payload = {
                'x': np.random.uniform(0, 1),
                'y': np.random.uniform(0, 1),
                'pressure': np.random.uniform(0.3, 1.0),
                'action': 'tap' if i % 2 == 0 else 'swipe',
            }
        elif event_type == MobileEventType.APP_STATE:
            payload = {
                'app': f'App_{i % 5}',
                'foreground': i % 3 == 0,
                'battery_usage': np.random.uniform(0.1, 0.5),
            }
        elif event_type == MobileEventType.LOCATION:
            payload = {
                'lat': np.random.uniform(13.5, 14.0),
                'lon': np.random.uniform(100.0, 101.0),
                'accuracy': np.random.uniform(10, 100),
            }
        elif event_type == MobileEventType.SMS:
            payload = {
                'sender': f'+66123456{i:04d}',
                'body': f'Short message {i}',
                'unread': True,
            }
        elif event_type == MobileEventType.CALL:
            payload = {
                'caller': f'+66987654{i:04d}',
                'duration': i * 30,
                'missed': i % 4 == 0,
            }
        else:
            payload = {}

        events.append(MobileEvent(
            event_type=event_type,
            timestamp=time.time() - (n_events - i) * 0.5,
            payload=payload,
            priority=np.random.randint(1, 11),
        ))

    return events


if __name__ == '__main__':
    # Quick standalone test
    print("Stage 20: Mobile Sensory Bridge - Standalone Test")
    print("=" * 50)

    bridge = MobileSensoryBridge()

    # Generate test events
    events = create_simulated_events(15)
    print(f"Generated {len(events)} simulated events")

    # Process events
    state = bridge.inject_events(events)

    print(f"Sensory neurons: {bridge.n_sensory}")
    print(f"Mean voltage: {bridge.get_mean_voltage():.4f} mV")
    print(f"Spiking neurons: {bridge.get_spike_count()}")
    print(f"Event history: {len(bridge.event_history)} events")

    # Show event type distribution
    type_counts = {}
    for e in events:
        t = e.event_type.value
        type_counts[t] = type_counts.get(t, 0) + 1
    print(f"Event type distribution: {type_counts}")

    print("\nTest PASSED: Mobile Sensory Bridge operational")
