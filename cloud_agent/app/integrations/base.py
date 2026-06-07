import logging
from typing import Any


class IntegrationClient:
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)

    async def send(self, payload: dict[str, Any]) -> None:
        raise NotImplementedError
