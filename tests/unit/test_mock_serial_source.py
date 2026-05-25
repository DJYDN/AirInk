from airwrite.devices.mock_serial_source import MockSerialSource


def test_mock_serial_source_reads_supplied_messages():
    source = MockSerialSource(messages=[b'{"imu": [0, 0, 1]}'])

    assert source.read() == b'{"imu": [0, 0, 1]}'
