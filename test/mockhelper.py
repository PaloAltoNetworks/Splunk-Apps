"""
This module implements a class that mocks the Splunk "helper" class.
"""

from typing import Optional, Dict, Any
import io
import os
import json
import logging
import requests


class MockHelper:
    """
    Class to mock the Splunk helper class.
    """

    @staticmethod
    def _load_json(path: str) -> Dict[Any, Any]:
        """
        Load a dict from a file in JSON format.
        """
        try:
            with io.open(path, mode="r", encoding="utf-8") as file_descriptor:
                return json.loads(file_descriptor.read())
        except FileNotFoundError:
            return {}


    @staticmethod
    def _save_json(path: str, data: Dict[Any, Any]):
        """
        Writes a dict into a file in JSON format.
        """
        with io.open(path, mode="w", encoding="utf-8") as file_descriptor:
            json.dump(data, file_descriptor)

    def __init__(self, db_file: Optional[str] = None):  # pylint: disable=E1136
        """
        Class initialization.
        """
        self._db_file = db_file
        self._logger = logging.getLogger("splunk_mock_helper")
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(self._logger.getEffectiveLevel())
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
        )
        self._console_handler.setFormatter(formatter)
        self._logger.addHandler(self._console_handler)
        self._db: Dict[Any, Any]
        if self._db_file:
            self._db = MockHelper._load_json(self._db_file)
            if self._db is None:
                raise RuntimeError(f"Unable to load db file: {self._db_file}")

    def get_input_stanza_names(self) -> Any:
        # Mock Input Stanza Name
        source = "testsource"
        return source

    def get_output_index(self) -> Any:
        index = "main"
        return index

    def get_check_point(self, key: str) -> Any:
        """
        Reads data from the DB key/value store.
        """
        return 1

    def save_check_point(self, key: str, value: Any):
        """
        Saves a key into the DB key/value store.
        """
        return 1

    def new_event(self, host: str, source: str, index: str, sourcetype: str, data: Dict[Any, Any]):
        print("New Event")

    def delete_check_point(self, key: str):
        """
        Deletes a key from the DB key/value store if present.
        """
        if key in self._db:
            self._db.pop(key, None)
            if self._db_file:
                MockHelper._save_json(self._db_file, self._db)

    def get_arg(self, key: str) -> Any:  # pylint: disable=R0201
        """
        Returns an environment variable value.
        """
        return os.environ.get(key)

    def get_proxy(self) -> Dict[str, Any]:  # pylint: disable=R0201
        """
        Mocks proxy functionality, always returns a dict with False.
        """
        return {"proxy_enabled": False}

    def set_log_level(self, log_level: Any):
        """
        Sets the log level to the internal logger.
        """
        self._logger.setLevel(log_level)
        self._console_handler.setLevel(log_level)

    def get_log_level(self) -> Any:
        """
        Returns the log level from the internal logger.
        """
        return self._logger.getEffectiveLevel()

    def log_debug(self, message: str):
        """
        Logs debug data.
        """
        self._logger.debug(message)

    def send_http_request(  # pylint: disable=R0201
        self, method: str, url: str, **kwargs
    ) -> Any:
        """
        Wraps around a request call
        """
        kwargs.pop("use_proxy", None)
        kwargs.pop("payload", None)
        parameters = kwargs.pop("parameters", {})
        return requests.request(method=method, url=url, json=parameters, **kwargs)
