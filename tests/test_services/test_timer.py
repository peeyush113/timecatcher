import pytest
from timetracker.services.timer import PomodoroService, PomodoroConfig
from timetracker.models import TimerStatus, SessionType


@pytest.fixture
def svc():
    cfg = PomodoroConfig(work_duration=10, short_break=3, long_break=6, pomodoros_per_set=4)
    return PomodoroService(config=cfg)


def test_initial_state_is_idle(svc):
    assert svc.state.status == TimerStatus.IDLE


def test_begin_intent_transitions_to_intent(svc):
    svc.begin_intent(goal_id=1)
    assert svc.state.status == TimerStatus.INTENT
    assert svc.state.goal_id == 1


def test_start_transitions_to_running(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="Write tests")
    assert svc.state.status == TimerStatus.RUNNING
    assert svc.state.seconds_remaining == 10
    assert svc.state.intent == "Write tests"


def test_pause_and_resume(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    svc.pause()
    assert svc.state.status == TimerStatus.PAUSED
    svc.resume()
    assert svc.state.status == TimerStatus.RUNNING


def test_tick_decrements_seconds(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    finished = svc.tick()
    assert svc.state.seconds_remaining == 9
    assert finished is False


def test_tick_to_zero_triggers_reflection(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    for _ in range(10):
        svc.tick()
    assert svc.state.status == TimerStatus.REFLECTION
    assert svc.state.seconds_remaining == 0


def test_reflection_moves_to_short_break(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    for _ in range(10):
        svc.tick()
    break_type = svc.submit_reflection(reflection="done", focus_score=4)
    assert break_type == SessionType.SHORT_BREAK
    assert svc.state.status == TimerStatus.BREAK
    assert svc.state.seconds_remaining == 3


def test_abandon_resets_to_idle(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    svc.abandon()
    assert svc.state.status == TimerStatus.IDLE
    assert svc.state.goal_id is None


def test_skip_break(svc):
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    for _ in range(10):
        svc.tick()
    svc.submit_reflection("done", 4)
    svc.skip_break()
    assert svc.state.status == TimerStatus.RUNNING
    assert svc.state.seconds_remaining == 10


def test_subscriber_notified_on_state_change(svc):
    events = []
    svc.subscribe(lambda s: events.append(s.status))
    svc.begin_intent(goal_id=1)
    svc.start(intent="x")
    assert TimerStatus.INTENT in events
    assert TimerStatus.RUNNING in events


def test_begin_intent_raises_if_not_idle(svc):
    svc.begin_intent(goal_id=1)
    with pytest.raises(ValueError):
        svc.begin_intent(goal_id=2)


def test_fourth_pomodoro_gives_long_break(svc):
    # Complete 3 pomodoros + short breaks, then 4th should give long break
    for i in range(3):
        if svc.state.status == TimerStatus.IDLE:
            svc.begin_intent(goal_id=1)
        svc.start(intent="x")
        for _ in range(10):
            svc.tick()
        svc.submit_reflection("done", 3)  # moves to BREAK
        for _ in range(3):
            svc.tick()  # exhaust short break -> moves to INTENT

    # Now on pomodoro_number=4
    assert svc.state.status == TimerStatus.INTENT
    svc.start(intent="last")
    for _ in range(10):
        svc.tick()
    break_type = svc.submit_reflection("done", 5)
    assert break_type == SessionType.LONG_BREAK
    assert svc.state.seconds_remaining == 6
