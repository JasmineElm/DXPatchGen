"""
Tests for DXPatchGen CLI commands.
"""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from dxpatchgen.cli.app import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "DXPatchGen version" in result.stdout


def test_cli_generate_single_and_save(tmp_path: Path):
    out_file = tmp_path / "patch.syx"
    result = runner.invoke(
        app,
        [
            "generate",
            "--category", "keys",
            "--algorithm", "5",
            "--seed", "42",
            "--output", str(out_file),
            "--name", "E PIANO 1",
        ],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    assert out_file.stat().st_size == 4104  # standard Dexed-compatible 32-voice bank


def test_cli_generate_voice_dump_format(tmp_path: Path):
    out_file = tmp_path / "voice.syx"
    result = runner.invoke(
        app,
        [
            "generate",
            "--category", "keys",
            "--format", "voice",
            "--output", str(out_file),
        ],
    )
    assert result.exit_code == 0
    assert out_file.exists()
    assert out_file.stat().st_size == 163  # standard 1-voice bulk SysEx


def test_cli_bank_generation(tmp_path: Path):
    out_bank = tmp_path / "bank.syx"
    result = runner.invoke(
        app,
        [
            "bank",
            "--category", "mixed",
            "--seed", "99",
            "--output", str(out_bank),
        ],
    )
    assert result.exit_code == 0
    assert out_bank.exists()
    assert out_bank.stat().st_size == 4104  # standard 32-voice bank Syx


def test_cli_inspect(tmp_path: Path):
    out_file = tmp_path / "test.syx"
    runner.invoke(app, ["generate", "--output", str(out_file), "--seed", "123"])

    result = runner.invoke(app, ["inspect", str(out_file)])
    assert result.exit_code == 0
    assert "OPERATOR MATRIX" in result.stdout


def test_cli_mutate(tmp_path: Path):
    out_file = tmp_path / "source.syx"
    runner.invoke(app, ["generate", "--output", str(out_file), "--seed", "123"])

    mutated_file = tmp_path / "mutated.syx"
    result = runner.invoke(app, ["mutate", str(out_file), "--output", str(mutated_file), "--rate", "0.3"])
    assert result.exit_code == 0
    assert mutated_file.exists()


def test_cli_list_algorithms():
    result = runner.invoke(app, ["list-algorithms", "--id", "1"])
    assert result.exit_code == 0
    assert "Algorithm 1" in result.stdout
