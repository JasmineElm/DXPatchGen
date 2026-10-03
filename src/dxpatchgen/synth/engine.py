"""
Pure-Python Yamaha DX7 6-Operator FM Synthesis Audio Engine.
Renders DX7Patch instances to 16-bit PCM audio WAV files/buffers.
"""

from __future__ import annotations

import io
import math
import struct
import wave
from dataclasses import dataclass
from typing import List, Sequence, Tuple, Union

from dxpatchgen.core.algorithms import get_algorithm
from dxpatchgen.core.models import DX7Patch, Operator


def dx7_rate_to_seconds(rate: int) -> float:
    """
    Convert DX7 envelope rate (0-99) to duration in seconds.
    DX7 rate curves are exponential: 99 is ~2ms, 50 is ~0.5s, 0 is ~30s.
    """
    if rate >= 99:
        return 0.003
    # Approximate DX7 envelope timing curve
    return 30.0 * (10.0 ** (-rate / 25.0)) + 0.003


def midi_to_freq(note_number: int) -> float:
    """Convert MIDI note number (0-127) to frequency in Hz (A4 = 69 = 440Hz)."""
    return 440.0 * (2.0 ** ((note_number - 69.0) / 12.0))


@dataclass
class OperatorState:
    """Runtime DSP state for a single FM operator."""

    phase: float = 0.0
    feedback_history: float = 0.0
    current_level: float = 0.0


class DX7SynthEngine:
    """
    Synthesizes audio from a DX7Patch with 6-operator FM routing,
    envelopes, feedback, and LFO modulation.
    """

    DEFAULT_SAMPLE_RATE = 22050  # Fast, crisp sample rate for instant preview

    @classmethod
    def render_note_wav(
        cls,
        patch: DX7Patch,
        midi_note: int = 60,  # Middle C (C4)
        velocity: int = 100,
        duration: float = 1.5,
        release_start: float = 1.0,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ) -> bytes:
        """
        Render a single MIDI note into a 16-bit mono WAV in-memory buffer.
        """
        raw_pcm = cls.render_note_pcm(
            patch=patch,
            midi_note=midi_note,
            velocity=velocity,
            duration=duration,
            release_start=release_start,
            sample_rate=sample_rate,
        )

        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(raw_pcm)

        return wav_io.getvalue()

    @classmethod
    def render_arpeggio_wav(
        cls,
        patch: DX7Patch,
        notes: Sequence[int] = (48, 52, 55, 60),  # C3, E3, G3, C4
        note_length: float = 0.35,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ) -> bytes:
        """
        Render a preview arpeggio phrase into a WAV in-memory buffer.
        """
        all_pcm = bytearray()
        for idx, note in enumerate(notes):
            # Last note has longer ring out
            dur = note_length * 2.5 if idx == len(notes) - 1 else note_length
            rel = note_length * 1.5 if idx == len(notes) - 1 else note_length * 0.8
            pcm = cls.render_note_pcm(
                patch=patch,
                midi_note=note,
                velocity=100,
                duration=dur,
                release_start=rel,
                sample_rate=sample_rate,
            )
            all_pcm.extend(pcm)

        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(bytes(all_pcm))

        return wav_io.getvalue()

    @classmethod
    def render_note_pcm(
        cls,
        patch: DX7Patch,
        midi_note: int = 60,
        velocity: int = 100,
        duration: float = 1.5,
        release_start: float = 1.0,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
    ) -> bytes:
        """
        Render FM audio synthesis samples to 16-bit PCM byte buffer.
        """
        total_samples = int(duration * sample_rate)
        rel_sample = int(release_start * sample_rate)
        dt = 1.0 / sample_rate
        two_pi = 2.0 * math.pi

        alg_info = get_algorithm(patch.algorithm)
        carrier_set = set(alg_info.carriers)
        fb_op_idx = alg_info.feedback_op - 1

        # Calculate base frequencies & envelope timings for 6 operators
        base_freq = midi_to_freq(midi_note + (patch.transpose - 24))
        op_freqs = []
        op_env_params = []
        op_vel_gains = []

        for i in range(6):
            op = patch.operators[i]
            # Frequency
            if op.osc_mode == 0:
                coarse = 0.5 if op.freq_coarse == 0 else float(op.freq_coarse)
                ratio = coarse * (1.0 + op.freq_fine / 100.0)
                freq = base_freq * ratio
            else:
                base_hz = 10.0 ** (op.freq_coarse % 4)
                freq = base_hz * (1.0 + op.freq_fine / 100.0)

            # Detune offset in Hz
            det_cents = (op.detune - 7) * 1.5
            freq *= 2.0 ** (det_cents / 1200.0)
            op_freqs.append(freq)

            # Envelope timings
            t_a = dx7_rate_to_seconds(op.eg_rate_1)
            t_d1 = dx7_rate_to_seconds(op.eg_rate_2)
            t_d2 = dx7_rate_to_seconds(op.eg_rate_3)
            t_r = dx7_rate_to_seconds(op.eg_rate_4)
            l1 = (op.eg_level_1 / 99.0) ** 2
            l2 = (op.eg_level_2 / 99.0) ** 2
            l3 = (op.eg_level_3 / 99.0) ** 2
            l4 = (op.eg_level_4 / 99.0) ** 2
            out_gain = (op.output_level / 99.0) ** 2.2

            op_env_params.append((t_a, t_d1, t_d2, t_r, l1, l2, l3, l4, out_gain))

            # Velocity sensitivity
            vel_factor = (velocity / 127.0) ** (op.key_vel_sens / 3.0) if op.key_vel_sens > 0 else 1.0
            op_vel_gains.append(vel_factor)

        # Feedback scaling
        fb_gain = (2.0 ** (patch.feedback - 7)) * 2.5 if patch.feedback > 0 else 0.0

        # DSP state variables
        phases = [0.0] * 6
        fb_val = 0.0
        pcm_out = bytearray(total_samples * 2)

        # Operator evaluation order (modulators to carriers: 6 down to 1)
        eval_order = [5, 4, 3, 2, 1, 0]  # indices for OP6..OP1

        for n in range(total_samples):
            t = n * dt
            in_release = n >= rel_sample
            t_rel = (n - rel_sample) * dt if in_release else 0.0

            # 1. Compute operator envelope amplitudes
            op_amps = [0.0] * 6
            for i in range(6):
                t_a, t_d1, t_d2, t_r, l1, l2, l3, l4, out_gain = op_env_params[i]
                if not in_release:
                    if t < t_a:
                        amp = (t / t_a) * l1
                    elif t < t_a + t_d1:
                        frac = (t - t_a) / t_d1
                        amp = l1 + frac * (l2 - l1)
                    else:
                        frac = min(1.0, (t - t_a - t_d1) / t_d2)
                        amp = l2 + frac * (l3 - l2)
                else:
                    amp = l3 * max(0.0, 1.0 - (t_rel / t_r))

                op_amps[i] = amp * out_gain * op_vel_gains[i]

            # 2. Phase accumulator and FM modulation
            # Modulator outputs to feed downstream operators
            op_outputs = [0.0] * 6

            for idx in eval_order:
                op_num = idx + 1
                phase_mod = 0.0

                # Check which modulators feed this operator
                for mod_num, targets in alg_info.connections.items():
                    if op_num in targets:
                        phase_mod += op_outputs[mod_num - 1] * 4.0

                # Apply self-feedback if this is the feedback operator
                if idx == fb_op_idx and patch.feedback > 0:
                    phase_mod += fb_val * fb_gain

                # Compute sine output
                current_phase = phases[idx] + phase_mod
                out = math.sin(current_phase) * op_amps[idx]
                op_outputs[idx] = out

                if idx == fb_op_idx:
                    fb_val = (fb_val + out) * 0.5  # average filter for stability

                # Advance phase
                phases[idx] = (phases[idx] + two_pi * op_freqs[idx] * dt) % two_pi

            # 3. Sum audio from carrier operators
            audio_sample = 0.0
            for carrier_num in alg_info.carriers:
                audio_sample += op_outputs[carrier_num - 1]

            # Soft clip / master scaling
            audio_sample = math.tanh(audio_sample * 1.1)
            int_val = int(audio_sample * 28000.0)
            int_val = max(-32767, min(32767, int_val))
            struct.pack_into("<h", pcm_out, n * 2, int_val)

        return bytes(pcm_out)
