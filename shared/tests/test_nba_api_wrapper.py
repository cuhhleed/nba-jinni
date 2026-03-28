from unittest.mock import MagicMock
from unittest.mock import patch
import requests
from nbajinni_shared.nba_api_wrapper import NbaApiWrapper

def test_successful_call():
    # Arrange — set up your fake objects
    fake_endpoint = MagicMock()
    fake_endpoint.get_data_frames.return_value = [MagicMock()]
    wrapper = NbaApiWrapper()

    # Act — call the thing you're testing
    result = wrapper.call(fake_endpoint)

    # Assert — verify the outcome
    assert result

@patch("time.sleep")
def test_retry_exhaustion(mock_sleep):
    mock_endpoint = MagicMock()
    mock_endpoint.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        requests.exceptions.RequestException("timeout"),
        requests.exceptions.RequestException("timeout")
    ]
    wrapper = NbaApiWrapper()

    result = wrapper.call(mock_endpoint)

    assert result is None
    assert mock_sleep.call_count == 3
    mock_sleep.assert_called_with(1.0)

@patch("time.sleep")
def test_first_retry_successful(mock_sleep):
    mock_endpoint = MagicMock()
    mock_endpoint.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper()

    result = wrapper.call(mock_endpoint)

    assert result
    assert mock_sleep.call_count == 1


@patch("time.sleep")
def test_second_retry_successful(mock_sleep):
    mock_endpoint = MagicMock()
    mock_endpoint.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper()

    result = wrapper.call(mock_endpoint)

    assert result
    assert mock_sleep.call_count == 2

@patch("time.sleep")
def test_default_throttle_on_retry(mock_sleep):
    mock_endpoint = MagicMock()
    mock_endpoint.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper()

    result = wrapper.call(mock_endpoint)

    mock_sleep.assert_called_once_with(1.0)

@patch("time.sleep")
def test_custom_throttle_on_retry(mock_sleep):
    mock_endpoint = MagicMock()
    mock_endpoint.get_data_frames.side_effect = [
        requests.exceptions.RequestException("timeout"),
        [MagicMock()]
    ]

    wrapper = NbaApiWrapper(throttle_delay=2.0)

    result = wrapper.call(mock_endpoint)

    mock_sleep.assert_called_once_with(2.0)