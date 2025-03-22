#!/usr/bin/env python3
import logging
import os
from pathlib import Path

import yaml

from src.stt.server import BaseSTT, DummySTT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("voxbridge")


def load_config():
    """Load configuration from the appropriate YAML file"""
    env = os.getenv("VOXBRIDGE_ENV", "development")
    config_path = Path(f"config/{env}.yaml")

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        return {}


def create_stt_engine(config: dict) -> BaseSTT:
    """
    Create and return an STT engine based on configuration.
    Falls back to DummySTT if no engine is configured or if configured engine fails.
    """
    engine_name = config.get("stt", {}).get("engine")

    if not engine_name or engine_name == "placeholder":
        logger.warning("No STT engine configured, falling back to DummySTT")
        return DummySTT()

    # Here we'll add support for other engines (Google, Vosk, Whisper)
    # For now, just return DummySTT
    logger.warning(
        f"STT engine '{engine_name}' not implemented yet, using DummySTT")
    return DummySTT()


def main():
    """Main entry point for VoxBridge"""
    logger.info("VoxBridge is starting")

    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration, exiting")
        return

    # Get service name from environment (useful in Docker context)
    service_name = os.environ.get("SERVICE_NAME", "main")
    logger.info(f"Running as service: {service_name}")

    if service_name == "stt":
        # Initialize STT service
        stt_engine = create_stt_engine(config)
        logger.info(f"Initialized STT engine: {stt_engine.__class__.__name__}")
        stt_engine.start()  # This will run the service loop
    else:
        logger.info(f"Service {service_name} not handled by this instance")


if __name__ == "__main__":
    main()
