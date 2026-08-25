import logging
from typing import Optional

import docker

from app.core.config import settings

logger = logging.getLogger(__name__)


class DockerEngine:
    """
    Singleton Docker daemon connection manager.
    Supports Windows Named Pipes, Linux Unix Sockets, and TCP endpoints.
    """

    _instance: Optional["DockerEngine"] = None
    _client: Optional[docker.DockerClient] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_client(self) -> Optional[docker.DockerClient]:
        """Return a live Docker client, attempting reconnection if needed."""
        if self._client is not None:
            try:
                self._client.ping()
                return self._client
            except Exception:
                logger.warning("Docker client connection lost — attempting reconnect.")
                self._client = None

        candidate_urls = [
            settings.DOCKER_BASE_URL if settings.DOCKER_BASE_URL else None,
            "npipe:////./pipe/docker_engine",          # Windows Docker Desktop
            "npipe:////./pipe/dockerDesktopLinuxEngine",  # Docker Desktop WSL2
            "unix:///var/run/docker.sock",              # Linux / macOS
            None,                                       # from_env() fallback
        ]

        for url in candidate_urls:
            try:
                client = docker.DockerClient(base_url=url) if url else docker.from_env()
                client.ping()
                self._client = client
                logger.info(f"Docker connected via: {url or 'environment default'}")
                return self._client
            except Exception as exc:
                logger.debug(f"Docker probe failed for '{url}': {exc}")

        logger.error("Unable to connect to Docker daemon via any transport.")
        return None

    def is_available(self) -> bool:
        return self.get_client() is not None


docker_engine = DockerEngine()
