import time
from typing import Any, Dict, List, Optional

import requests
import yaml

from utils.logger import log_retry, setup_logger


log = setup_logger("api_connector")


class APIConnector:
    """
    Generic API connector for loading API configuration and executing HTTP GET requests.
    """

    def __init__(self, config_path: str, source_name: str):
        self.config_path = config_path
        self.source_name = source_name
        self.config = self._load_config()

        self.base_url = self.config["base_url"]
        self.endpoint = self.config["endpoint"]
        self.request_config = self.config.get("request", {})
        self.pagination_config = self.config.get("pagination", {})
        self.query_params = self.config.get("query_params", {})

        self.timeout_seconds = self.request_config.get("timeout_seconds", 30)
        self.max_retries = self.request_config.get("max_retries", 3)
        self.retry_backoff_seconds = self.request_config.get(
            "retry_backoff_seconds",
            2
        )

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as config_file:
                all_configs = yaml.safe_load(config_file)

            if not all_configs:
                raise ValueError("Configuration file is empty.")

            if self.source_name not in all_configs:
                raise KeyError(
                    f"Source '{self.source_name}' not found in configuration."
                )

            return all_configs[self.source_name]

        except FileNotFoundError as exc:
            log.error(f"Configuration file not found: {self.config_path}")
            raise exc

        except yaml.YAMLError as exc:
            log.error(f"Invalid YAML configuration: {exc}")
            raise exc

    def build_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/{self.endpoint.lstrip('/')}"

    def get(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self.build_url()
        request_params = params or {}

        for attempt in range(1, self.max_retries + 1):
            try:
                log.info(
                    f"Sending GET request | url={url} | "
                    f"attempt={attempt} | params={request_params}"
                )

                response = requests.get(
                    url,
                    params=request_params,
                    timeout=self.timeout_seconds
                )

                response.raise_for_status()
                return response.json()

            except requests.exceptions.Timeout as exc:
                log.warning(
                    f"Request timeout | attempt={attempt}/{self.max_retries} | url={url}"
                )

                if attempt == self.max_retries:
                    raise exc

            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response else None

                log.warning(
                    f"HTTP error | status_code={status_code} | "
                    f"attempt={attempt}/{self.max_retries} | url={url}"
                )

                if attempt == self.max_retries:
                    raise exc

            except requests.exceptions.RequestException as exc:
                log.warning(
                    f"Request failed | attempt={attempt}/{self.max_retries} | "
                    f"url={url} | error={exc}"
                )

                if attempt == self.max_retries:
                    raise exc

            log_retry(
                log=log,
                source=self.source_name,
                attempt=attempt,
                max_attempts=self.max_retries,
                wait_seconds=self.retry_backoff_seconds
            )

            time.sleep(self.retry_backoff_seconds)

        raise RuntimeError("GET request failed after all retry attempts.")

    def fetch_paginated(self) -> List[Dict[str, Any]]:
        pagination_enabled = self.pagination_config.get("enabled", False)

        if not pagination_enabled:
            response_data = self.get(params=self.query_params)
            return response_data.get("results", [])

        page_param = self.pagination_config.get("page_param", "page")
        per_page_param = self.pagination_config.get("per_page_param", "per-page")
        per_page = self.pagination_config.get("per_page", 100)
        max_pages = self.pagination_config.get("max_pages", 1)

        all_records = []

        for page_number in range(1, max_pages + 1):
            params = {
                **self.query_params,
                page_param: page_number,
                per_page_param: per_page
            }

            log.info(
                f"Fetching page {page_number}/{max_pages} | source={self.source_name}"
            )

            response_data = self.get(params=params)
            records = response_data.get("results", [])

            if not records:
                log.info(f"No records returned for page={page_number}")
                break

            all_records.extend(records)

        log.info(
            f"Fetched {len(all_records)} total records | source={self.source_name}"
        )

        return all_records