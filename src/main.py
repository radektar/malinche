"""Main entry point for Malinche daemon."""

import sys

from src.env_loader import load_env_file

# Load environment variables before importing config-dependent modules
load_env_file()

# Perform migration BEFORE importing config-dependent modules
# This ensures deterministic configuration and prevents side effects during module import
from src.config.migration import perform_migration_if_needed
from src.config.config import get_config

# Run migration if needed (reads ENV and old config files, saves new config)
perform_migration_if_needed()

# Initialize global config instance after migration
# This ensures config is deterministic and doesn't depend on import order
get_config()

from src.logger import logger
from src.app_core import MalincheTranscriber


def main():
    """Main entry point."""
    try:
        app = MalincheTranscriber()
        app.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()


