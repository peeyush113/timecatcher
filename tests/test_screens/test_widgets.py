import pytest
from timetracker.models import TimerStatus


async def test_timer_display_renders():
    from textual.app import App, ComposeResult
    from timetracker.widgets.timer_display import TimerDisplay

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield TimerDisplay()

    app = TestApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.pause(0.1)
        widget = app.query_one(TimerDisplay)
        assert widget is not None
        assert widget.seconds == 25 * 60


async def test_timer_display_updates_seconds():
    from textual.app import App, ComposeResult
    from timetracker.widgets.timer_display import TimerDisplay

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield TimerDisplay()

    app = TestApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.pause(0.1)
        widget = app.query_one(TimerDisplay)
        widget.seconds = 300
        await pilot.pause(0.1)
        from textual.widgets import Label
        label = app.query_one("#timer-time", Label)
        assert "05:00" in str(label.content)


async def test_focus_sparkline_renders():
    from textual.app import App, ComposeResult
    from timetracker.widgets.sparkline import FocusSparkline

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield FocusSparkline(scores=[3.0, 4.0, 5.0])

    app = TestApp()
    async with app.run_test(headless=True) as pilot:
        await pilot.pause(0.1)
        widget = app.query_one(FocusSparkline)
        assert widget is not None
