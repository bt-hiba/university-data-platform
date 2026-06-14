import os
from typing import Any, Dict, List, Optional

from ingestion.api.api_connector import APIConnector
from utils.logger import setup_logger


log = setup_logger("openalex_connector")

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_DEFAULT_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "configs", "sources.yaml")


class OpenAlexConnector:
    """
    Source-specific connector for fetching publication data from OpenAlex.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        source_name: str = "openalex"
    ):
        self.source_name = source_name
        self.api_connector = APIConnector(
            config_path=config_path or _DEFAULT_CONFIG_PATH,
            source_name=source_name
        )

        self.source_config = self.api_connector.config
        self.source_system = self.source_config.get("source_system", source_name)

    def fetch_publications(self) -> List[Dict[str, Any]]:
        log.info(f"Starting publication fetch | source={self.source_system}")

        publications = self.api_connector.fetch_paginated()

        log.info(
            f"Completed publication fetch | "
            f"source={self.source_system} | record_count={len(publications)}"
        )

        return publications