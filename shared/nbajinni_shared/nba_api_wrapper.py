import time

import requests
from nbajinni_shared.logging import get_logger


class NbaApiWrapper:
    def __init__(self, back_off_throttle=10.0, call_count_throttle=2.0):
        self.back_off_throttle = back_off_throttle
        self.call_count_throttle = call_count_throttle
        self.logger = get_logger("nba_api_wrapper")
        self.call_count = 0

    def call(self, endpoint_class, **kwargs):
        endpoint_name = endpoint_class.__name__
        self.call_count += 1
        retries = 3
        attempts = 0
        error_message = ""

        if self.call_count % 10 == 0:
            self.logger.info("calls_throttled", endpoint=endpoint_name)
            time.sleep(self.call_count_throttle)

        while attempts < retries:
            try:
                endpoint = endpoint_class(**kwargs)
                data_frames = endpoint.get_data_frames()
                self.logger.info("fetch_successful", endpoint=endpoint_name)
                return data_frames
            except Exception as e:
                error_message = str(e)
                self.logger.warning(
                    "fetch_failed",
                    endpoint=endpoint_name,
                    attempt=attempts + 1,
                    error=error_message,
                )
                time.sleep(self.back_off_throttle)
                attempts += 1

        self.logger.error("retries_exhausted", endpoint=endpoint_name, error=error_message)
        return None
