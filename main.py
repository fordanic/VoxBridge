#!/usr/bin/env python3
import os
import yaml
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("voxbridge")

def load_config():
    """Load configuration from config.yaml file"""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return {}

def main():
    """Main entry point for VoxBridge"""
    logger.info("VoxBridge is starting")

    # Load configuration
    config = load_config()
    if not config:
        logger.warning("Using default configuration")

    # Get service name from environment (useful in Docker context)
    service_name = os.environ.get("SERVICE_NAME", "main")
    logger.info(f"Running as service: {service_name}")

    # This is just a placeholder. In a real implementation,
    # we would initialize the appropriate service based on service_name.
    logger.info(f"VoxBridge {service_name} service initialized")

if __name__ == "__main__":
    main()
