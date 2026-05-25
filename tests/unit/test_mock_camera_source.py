from airwrite.devices.camera_source import CameraFrame
from airwrite.devices.mock_camera_source import MockCameraSource


def test_camera_frame_is_not_frozen_when_holding_mutable_frame_data():
    assert CameraFrame.__dataclass_params__.frozen is False


def test_mock_camera_source_yields_requested_zero_frames():
    source = MockCameraSource(frame_size=(640, 480), frame_count=3)

    frames = list(source.frames())

    assert len(frames) == 3
    assert all(frame.data.shape == (480, 640, 3) for frame in frames)
    assert all(frame.data[0, 0, 0] == 0 for frame in frames)
    assert all(frame.data.sum() == 0 for frame in frames)
    assert frames[0].data is not frames[1].data
    frames[0].data[0, 0, 0] = 255
    assert frames[1].data[0, 0, 0] == 0
