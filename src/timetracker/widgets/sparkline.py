from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Sparkline, Label


class FocusSparkline(Widget):
    """Focus score trend over recent sessions."""

    DEFAULT_CSS = """
    FocusSparkline {
        height: 5;
        border: solid $panel;
        padding: 0 1;
    }
    #sparkline-title {
        color: $accent;
        text-style: bold;
    }
    """

    def __init__(self, scores: list[float], **kwargs):
        super().__init__(**kwargs)
        self._scores = scores if scores else [0.0]

    def compose(self) -> ComposeResult:
        avg = sum(self._scores) / len(self._scores) if self._scores else 0
        yield Label(f"Focus trend  avg: {avg:.1f}/5", id="sparkline-title")
        yield Sparkline(self._scores, summary_function=max)
