import time
import logging
import db

logger = logging.getLogger(__name__)

# In-memory fast version counter initialized to current millisecond timestamp
_CURRENT_STATE_VERSION = int(time.time() * 1000)

def get_state_version():
    """Return the current system state version counter."""
    global _CURRENT_STATE_VERSION
    return _CURRENT_STATE_VERSION

def bump_state_version():
    """
    Increment state version counter to notify all connected clients
    that database state has changed.
    """
    global _CURRENT_STATE_VERSION
    _CURRENT_STATE_VERSION = int(time.time() * 1000)
    logger.debug(f"System state version bumped to: {_CURRENT_STATE_VERSION}")
    return _CURRENT_STATE_VERSION
