"""
Tests for DX7 FM audio synthesis engine.
"""

import wave
import io
import pytest

from dxpatchgen.core.models import DX7Patch
from dxpatchgen.generator.templates import KeysGenerator, BassGenerator, BellGenerator
from dxpatchgen.synth.engine import DX7SynthEngine, midi_to_freq, dx7_rate_to_seconds


def test_midi_to_freq():
    assert pytest.approx(midi_to_freq(69), 0.01) == 440.0  # A4
    assert pytest.approx(midi_to_freq(60), 0.01) == 261.63  # Middle C


def test_dx7_rate_to_seconds():
    # Rate 99 should be fast attack (~3ms)
    assert dx7_rate_to_seconds(99) <= 0.005
    # Rate 50 should be around 0.5s
    assert 0.1 <= dx7_rate_to_seconds(50) <= 1.0


def test_render_note_wav():
    patch = KeysGenerator().generate()
    wav_data = DX7SynthEngine.render_note_wav(patch, midi_note=60, duration=0.5)

    assert len(wav_data) > 0
    # Verify WAV header
    with wave.open(io.BytesIO(wav_data), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == DX7SynthEngine.DEFAULT_SAMPLE_RATE
        assert wf.getnframes() == int(0.5 * DX7SynthEngine.DEFAULT_SAMPLE_RATE)


def test_render_arpeggio_wav():
    patch = BellGenerator().generate()
    wav_data = DX7SynthEngine.render_arpeggio_wav(patch, notes=[48, 52, 55, 60], note_length=0.1)
    assert len(wav_data) > 0
    with wave.open(io.BytesIO(wav_data), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == DX7SynthEngine.DEFAULT_SAMPLE_RATE
