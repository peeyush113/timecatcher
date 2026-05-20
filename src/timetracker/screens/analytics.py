from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static


class AnalyticsScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Static("Analytics — coming soon")
