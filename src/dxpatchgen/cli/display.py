"""
Rich terminal visualization for DX7 Patches, Operator matrices, and Algorithms.
"""

from __future__ import annotations

from typing import List

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dxpatchgen.core.algorithms import get_algorithm
from dxpatchgen.core.models import DX7Patch, Operator


def make_envelope_bar(r1: int, r2: int, r3: int, r4: int, l1: int, l2: int, l3: int, l4: int) -> str:
    """Generate a compact ASCII representation of an EG envelope."""
    # Attack slope
    att = "╱" if r1 < 70 else "↑"
    # Decay
    dec = "╲" if l2 < l1 else "─"
    # Sustain
    sus = "━" if l3 > 50 else "─"
    # Rel
    rel = "⮡"
    return f"{att}{dec}{sus}{rel} [L:{l1},{l2},{l3},{l4} R:{r1},{r2},{r3},{r4}]"


def render_operator_table(patch: DX7Patch) -> Table:
    """Render a colored Rich Table of the 6 operators."""
    alg_info = get_algorithm(patch.algorithm)
    carrier_set = set(alg_info.carriers)

    table = Table(
        title="[bold cyan]DX7 OPERATOR MATRIX[/bold cyan]",
        title_justify="left",
        header_style="bold magenta",
        show_edge=True,
        expand=True,
    )

    table.add_column("OP", justify="center", style="bold")
    table.add_column("Role", justify="center")
    table.add_column("Level", justify="right")
    table.add_column("Mode", justify="center")
    table.add_column("Ratio / Freq", justify="right", style="green")
    table.add_column("Detune", justify="right")
    table.add_column("Vel Sens", justify="center")
    table.add_column("Rate Sc", justify="center")
    table.add_column("Envelope (R1..R4 / L1..L4)", justify="left", style="yellow")

    # Display OP6 down to OP1 (DX7 convention)
    for op_num in range(6, 0, -1):
        op = patch.op(op_num)
        is_carrier = op_num in carrier_set
        role_style = "bold green" if is_carrier else "dim cyan"
        role_icon = "🔊 CARRIER" if is_carrier else "⚡ MODULATOR"

        ratio_str = f"{op.frequency_ratio:.3f}" if op.osc_mode == 0 else f"{op.freq_coarse} Hz (fix)"
        det_sign = f"{op.detune_cents:+d}" if op.detune_cents != 0 else "0"

        env_str = (
            f"R:{op.eg_rate_1:02d},{op.eg_rate_2:02d},{op.eg_rate_3:02d},{op.eg_rate_4:02d} "
            f"L:{op.eg_level_1:02d},{op.eg_level_2:02d},{op.eg_level_3:02d},{op.eg_level_4:02d}"
        )

        table.add_row(
            f"OP{op_num}",
            f"[{role_style}]{role_icon}[/{role_style}]",
            f"{op.output_level:02d}",
            "Ratio" if op.osc_mode == 0 else "Fixed",
            ratio_str,
            det_sign,
            str(op.key_vel_sens),
            str(op.rate_scaling),
            env_str,
        )

    return table


def render_algorithm_panel(patch: DX7Patch) -> Panel:
    """Render the algorithm diagram and common parameters."""
    alg_info = get_algorithm(patch.algorithm)

    common_info = (
        f"[bold]Algorithm:[/bold] {patch.algorithm}/32\n"
        f"[bold]Feedback:[/bold] {patch.feedback} (on OP{alg_info.feedback_op})\n"
        f"[bold]Transpose:[/bold] {patch.transpose_note} ({patch.transpose})\n"
        f"[bold]Key Sync:[/bold] {'ON' if patch.key_sync else 'OFF'}\n"
        f"[bold]LFO Wave:[/bold] {patch.lfo.waveform_name} (Spd:{patch.lfo.speed}, Dly:{patch.lfo.delay})\n"
        f"[bold]Pitch Mod:[/bold] Depth:{patch.lfo.pitch_mod_depth}, Sens:{patch.lfo.pitch_mod_sens}"
    )

    content = Table.grid(expand=True, padding=(0, 2))
    content.add_column(ratio=1)
    content.add_column(ratio=1)

    diagram_text = Text(f"{alg_info.ascii_diagram}\n{alg_info.description}", style="bold green")
    content.add_row(
        diagram_text,
        Panel(common_info, title="[cyan]Common Parameters[/cyan]", border_style="dim"),
    )

    return Panel(
        content,
        title=f"[bold yellow]Algorithm {patch.algorithm} Topology[/bold yellow]",
        border_style="cyan",
    )


def render_patch_view(patch: DX7Patch, title_prefix: str = "DX7 Voice") -> Panel:
    """Render a complete, rich overview of a DX7 patch."""
    op_table = render_operator_table(patch)
    alg_panel = render_algorithm_panel(patch)

    group = Group(
        alg_panel,
        op_table,
    )

    header = f"🎹 [bold white on blue] {patch.name.strip()} [/bold white on blue] — {title_prefix}"
    return Panel(group, title=header, border_style="bright_blue", expand=True)
