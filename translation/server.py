import logging
import time

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Translation service")
    # This is just a placeholder that keeps the container running
    while True:
        logger.info("Translation service running...")
        time.sleep(60)
