"""
Asynchronous, non-blocking audio player for previewing DX7 patches.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional, Sequence

from dxpatchgen.core.models import DX7Patch
from dxpatchgen.synth.engine import DX7SynthEngine


class AudioPlayer:
    """
    Non-blocking background audio player for DX7 patch previews.
    """

    _current_process: Optional[subprocess.Popen] = None
    _lock = threading.Lock()

    @classmethod
    def stop(cls) -> None:
        """Stop any currently playing audio."""
        with cls._lock:
            if cls._current_process is not None:
                try:
                    cls._current_process.terminate()
                    cls._current_process = None
                except Exception:
                    pass

    @classmethod
    def play_patch_async(
        cls,
        patch: DX7Patch,
        mode: str = "arpeggio",  # 'arpeggio' or 'note'
        midi_note: int = 60,
    ) -> threading.Thread:
        """
        Synthesize and play DX7Patch in background thread without blocking UI.
        """
        thread = threading.Thread(
            target=cls._render_and_play,
            args=(patch, mode, midi_note),
            daemon=True,
        )
        thread.start()
        return thread

    @classmethod
    def _render_and_play(cls, patch: DX7Patch, mode: str, midi_note: int) -> None:
        cls.stop()

        # 1. Synthesize audio WAV buffer
        if mode == "arpeggio":
            wav_data = DX7SynthEngine.render_arpeggio_wav(patch)
        else:
            wav_data = DX7SynthEngine.render_note_wav(patch, midi_note=midi_note)

        # 2. Write to temporary WAV file
        temp_dir = tempfile.gettempdir()
        temp_wav = Path(temp_dir) / f"dxpatchgen_preview_{os.getpid()}.wav"
        temp_wav.write_bytes(wav_data)

        # 3. Detect system audio player command
        player_cmd = cls._find_audio_player()
        if not player_cmd:
            return

        try:
            with cls._lock:
                cls._current_process = subprocess.Popen(
                    [player_cmd, str(temp_wav)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            cls._current_process.wait()
        except Exception:
            pass
        finally:
            with cls._lock:
                cls._current_process = None
            try:
                if temp_wav.exists():
                    temp_wav.unlink()
            except Exception:
                pass

    @staticmethod
    def _find_audio_player() -> Optional[str]:
        """Find appropriate CLI audio player binary (afplay on macOS, aplay/paplay on Linux)."""
        for cmd in ["afplay", "pw-play", "paplay", "aplay"]:
            if shutil.which(cmd):
                return cmd
        return None
