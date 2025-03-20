from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import Any, Dict

class ServiceAPI:
    def __init__(self, service: Any):
        self.app = FastAPI()
        self.service = service
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self) -> None:
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_routes(self) -> None:
        @self.app.get("/health")
        async def health_check() -> Dict[str, Any]:
            try:
                health_status = self.service.health_check()
                return JSONResponse(content=health_status)
            except Exception as e:
                raise HTTPException(status_code=503, detail=str(e))

        @self.app.get("/metrics")
        async def metrics() -> Dict[str, Any]:
            # Implement Prometheus metrics
            pass