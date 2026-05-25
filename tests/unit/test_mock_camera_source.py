from airwrite.devices.mock_camera_source import MockCameraSource


def test_mock_camera_source_yields_requested_zero_frames():
    source = MockCameraSource(frame_size=(640, 480), frame_count=3)

    frames = list(source.frames())

    assert len(frames) == 3
    assert all(frame.data.shape == (480, 640, 3) for frame in frames)
    assert all(frame.data[0, 0, 0] == 0 for frame in frames)
    assert all(frame.data.sum() == 0 for frame in frames)
