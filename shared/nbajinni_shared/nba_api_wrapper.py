from nbajinni_shared.logging import get_logger
import requests
import time

class NbaApiWrapper:
    def __init__(self, throttle_delay=1.0):
        self.throttle_delay = throttle_delay
        self.logger = get_logger("nba_api_wrapper")

    def call(self, endpoint):
        retries = 3
        attempts = 0
        error_message = ""
        while attempts < retries:
            try:
                data_frame = endpoint.get_data_frames()[0]
                self.logger.info("fetch_successful", endpoint=type(endpoint).__name__)
                return data_frame
            except requests.exceptions.RequestException as e:
                error_message = str(e)
                self.logger.warning("fetch_failed", endpoint=type(endpoint).__name__, attempt=attempts + 1, error=error_message)
                time.sleep(self.throttle_delay)
                attempts += 1
        
        self.logger.error("retries_exhausted", endpoint=type(endpoint).__name__, error=error_message)
        return None