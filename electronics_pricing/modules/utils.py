"""
Utility functions for the pricing optimization system.
"""
import logging
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with consistent configuration."""
    return logging.getLogger(name)


def set_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    logging.getLogger(__name__).info(f"Random seed set to {seed}")


def create_output_dir(path: str) -> Path:
    """Create output directory if it doesn't exist."""
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def safe_log(values: np.ndarray, offset: float = 1.0) -> np.ndarray:
    """Safely compute log of values add offset to avoid log(0)."""
    return np.log(values + offset)


def safe_exp(values: np.ndarray, offset: float = 1.0) -> np.ndarray:
    """Safely compute exp of log-transformed values."""
    return np.exp(values) - offset
