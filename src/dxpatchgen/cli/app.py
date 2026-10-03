"""
Command-line interface for DXPatchGen.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dxpatchgen.cli.display import render_algorithm_panel, render_patch_view
from dxpatchgen.core.algorithms import ALGORITHMS, get_algorithm
from dxpatchgen.core.bank import DX7Bank
from dxpatchgen.core.models import DX7Patch
from dxpatchgen.core.sysex import read_sysex, write_sysex
from dxpatchgen.generator.base import GenerationOptions
from dxpatchgen.generator.mutator import PatchMutator
from dxpatchgen.generator.templates import GENERATOR_REGISTRY, get_generator

app = typer.Typer(
    name="dxpatchgen",
    help="🎹 Yamaha DX7 Patch Generator, Mutator, Bank Manager & Sound Design Tool",
    add_completion=False,
    no_args_is_help=False,
)

console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version information"),
) -> None:
    if version:
        import dxpatchgen
        console.print(f"[bold cyan]DXPatchGen[/bold cyan] version [green]{dxpatchgen.__version__}[/green]")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        # Default action: run generate command
        generate()


@app.command("generate", help="Generate one or more random DX7 patches")
def generate(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Path to save generated .syx file (e.g. patch.syx)"
    ),
    category: str = typer.Option(
        "constrained",
        "--category",
        "-c",
        help="Sound category: constrained, random, keys, bass, pad, percussive, lead, bell, fx",
    ),
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        "-P",
        help="Sonic profile layer: warm, atonal, crisp, gritty, ethereal",
    ),
    algorithm: Optional[int] = typer.Option(
        None, "--algorithm", "-a", min=1, max=32, help="Force specific algorithm (1-32)"
    ),
    brightness: float = typer.Option(
        0.6, "--brightness", min=0.0, max=1.0, help="Brightness / FM modulation index (0.0 - 1.0)"
    ),
    dissonance: float = typer.Option(
        0.0, "--dissonance", min=0.0, max=1.0, help="Inharmonicity / ratio dissonance (0.0 - 1.0)"
    ),
    detune: float = typer.Option(
        0.3, "--detune", min=0.0, max=1.0, help="Detuning spread between operators (0.0 - 1.0)"
    ),
    envelope_speed: float = typer.Option(
        0.5, "--speed", min=0.0, max=1.0, help="Envelope speed (0.0 = slow pad, 1.0 = snappy pluck)"
    ),
    seed: Optional[int] = typer.Option(
        None, "--seed", "-s", help="Random seed for deterministic patch generation"
    ),
    name: Optional[str] = typer.Option(
        None, "--name", "-n", help="Custom patch name (up to 10 characters)"
    ),
    count: int = typer.Option(
        1, "--count", min=1, max=32, help="Number of patches to generate"
    ),
    format: str = typer.Option(
        "bank",
        "--format",
        "-f",
        help="SysEx output format: 'bank' (4,104 bytes for Dexed/hardware) or 'voice' (163 bytes single voice dump)",
    ),
    play: bool = typer.Option(
        False, "--play", "-p", help="Play preview audio using built-in FM synth engine"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Quiet mode: suppress visual patch inspection"
    ),
) -> None:
    """Generate random Yamaha DX7 patch(es)."""
    gen = get_generator(category)

    patches = []
    for i in range(count):
        cur_seed = seed + i if seed is not None else None
        opts = GenerationOptions(
            seed=cur_seed,
            algorithm=algorithm,
            category=category,
            profile=profile,
            brightness=brightness,
            dissonance=dissonance,
            detune_amount=detune,
            envelope_speed=envelope_speed,
            name=name if count == 1 else None,
        )
        patch = gen.generate(opts)
        patches.append(patch)

        if not quiet:
            prefix_info = f"[{category.upper()}" + (f":{profile.upper()}]" if profile else "]")
            panel = render_patch_view(patch, title_prefix=f"Generated {prefix_info}")
            console.print(panel)

        if play:
            from dxpatchgen.synth.player import AudioPlayer
            console.print(f"[bold cyan]▶ Auditioning '{patch.name.strip()}'...[/bold cyan]")
            thread = AudioPlayer.play_patch_async(patch, mode="arpeggio")
            thread.join()

    if output:
        fmt = format.lower().strip()
        if fmt == "voice" and count == 1:
            saved_path = write_sysex(patches[0], output)
            console.print(
                f"[bold green]✓[/bold green] Saved single voice dump to [cyan]{saved_path}[/cyan] (163 bytes)"
            )
        else:
            # Default: standard 32-voice bank compatible with Dexed Cartridge loader
            bank = DX7Bank(patches=patches)
            saved_path = bank.save(output)
            console.print(
                f"[bold green]✓[/bold green] Saved to [cyan]{saved_path}[/cyan] (4,104 bytes, Dexed-compatible 32-voice bank)"
            )
    elif not quiet and count == 1:
        console.print("[dim]Tip: Use --output my_patch.syx to export to a standard Dexed-compatible SysEx file.[/dim]")


@app.command("play", help="Audition a DX7 patch (.syx) using the built-in FM audio synthesizer")
def play_cmd(
    file_path: Path = typer.Argument(..., exists=True, help="Path to .syx file to play"),
    slot: int = typer.Option(1, "--slot", "-s", min=1, max=32, help="Bank slot (1-32) to play if bank file"),
    mode: str = typer.Option("arpeggio", "--mode", "-m", help="Playback mode: 'arpeggio' or 'note'"),
    note: int = typer.Option(60, "--note", help="MIDI note number for single note playback (60 = Middle C)"),
) -> None:
    """Play audio preview of a .syx file."""
    from dxpatchgen.synth.player import AudioPlayer

    data = read_sysex(file_path)
    if isinstance(data, list):
        target_patch = data[slot - 1]
        console.print(f"[bold cyan]▶ Playing Bank Slot {slot:02d}: '{target_patch.name.strip()}' ({file_path.name})...[/bold cyan]")
    else:
        target_patch = data
        console.print(f"[bold cyan]▶ Playing Voice: '{target_patch.name.strip()}' ({file_path.name})...[/bold cyan]")

    thread = AudioPlayer.play_patch_async(target_patch, mode=mode, midi_note=note)
    thread.join()


@app.command("bank", help="Generate a full 32-voice DX7 bank (.syx)")
def bank_cmd(
    output: Path = typer.Option(
        Path("dx7_bank.syx"), "--output", "-o", help="Path to save 32-voice bank .syx file"
    ),
    category: str = typer.Option(
        "mixed",
        "--category",
        "-c",
        help="Category for bank voices: mixed, keys, bass, pad, percussive, lead, bell, fx, random",
    ),
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        "-P",
        help="Sonic profile layer: warm, atonal, crisp, gritty, ethereal",
    ),
    seed: Optional[int] = typer.Option(
        None, "--seed", "-s", help="Random seed for deterministic bank generation"
    ),
) -> None:
    """Generate a full 32-patch DX7 Bank."""
    import random
    rng = random.Random(seed) if seed is not None else random.Random()

    available_categories = ["keys", "bass", "pad", "percussive", "lead", "bell", "fx", "constrained"]
    patches = []

    title_text = f"Generating 32-Voice DX7 Bank" + (f" (Profile: {profile.upper()})" if profile else "")
    table = Table(title=f"[bold cyan]{title_text}[/bold cyan]", show_edge=True)
    table.add_column("Slot", justify="right", style="bold")
    table.add_column("Patch Name", style="bold green")
    table.add_column("Category", style="yellow")
    table.add_column("Algorithm", justify="center")
    table.add_column("Feedback", justify="center")

    for i in range(1, 33):
        cat = rng.choice(available_categories) if category == "mixed" else category
        gen = get_generator(cat)
        p_seed = rng.randint(0, 1_000_000)
        opts = GenerationOptions(seed=p_seed, category=cat, profile=profile)
        p = gen.generate(opts)
        patches.append(p)
        table.add_row(f"{i:02d}", p.name.strip(), cat.capitalize(), str(p.algorithm), str(p.feedback))

    bank = DX7Bank(patches=patches)
    saved_path = bank.save(output)
    console.print(table)
    console.print(f"\n[bold green]✓[/bold green] Successfully created 32-patch bank at [bold cyan]{saved_path}[/bold cyan] (4104 bytes)")


@app.command("inspect", help="Inspect and display parameters of an existing .syx file")
def inspect_cmd(
    file_path: Path = typer.Argument(..., exists=True, help="Path to .syx file to inspect"),
    slot: int = typer.Option(1, "--slot", "-s", min=1, max=32, help="Bank slot (1-32) to display details for"),
) -> None:
    """Inspect DX7 SysEx file."""
    data = read_sysex(file_path)

    if isinstance(data, DX7Patch):
        console.print(render_patch_view(data, title_prefix=f"Single Voice: {file_path.name}"))
    elif isinstance(data, list):
        console.print(f"[bold cyan]32-Voice Bank:[/bold cyan] [green]{file_path.name}[/green] ({len(data)} voices)")
        table = Table(title=f"Voices in {file_path.name}", show_edge=True)
        table.add_column("Slot", justify="right")
        table.add_column("Name", style="bold green")
        table.add_column("Algorithm", justify="center")
        table.add_column("Feedback", justify="center")

        for idx, patch in enumerate(data, 1):
            table.add_row(f"{idx:02d}", patch.name.strip(), str(patch.algorithm), str(patch.feedback))
        console.print(table)

        # Show details for requested slot
        target_patch = data[slot - 1]
        console.print(render_patch_view(target_patch, title_prefix=f"Slot {slot:02d} Details"))


@app.command("mutate", help="Mutate an existing DX7 .syx patch")
def mutate_cmd(
    file_path: Path = typer.Argument(..., exists=True, help="Input .syx file to mutate"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output .syx file path"),
    rate: float = typer.Option(0.2, "--rate", "-r", min=0.0, max=1.0, help="Mutation intensity (0.0 - 1.0)"),
    seed: Optional[int] = typer.Option(None, "--seed", "-s", help="Random seed"),
) -> None:
    """Mutate an existing patch."""
    data = read_sysex(file_path)
    source_patch = data[0] if isinstance(data, list) else data

    mutated = PatchMutator.mutate(source_patch, mutation_rate=rate, seed=seed)
    console.print(render_patch_view(mutated, title_prefix=f"Mutated from {source_patch.name.strip()}"))

    if output:
        saved_path = write_sysex(mutated, output)
        console.print(f"[bold green]✓[/bold green] Saved mutated patch to [cyan]{saved_path}[/cyan]")


@app.command("list-algorithms", help="Display all 32 DX7 algorithms and their topologies")
def list_algorithms_cmd(
    alg_id: Optional[int] = typer.Option(None, "--id", "-i", min=1, max=32, help="Specific algorithm ID")
) -> None:
    """List DX7 algorithms."""
    if alg_id is not None:
        p = DX7Patch(algorithm=alg_id)
        console.print(render_algorithm_panel(p))
    else:
        for i in range(1, 33):
            p = DX7Patch(algorithm=i)
            console.print(render_algorithm_panel(p))


@app.command("tui", help="Launch interactive full-screen Terminal User Interface")
def tui_cmd() -> None:
    """Launch interactive TUI."""
    from dxpatchgen.tui.app import launch_tui
    launch_tui()


if __name__ == "__main__":
    app()
