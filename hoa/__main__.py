"""
Main entry point for HOA application.
"""

import logging

import uvicorn

from hoa.app import create_app
from hoa.config import get_settings


def main():
    """Main entry point."""
    # Load settings
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting HOA authentication server")
    logger.info("Environment: %s", settings.environment)
    logger.info("Database: %s", settings.database_url)
    logger.info("JWT Algorithm: %s", settings.jwt_algorithm)

    # Create app
    app = create_app()

    # Run uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()

