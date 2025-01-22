from app.api.routes import app
from app.utils.logging_config import setup_logging

# Setup logging
logger = setup_logging()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting File Concatenator service")
    uvicorn.run(app, host="0.0.0.0", port=8000)
