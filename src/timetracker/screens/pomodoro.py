from datetime import datetime
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, RadioSet, RadioButton
from textual.containers import Vertical, Horizontal

from ..models import Goal, TimerStatus
from ..services.timer import PomodoroService
from ..services.sessions import SessionService


class IntentModal(ModalScreen):
    """Pre-session modal: select goal and state your intent."""

    DEFAULT_CSS = """
    IntentModal {
        align: center middle;
    }
    #intent-dialog {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 2 4;
    }
    .modal-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    .field-label {
        color: $text-muted;
        margin-top: 1;
    }
    Button {
        margin-top: 1;
        margin-right: 1;
    }
    """

    def __init__(self, timer_svc: PomodoroService, goals: list[Goal], **kwargs):
        super().__init__(**kwargs)
        self._timer_svc = timer_svc
        self._goals = goals

    def compose(self) -> ComposeResult:
        with Vertical(id="intent-dialog"):
            yield Label("Start a Pomodoro", classes="modal-title")
            yield Label("Goal:", classes="field-label")
            options = [(g.title, str(g.id)) for g in self._goals]
            yield Select(options, id="goal-select", value=str(self._goals[0].id))
            yield Label("What will you work on this session?", classes="field-label")
            yield Input(placeholder="Describe your intent...", id="intent-input")
            with Horizontal():
                yield Button("Start  ▶", variant="success", id="btn-start")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
            return

        goal_select = self.query_one("#goal-select", Select)
        intent_input = self.query_one("#intent-input", Input)

        if not intent_input.value.strip():
            self.notify("Please enter your intent for this session", severity="warning")
            return

        if goal_select.value == Select.BLANK:
            self.notify("Please select a goal", severity="warning")
            return

        goal_id = int(goal_select.value)
        intent = intent_input.value.strip()

        self._timer_svc.begin_intent(goal_id=goal_id)
        self._timer_svc.start(intent=intent)
        self.dismiss({"goal_id": goal_id, "intent": intent})


class ReflectionModal(ModalScreen):
    """Post-session modal: reflection text + focus rating 1-5."""

    DEFAULT_CSS = """
    ReflectionModal {
        align: center middle;
    }
    #reflect-dialog {
        width: 62;
        height: auto;
        max-height: 85%;
        border: thick $success;
        background: $surface;
        padding: 2 4;
    }
    .modal-title {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
    }
    .field-label {
        color: $text-muted;
        margin-top: 1;
    }
    Button {
        margin-top: 1;
        margin-right: 1;
    }
    """

    def __init__(
        self,
        timer_svc: PomodoroService,
        session_svc: SessionService,
        session_id: int | None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._timer_svc = timer_svc
        self._session_svc = session_svc
        self._session_id = session_id

    def compose(self) -> ComposeResult:
        with Vertical(id="reflect-dialog"):
            yield Label("Session Complete! ✓", classes="modal-title")
            yield Label("What did you accomplish?", classes="field-label")
            yield Input(placeholder="Brief reflection...", id="reflection-input")
            yield Label("Focus quality (1 = distracted, 5 = deep focus):", classes="field-label")
            with RadioSet(id="focus-rating"):
                yield RadioButton("★☆☆☆☆  1 — Very distracted")
                yield RadioButton("★★☆☆☆  2 — Somewhat distracted")
                yield RadioButton("★★★☆☆  3 — Decent focus", value=True)
                yield RadioButton("★★★★☆  4 — Good focus")
                yield RadioButton("★★★★★  5 — Deep focus")
            with Horizontal():
                yield Button("Save & Break  ☕", variant="success", id="btn-break")
                yield Button("Save & Finish", variant="primary", id="btn-finish")
                yield Button("Skip", id="btn-skip")

    def _get_focus_score(self) -> int:
        radio_set = self.query_one("#focus-rating", RadioSet)
        idx = radio_set.pressed_index
        return (idx + 1) if idx is not None else 3

    def _save_session(self, reflection: str, score: int) -> None:
        if self._session_id is not None:
            self._session_svc.complete(
                session_id=self._session_id,
                ended_at=datetime.now(),
                actual_duration=self._timer_svc.state.config.work_duration // 60,
                reflection=reflection or None,
                focus_score=score,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        reflection = self.query_one("#reflection-input", Input).value.strip()
        score = self._get_focus_score()

        if event.button.id == "btn-skip":
            self._timer_svc.abandon()
            self.dismiss(None)

        elif event.button.id == "btn-finish":
            self._save_session(reflection, score)
            self._timer_svc.finish()
            self.dismiss({"action": "finish"})

        elif event.button.id == "btn-break":
            self._save_session(reflection, score)
            self._timer_svc.submit_reflection(reflection, score)
            self.dismiss({"action": "break"})
