from airwrite.trajectory.mapping import RelativeMotionMapper


def test_relative_motion_mapper_initializes_cursor_at_canvas_center() -> None:
    mapper = RelativeMotionMapper()

    point = mapper.update(
        tip_x=0.50,
        tip_y=0.50,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
    )

    assert point == (500.0, 250.0)


def test_relative_motion_mapper_accumulates_tip_deltas_instead_of_absolute_position() -> None:
    mapper = RelativeMotionMapper()
    mapper.update(
        tip_x=0.50,
        tip_y=0.50,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
    )

    point = mapper.update(
        tip_x=0.55,
        tip_y=0.45,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
    )

    assert point == (550.0, 225.0)


def test_relative_motion_mapper_hover_reanchors_without_moving_cursor() -> None:
    mapper = RelativeMotionMapper()
    mapper.update(
        tip_x=0.50,
        tip_y=0.50,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
    )
    mapper.hover(tip_x=0.90, tip_y=0.10)

    point = mapper.update(
        tip_x=0.90,
        tip_y=0.10,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
    )

    assert point == (500.0, 250.0)


def test_relative_motion_mapper_clamps_cursor_to_canvas_bounds() -> None:
    mapper = RelativeMotionMapper()
    mapper.update(
        tip_x=0.50,
        tip_y=0.50,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
    )

    point = mapper.update(
        tip_x=2.0,
        tip_y=-1.0,
        image_width=200.0,
        image_height=100.0,
        canvas_width=1000.0,
        canvas_height=500.0,
    )

    assert point == (1000.0, 0.0)
