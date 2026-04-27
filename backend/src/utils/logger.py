"""
Logging configuration for the AI pipeline — all 6 steps
"""
import logging
import os
from datetime import datetime

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """Setup a logger with file and console handlers"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    log_file = os.path.join(LOGS_DIR, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)

    # Use errors='replace' to prevent UnicodeEncodeError on Windows cp1252
    import sys
    console_handler = logging.StreamHandler(
        open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)
    )
    console_handler.setLevel(logging.WARNING)  # Only warnings+ to console

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ── Step loggers ──
pipeline_logger       = setup_logger("ai_pipeline")         # Orchestrator
text_gen_logger       = setup_logger("text_generation")      # Step 1, 4, 5
image_analysis_logger = setup_logger("image_analysis")       # Step 2
trend_research_logger = setup_logger("trend_research")       # Step 3
image_gen_logger      = setup_logger("image_generation")     # Step 6
