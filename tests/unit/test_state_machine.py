from airwrite.interaction.state_machine import DrawingState, DrawingStateMachine


def test_state_machine_enters_hover_and_drawing_based_on_pinch_state() -> None:
    machine = DrawingStateMachine(lost_frame_limit=2)

    assert machine.state is DrawingState.NO_HAND
    assert machine.on_hand_detected(is_drawing=False) is DrawingState.HOVER
    assert machine.on_hand_detected(is_drawing=True) is DrawingState.DRAWING
    assert machine.on_hand_detected(is_drawing=False) is DrawingState.HOVER


def test_state_machine_transitions_from_lost_to_no_hand_after_limit() -> None:
    machine = DrawingStateMachine(lost_frame_limit=2)

    machine.on_hand_detected(is_drawing=False)

    assert machine.on_no_hand() is DrawingState.LOST
    assert machine.on_no_hand() is DrawingState.NO_HAND


def test_state_machine_recovers_from_lost_when_hand_returns() -> None:
    machine = DrawingStateMachine(lost_frame_limit=2)

    machine.on_hand_detected(is_drawing=True)
    machine.on_no_hand()

    assert machine.state is DrawingState.LOST
    assert machine.on_hand_detected(is_drawing=False) is DrawingState.HOVER


def test_state_machine_with_limit_one_still_enters_lost_before_no_hand() -> None:
    machine = DrawingStateMachine(lost_frame_limit=1)

    machine.on_hand_detected(is_drawing=False)

    assert machine.on_no_hand() is DrawingState.LOST
    assert machine.on_no_hand() is DrawingState.NO_HAND
