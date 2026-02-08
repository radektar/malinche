"""Core application orchestrator for Olympus Transcriber."""

import os
import time
import signal
import threading
from pathlib import Path
from typing import Optional

from src.config import config
from src.logger import logger
from src.transcriber import Transcriber
from src.file_monitor import FileMonitor
from src.app_status import AppStatus, AppState


class OlympusTranscriber:
    """Main application orchestrator.

    Manages the lifecycle of the transcriber daemon, coordinating
    FSEvents monitoring, periodic checking, and graceful shutdown.

    Attributes:
        transcriber: Transcription engine instance
        monitor: File system monitor instance
        periodic_thread: Background thread for periodic checks
        running: Flag indicating if application is running
        state: Thread-safe application state
    """

    def __init__(self, setup_signals: bool = True):
        """Initialize the application.
        
        Args:
            setup_signals: Whether to setup signal handlers (only works in main thread)
        """
        self.transcriber: Optional[Transcriber] = None
        self.monitor: Optional[FileMonitor] = None
        self.periodic_thread: Optional[threading.Thread] = None
        self.running = False
        self.state = AppState()

        # Setup signal handlers for graceful shutdown (only in main thread)
        if setup_signals:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        logger.info(f"Received {signal_name}, shutting down...")
        self.stop()

    def _periodic_check(self):
        """Periodic check for recorder (fallback if FSEvents misses event).

        Runs in a background thread, checking every PERIODIC_CHECK_INTERVAL
        seconds for a connected recorder.
        """
        logger.info(
            f"✓ Periodic checker started "
            f"(interval: {config.PERIODIC_CHECK_INTERVAL}s)"
        )

        while self.running:
            try:
                time.sleep(config.PERIODIC_CHECK_INTERVAL)

                if not self.running:
                    break

                # Only check if recorder is not already being monitored
                if self.transcriber and not self.transcriber.recorder_monitoring:
                    recorder = self.transcriber.find_recorder()
                    if recorder:
                        logger.debug("Periodic check triggered processing")
                        self.transcriber.process_recorder()

            except Exception as e:
                logger.error(f"Error in periodic check: {e}", exc_info=True)
                self.state.status = AppStatus.ERROR
                self.state.error_message = str(e)

        logger.info("✓ Periodic checker stopped")

    def start(self):
        """Start the transcriber daemon."""
        logger.info("=" * 60)
        logger.info("🚀 Olympus Transcriber starting...")
        logger.info("=" * 60)

        # Log configuration
        logger.info(f"📂 Transcription directory: {config.TRANSCRIBE_DIR}")
        logger.info(f"📄 State file: {config.STATE_FILE}")
        logger.info(f"📋 Log file: {config.LOG_FILE}")

        # Log TRANSCRIBE_DIR source (from config, which was migrated from ENV if needed)
        logger.info(
            f"ℹ️  TRANSCRIBE_DIR: {config.TRANSCRIBE_DIR} "
            f"(set OLYMPUS_TRANSCRIBE_DIR env var and restart to change)"
        )
        
        # Ensure transcription directory exists
        try:
            config.ensure_directories()
            if config.TRANSCRIBE_DIR.exists():
                logger.info(f"✓ Transcription directory exists: {config.TRANSCRIBE_DIR}")
            else:
                logger.warning(
                    f"⚠️  Transcription directory does not exist and could not be created: "
                    f"{config.TRANSCRIBE_DIR}"
                )
        except Exception as e:
            logger.error(
                f"✗ Failed to create transcription directory: {e}",
                exc_info=True
            )
            logger.error(
                "Please ensure OLYMPUS_TRANSCRIBE_DIR points to a valid, "
                "accessible directory (same vault path on all computers to avoid duplicates)"
            )
            raise
        
        # Diagnostic check: warn if directory doesn't look like a synced vault
        transcribe_path_str = str(config.TRANSCRIBE_DIR)
        if "iCloud" not in transcribe_path_str and "Obsidian" not in transcribe_path_str:
            logger.warning(
                "⚠️  TRANSCRIBE_DIR does not appear to be in a synced location "
                "(iCloud/Obsidian). For multi-computer setups, ensure all instances "
                "point to the same synchronized vault directory to prevent duplicate transcriptions."
            )

        # Initialize transcriber
        try:
            # Create transcriber with injected config for better testability
            self.transcriber = Transcriber(config=config)
            # Inject state updater callback into transcriber
            self.transcriber.set_state_updater(self._update_state)
        except Exception as e:
            logger.error(f"Failed to initialize transcriber: {e}", exc_info=True)
            self.state.status = AppStatus.ERROR
            self.state.error_message = f"Błąd inicjalizacji: {e}"
            raise

        # Initialize file monitor
        self.monitor = FileMonitor(callback=self.transcriber.process_recorder)

        # Start FSEvents monitor
        try:
            self.monitor.start()
        except Exception as e:
            logger.error(f"Failed to start file monitor: {e}")
            logger.warning("Continuing with periodic check only")
            self.state.status = AppStatus.ERROR
            self.state.error_message = f"Błąd monitora plików: {e}"

        # Start periodic checker thread
        self.running = True
        self.state.status = AppStatus.IDLE
        self.periodic_thread = threading.Thread(
            target=self._periodic_check,
            daemon=True,
            name="PeriodicChecker"
        )
        self.periodic_thread.start()

        logger.info("=" * 60)
        logger.info("✓ All monitors running")
        logger.info("⏳ Waiting for recorder connection...")
        logger.info("   (Press Ctrl+C to stop)")
        logger.info("=" * 60)

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            # Already handled by signal handler, but catch here too
            pass

    def stop(self):
        """Stop the transcriber daemon."""
        if not self.running:
            return

        logger.info("⏹  Shutting down...")

        # Stop running flag
        self.running = False
        self.state.status = AppStatus.IDLE

        # Stop file monitor
        if self.monitor:
            try:
                self.monitor.stop()
            except Exception as e:
                logger.error(f"Error stopping monitor: {e}")

        # Wait for periodic thread to finish
        if self.periodic_thread and self.periodic_thread.is_alive():
            logger.debug("Waiting for periodic checker to stop...")
            self.periodic_thread.join(timeout=5.0)

        logger.info("✓ Shutdown complete")
        logger.info("=" * 60)

    def _update_state(
        self,
        status: AppStatus,
        current_file: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Update application state (called by Transcriber).

        Args:
            status: New status
            current_file: Current file being processed (if any)
            error_message: Error message (if status is ERROR)
        """
        self.state.status = status
        self.state.current_file = current_file
        if error_message:
            self.state.error_message = error_message

