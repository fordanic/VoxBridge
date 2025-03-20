import httpx
import backoff
from typing import Any, Dict
import asyncio

class ServiceClient:
    def __init__(self, service_name: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.get("timeout", 10))

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, asyncio.TimeoutError),
        max_tries=3
    )
    async def request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"http://{self.config['host']}:{self.config['port']}{endpoint}"
        async with self.client as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> Dict[str, Any]:
        return await self.request("GET", "/health")