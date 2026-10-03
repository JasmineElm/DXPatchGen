"""
Interactive Textual TUI for Yamaha DX7 Patch Generation and Sound Design.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    ProgressBar,
    Select,
    Static,
)

from dxpatchgen.core.algorithms import get_algorithm
from dxpatchgen.core.bank import DX7Bank
from dxpatchgen.core.models import DX7Patch
from dxpatchgen.core.sysex import write_sysex
from dxpatchgen.generator.base import GenerationOptions
from dxpatchgen.generator.mutator import PatchMutator
from dxpatchgen.generator.templates import get_generator
from dxpatchgen.synth.player import AudioPlayer


class AlgorithmDisplay(Static):
    """Widget displaying the current algorithm diagram and info."""

    def update_patch(self, patch: DX7Patch) -> None:
        alg_info = get_algorithm(patch.algorithm)
        carriers_str = ", ".join(f"OP{c}" for c in alg_info.carriers)
        modulators_str = ", ".join(f"OP{m}" for m in alg_info.modulators)

        content = (
            f"[bold cyan]Algorithm {patch.algorithm}/32[/bold cyan]\n\n"
            f"{alg_info.ascii_diagram}\n\n"
            f"[bold]Role:[/bold] {alg_info.description}\n"
            f"[bold green]Carriers:[/bold green] {carriers_str}\n"
            f"[bold yellow]Modulators:[/bold yellow] {modulators_str}\n"
            f"[bold magenta]Feedback:[/bold magenta] OP{alg_info.feedback_op} (Level {patch.feedback})\n"
            f"[bold]Transpose:[/bold] {patch.transpose_note}"
        )
        self.update(content)


class OperatorsDisplay(Static):
    """Widget displaying the 6 operators in a structured tabular view."""

    def update_patch(self, patch: DX7Patch) -> None:
        alg_info = get_algorithm(patch.algorithm)
        carrier_set = set(alg_info.carriers)

        lines = [
            "[bold white on blue]  OP | ROLE      | LEVEL | RATIO/FREQ | DETUNE | VEL | ENVELOPE (R1-4/L1-4)         [/bold white on blue]"
        ]

        for op_num in range(6, 0, -1):
            op = patch.op(op_num)
            is_carr = op_num in carrier_set
            role = "[bold green]CARRIER  [/bold green]" if is_carr else "[yellow]MODULATOR[/yellow]"
            ratio_str = f"{op.frequency_ratio:6.3f}" if op.osc_mode == 0 else f"{op.freq_coarse:2d}Hz Fix"
            det = f"{op.detune_cents:+2d}" if op.detune_cents != 0 else " 0"

            env = (
                f"R:{op.eg_rate_1:02d},{op.eg_rate_2:02d},{op.eg_rate_3:02d},{op.eg_rate_4:02d} "
                f"L:{op.eg_level_1:02d},{op.eg_level_2:02d},{op.eg_level_3:02d},{op.eg_level_4:02d}"
            )

            lines.append(
                f" OP{op_num} | {role} |  {op.output_level:02d}   |   {ratio_str}   |  {det:3s}   |  {op.key_vel_sens}  | {env}"
            )

        # LFO info
        lfo = patch.lfo
        lines.append("")
        lines.append(
            f"[bold cyan]LFO:[/bold cyan] {lfo.waveform_name} | Speed: {lfo.speed} | Delay: {lfo.delay} | PMD: {lfo.pitch_mod_depth} | PMS: {lfo.pitch_mod_sens}"
        )

        self.update("\n".join(lines))


class BankListDisplay(Static):
    """Displays the list of 32 bank slots."""

    def update_bank(self, bank: DX7Bank, current_slot: int) -> None:
        lines = ["[bold magenta]32-Voice Bank Memory[/bold magenta]"]
        for i in range(1, 33):
            p = bank[i]
            prefix = "▶ " if i == current_slot else "  "
            lines.append(f"{prefix}{i:02d}: {p.name.strip()} (Alg {p.algorithm})")
        self.update("\n".join(lines))


class DXPatchGenTUI(App):
    """Textual TUI for DXPatchGen."""

    CSS = """
    Screen {
        layout: vertical;
        background: $surface;
    }

    #main-container {
        layout: horizontal;
        height: 1fr;
    }

    #left-panel {
        width: 32;
        padding: 1;
        background: $panel;
        border-right: solid $primary;
    }

    #center-panel {
        width: 1fr;
        padding: 1;
    }

    #right-panel {
        width: 30;
        padding: 1;
        background: $panel;
        border-left: solid $primary;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .btn {
        width: 100%;
        margin-bottom: 1;
    }

    #status-bar {
        height: 3;
        background: $primary-darken-2;
        color: $text;
        padding: 0 1;
        content-align: left middle;
    }

    #patch-name-input {
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("space", "regenerate", "Regenerate"),
        ("p", "preview", "Preview Audio"),
        ("m", "mutate", "Mutate"),
        ("s", "save_syx", "Save .syx"),
        ("b", "add_to_bank", "Add to Bank"),
        ("e", "export_bank", "Export Bank"),
        ("q", "quit", "Quit"),
    ]

    current_patch: reactive[Optional[DX7Patch]] = reactive(None)
    current_category: reactive[str] = reactive("keys")
    current_profile: reactive[Optional[str]] = reactive(None)
    current_slot: reactive[int] = reactive(1)

    def __init__(self) -> None:
        super().__init__()
        self.bank = DX7Bank()
        self.categories = [
            ("Keys / Electric Piano", "keys"),
            ("Bass", "bass"),
            ("Lush Pad", "pad"),
            ("FM Drum / Percussive", "percussive"),
            ("Lead Synth", "lead"),
            ("Crystal Bell", "bell"),
            ("Sci-Fi / FX", "fx"),
            ("Constrained Random", "constrained"),
            ("Pure Stochastic", "random"),
        ]
        self.profiles = [
            ("Profile: Neutral", "none"),
            ("Profile: Warm & Analog", "warm"),
            ("Profile: Atonal / Metallic", "atonal"),
            ("Profile: Crisp & Glassy", "crisp"),
            ("Profile: Gritty & Driven", "gritty"),
            ("Profile: Ethereal & Space", "ethereal"),
        ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            # Left panel: Controls & parameters
            with Vertical(id="left-panel"):
                yield Label("Category", classes="section-title")
                yield Select(
                    [(label, val) for label, val in self.categories],
                    value="keys",
                    id="category-select",
                    allow_blank=False,
                )
                yield Label("Sonic Profile", classes="section-title")
                yield Select(
                    [(label, val) for label, val in self.profiles],
                    value="none",
                    id="profile-select",
                    allow_blank=False,
                )
                yield Button("🎲 Generate (Space)", id="btn-generate", variant="primary", classes="btn")
                yield Button("▶ Preview Sound (P)", id="btn-preview", variant="default", classes="btn")
                yield Button("🧬 Mutate (M)", id="btn-mutate", variant="warning", classes="btn")
                yield Button("💾 Save Patch .syx (S)", id="btn-save-patch", variant="success", classes="btn")
                yield Button("📥 Add to Bank (B)", id="btn-add-bank", classes="btn")
                yield Button("📦 Export Bank .syx (E)", id="btn-export-bank", variant="success", classes="btn")

            # Center panel: Patch visualization
            with Vertical(id="center-panel"):
                yield Label("Voice Name:")
                yield Input(value="INIT VOICE", id="patch-name-input", max_length=10)
                with Horizontal():
                    yield AlgorithmDisplay(id="alg-display")
                yield OperatorsDisplay(id="ops-display")

            # Right panel: Bank overview
            with ScrollableContainer(id="right-panel"):
                yield BankListDisplay(id="bank-display")

        yield Static("Ready. Press [Space] to generate or [P] to audition sound.", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self.action_regenerate(play_audio=False)

    def action_regenerate(self, play_audio: bool = True) -> None:
        """Generate a new patch with current settings."""
        cat = self.current_category
        prof = self.current_profile if self.current_profile and self.current_profile != "none" else None
        gen = get_generator(cat)
        patch = gen.generate(GenerationOptions(category=cat, profile=prof))
        self.current_patch = patch
        self._refresh_ui()
        prof_tag = f" ({prof.upper()})" if prof else ""
        self._set_status(f"Generated new {cat.upper()}{prof_tag} patch: '{patch.name.strip()}' (Alg {patch.algorithm})")
        if play_audio:
            self.action_preview()

    def action_preview(self) -> None:
        """Audition current patch via built-in FM audio synthesizer."""
        if not self.current_patch:
            return
        AudioPlayer.play_patch_async(self.current_patch, mode="arpeggio")
        self._set_status(f"▶ Playing sound preview for '{self.current_patch.name.strip()}'...")

    def action_mutate(self) -> None:
        """Mutate current patch."""
        if not self.current_patch:
            return
        mutated = PatchMutator.mutate(self.current_patch, mutation_rate=0.2)
        self.current_patch = mutated
        self._refresh_ui()
        self._set_status(f"Mutated patch to: '{mutated.name.strip()}'")
        self.action_preview()

    def action_save_syx(self) -> None:
        """Save current patch in standard 32-voice bank format (Dexed-compatible)."""
        if not self.current_patch:
            return
        clean_name = "".join(c for c in self.current_patch.name.strip() if c.isalnum() or c in ("-", "_")).lower()
        if not clean_name:
            clean_name = "dx7_patch"
        filename = f"{clean_name}.syx"
        out_path = Path.cwd() / filename
        bank = DX7Bank()
        bank[1] = self.current_patch
        bank.save(out_path)
        self._set_status(f"Saved to [bold green]{filename}[/bold green] (4,104 bytes, Dexed-compatible bank)")

    def action_add_to_bank(self) -> None:
        """Add current patch to current bank slot."""
        if not self.current_patch:
            return
        slot = self.current_slot
        self.bank[slot] = self.current_patch
        self._set_status(f"Added '{self.current_patch.name.strip()}' to Bank Slot {slot:02d}")
        self.current_slot = (slot % 32) + 1
        bank_disp = self.query_one(BankListDisplay)
        bank_disp.update_bank(self.bank, self.current_slot)

    def action_export_bank(self) -> None:
        """Export bank to bank.syx."""
        out_path = Path.cwd() / "dx7_bank.syx"
        self.bank.save(out_path)
        self._set_status("Exported 32-voice bank to [bold green]dx7_bank.syx[/bold green] (4104 bytes)")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate":
            self.action_regenerate()
        elif event.button.id == "btn-preview":
            self.action_preview()
        elif event.button.id == "btn-mutate":
            self.action_mutate()
        elif event.button.id == "btn-save-patch":
            self.action_save_syx()
        elif event.button.id == "btn-add-bank":
            self.action_add_to_bank()
        elif event.button.id == "btn-export-bank":
            self.action_export_bank()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "category-select" and event.value:
            self.current_category = str(event.value)
        elif event.select.id == "profile-select":
            self.current_profile = str(event.value) if event.value != "none" else None

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "patch-name-input" and self.current_patch:
            self.current_patch.name = DX7Patch.sanitize_name(event.value)

    def _refresh_ui(self) -> None:
        if not self.current_patch:
            return
        try:
            name_input = self.query_one("#patch-name-input", Input)
            name_input.value = self.current_patch.name.strip()

            alg_disp = self.query_one(AlgorithmDisplay)
            alg_disp.update_patch(self.current_patch)

            ops_disp = self.query_one(OperatorsDisplay)
            ops_disp.update_patch(self.current_patch)

            bank_disp = self.query_one(BankListDisplay)
            bank_disp.update_bank(self.bank, self.current_slot)
        except Exception:
            pass

    def _set_status(self, msg: str) -> None:
        try:
            status = self.query_one("#status-bar", Static)
            status.update(msg)
        except Exception:
            pass


def launch_tui() -> None:
    """Launch the interactive Textual TUI app."""
    app = DXPatchGenTUI()
    app.run()
