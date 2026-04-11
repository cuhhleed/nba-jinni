import os
import time
from nbajinni_shared.logging import get_logger


class NbaApiWrapper:
    def __init__(self, back_off_throttle=None, call_count_throttle=None):
        if back_off_throttle is None:
            back_off_throttle = float(os.getenv("NBA_API_BACKOFF_THROTTLE", "1.0"))
        if call_count_throttle is None:
            call_count_throttle = float(os.getenv("NBA_API_CALL_COUNT_THROTTLE", "1.0"))
        self.back_off_throttle = back_off_throttle
        self.call_count_throttle = call_count_throttle
        self.logger = get_logger("nba_api_wrapper")
        self.call_count = 0

    def reconfigure(self, back_off_throttle, call_count_throttle):
        self.back_off_throttle = back_off_throttle
        self.call_count_throttle = call_count_throttle
        self.logger.info(
            "throttles_reconfigured",
            back_off_throttle=self.back_off_throttle,
            call_count_throttle=self.call_count_throttle,
            call_count=self.call_count,
        )

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
                return data_frames
            except Exception as e:
                error_message = str(e)
                self.logger.warning(
                    "fetch_failed",
                    endpoint=endpoint_name,
                    attempt=attempts + 1,
                    error=error_message,
                    arguments=kwargs,
                )
                time.sleep(self.back_off_throttle)
                attempts += 1

        self.logger.error("retries_exhausted", endpoint=endpoint_name, error=error_message, arguments=kwargs)
        return None
