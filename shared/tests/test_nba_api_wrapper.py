from unittest.mock import MagicMock
from unittest.mock import patch
import requests
from nbajinni_shared.nba_api_wrapper import NbaApiWrapper

def test_successful_call():
    # Arrange — set up your fake objects
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.return_value = [MagicMock()]
    wrapper = NbaApiWrapper()

    # Act — call the thing you're testing
    result = wrapper.call(MockEndpointClass)

    # Assert — verify the outcome
    assert result

@patch("time.sleep")
def test_retry_exhaustion(mock_sleep):
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        requests.exceptions.RequestException("timeout"),
        requests.exceptions.RequestException("timeout")
    ]
    wrapper = NbaApiWrapper()

    result = wrapper.call(MockEndpointClass)

    assert result is None
    assert mock_sleep.call_count == 3
    mock_sleep.assert_called_with(1.0)

@patch("time.sleep")
def test_first_retry_successful(mock_sleep):
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper()

    result = wrapper.call(MockEndpointClass)

    assert result
    assert mock_sleep.call_count == 1


@patch("time.sleep")
def test_second_retry_successful(mock_sleep):
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper()

    result = wrapper.call(MockEndpointClass)

    assert result
    assert mock_sleep.call_count == 2

@patch("time.sleep")
def test_default_throttle_on_retry(mock_sleep):
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper()

    result = wrapper.call(MockEndpointClass)

    mock_sleep.assert_called_once_with(1.0)

@patch("time.sleep")
def test_custom_throttle_on_retry(mock_sleep):
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper(back_off_throttle=2.0)

    result = wrapper.call(MockEndpointClass)

    mock_sleep.assert_called_once_with(2.0)

@patch("time.sleep")
def test_call_count_throttle(mock_sleep):
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.return_value = [MagicMock()]

    wrapper = NbaApiWrapper(call_count_throttle=5.0)

    for _ in range(10):
        wrapper.call(MockEndpointClass)

    mock_sleep.assert_called_once_with(5.0)

@patch("time.sleep")
def test_reconfigure_applies_new_throttles_to_subsequent_calls(mock_sleep):
    MockEndpointClass = MagicMock()
    MockEndpointClass.__name__ = "MockEndpoint"
    MockEndpointClass.return_value.get_data_frames.side_effect = [
        [MagicMock()],
        requests.exceptions.RequestException("timeout"),
        [MagicMock()],
        *[[MagicMock()] for _ in range(8)],
    ]

    wrapper = NbaApiWrapper(back_off_throttle=1.0, call_count_throttle=1.0)

    wrapper.call(MockEndpointClass)
    assert mock_sleep.call_count == 0

    wrapper.reconfigure(back_off_throttle=5.0, call_count_throttle=7.0)

    wrapper.call(MockEndpointClass)
    mock_sleep.assert_called_with(5.0)

    for _ in range(8):
        wrapper.call(MockEndpointClass)

    mock_sleep.assert_called_with(7.0)
    assert wrapper.call_count == 10