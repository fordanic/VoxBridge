from abc import ABC, abstractmethod
import signal
import time
from typing import Dict, Any
import logging
import logging.handlers
import os
from pathlib import Path
import yaml

class BaseService(ABC):
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.running = False
        self.config = self.load_config()  # Load config first
        self.setup_logging()  # Then set up logging
        self.logger = logging.getLogger(f"voxbridge.{service_name}")
        self.logger.info(f"Initializing {service_name} service")  # Add startup message
        self.setup_signal_handlers()

    def setup_logging(self) -> None:
        log_dir = Path(self.config.get('log_path', '/var/log/voxbridge'))
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{self.service_name}.log"
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        logger = logging.getLogger(f"voxbridge.{self.service_name}")
        logger.addHandler(handler)
        logger.setLevel(self.config.get('log_level', 'INFO'))

    def load_config(self) -> Dict[Any, Any]:
        env = os.getenv("VOXBRIDGE_ENV", "development")
        config_path = f"config/{env}.yaml"
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    def setup_signal_handlers(self) -> None:
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum: int, frame: Any) -> None:
        self.logger.info(f"Received shutdown signal {signum}")
        self.running = False
        self.cleanup()

    @abstractmethod
    def cleanup(self) -> None:
        """Implement service-specific cleanup logic"""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Implement service-specific health check"""
        pass

    def start(self) -> None:
        self.running = True
        self.logger.info(f"Starting {self.service_name} service")
        try:
            while self.running:
                self._run_service_loop()
                time.sleep(0.1)  # Prevent CPU spinning
        except Exception as e:
            self.logger.error(f"Service error: {e}", exc_info=True)  # Add exc_info=True for traceback
            self.running = False
        finally:
            self.cleanup()

    @abstractmethod
    def _run_service_loop(self) -> None:
        """Implement main service loop logic"""
        pass
