from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Any


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
        async def health_check() -> JSONResponse:
            try:
                health_status = self.service.health_check()
                return JSONResponse(content=health_status)
            except Exception as e:
                raise HTTPException(status_code=503, detail=str(e))

        @self.app.get("/metrics")
        async def metrics() -> JSONResponse:
            # Implement Prometheus metrics
            return JSONResponse(content={
                "service_name": self.service.service_name,
                "status": "running",
            })
