"""File system monitoring for Malinche using FSEvents."""

import time
from typing import Callable, Optional
from pathlib import Path

try:
    from fsevents import Observer, Stream
    FSEVENTS_AVAILABLE = True
except ImportError:
    FSEVENTS_AVAILABLE = False

from src.logger import logger
from src.config import config
from src.config.settings import UserSettings
from src.config.defaults import defaults
from src.volume_utils import (
    find_matching_volumes,
    has_audio_files,
    should_process_volume,
)


class FileMonitor:
    """Monitor /Volumes for recorder mount events using FSEvents.
    
    This class uses macOS FSEvents API to efficiently monitor the /Volumes
    directory for changes, watching for any external volume (USB drive, SD card, etc.)
    that contains audio files.
    
    Supports multiple watch modes:
    - "auto": Automatically detect any volume with audio files
    - "specific": Only watch volumes in the watched_volumes list
    - "manual": Don't auto-detect (user selects manually)
    
    Attributes:
        callback: Function to call when recorder activity is detected
        observer: FSEvents Observer instance
        is_monitoring: Flag indicating if monitoring is active
    """
    
    def __init__(self, callback: Callable[[], None]):
        """Initialize the file monitor.
        
        Args:
            callback: Function to call when recorder activity is detected
        """
        if not FSEVENTS_AVAILABLE:
            logger.warning(
                "⚠️  FSEvents not available. Install with: "
                "pip install MacFSEvents"
            )
        
        self.callback = callback
        self.observer: Optional[Observer] = None
        self.is_monitoring = False
        self._last_trigger_time = 0.0
        self._debounce_seconds = 2.0  # Prevent multiple rapid triggers
    
    def start(self) -> None:
        """Start monitoring /Volumes for mount events."""
        if not FSEVENTS_AVAILABLE:
            logger.error("Cannot start FSEvents monitor - library not available")
            return
        
        if self.is_monitoring:
            logger.warning("Monitor already running")
            return
        
        try:
            self.observer = Observer()
            
            def on_change(path, mask):
                """Callback for FSEvents changes."""
                current_time = time.time()
                
                # Debounce: Skip if triggered too recently
                if current_time - self._last_trigger_time < self._debounce_seconds:
                    return
                
                # Ignore internal macOS housekeeping on the recorder volume
                IGNORED_DIRS = {".Spotlight-V100", ".fseventsd", ".Trashes"}
                
                try:
                    path_obj = Path(path)
                except (TypeError, ValueError):
                    # Defensive: if path is not a string-like or invalid, just skip
                    logger.debug(f"Invalid path in FSEvents: {path}")
                    return
                
                # Detect which volume root (if any) this path belongs to
                volume_root: Optional[Path] = None
                
                # Get user settings
                settings = UserSettings.load()
                
                # Check if we should process this volume
                volumes_path = Path("/Volumes")
                for volume_name in volumes_path.iterdir():
                    if not volume_name.is_dir():
                        continue
                    
                    try:
                        path_obj.relative_to(volume_name)
                    except ValueError:
                        continue
                    else:
                        # Found the volume containing this path
                        if self._should_process_volume(volume_name, settings):
                            volume_root = volume_name
                            break
                
                if volume_root is None:
                    # Not a volume we should process
                    return
                
                # Compute relative path inside the volume
                try:
                    relative = path_obj.relative_to(volume_root)
                except ValueError:
                    # Should not happen given the check above, but be safe
                    logger.debug(f"Could not compute relative path for: {path}")
                    return
                
                # If the first component is a macOS system directory, ignore
                parts = relative.parts
                if parts and parts[0] in IGNORED_DIRS:
                    logger.debug(f"Ignoring system directory change: {path}")
                    return
                
                logger.info(f"📢 Detected volume activity: {path}")
                self._last_trigger_time = current_time
                
                # Wait for system to fully mount the volume or finish writes
                time.sleep(config.MOUNT_MONITOR_DELAY)
                
                # Trigger callback
                try:
                    self.callback()
                except Exception as e:
                    logger.error(f"Error in callback: {e}", exc_info=True)
            
            # Create stream watching /Volumes
            stream = Stream(on_change, "/Volumes", file_events=False)
            self.observer.schedule(stream)
            
            self.is_monitoring = True
            self.observer.start()
            
            logger.info("✓ FSEvents monitor started (watching /Volumes)")

            self._initial_scan()

        except Exception as e:
            logger.error(f"Failed to start FSEvents monitor: {e}", exc_info=True)
            self.is_monitoring = False

    def _initial_scan(self) -> None:
        """Trigger callback once if any matching volume is already mounted.

        FSEvents only fires on mount/change events, so recorders plugged in
        BEFORE the daemon started would otherwise be ignored until the user
        unplugs and re-plugs them. This scan closes that gap by checking the
        current contents of ``/Volumes`` right after the observer is up.

        The callback is invoked at most once per start because
        ``Transcriber.process_recorder()`` already iterates over every
        matching volume internally (``find_recorders()``).
        """
        try:
            settings = UserSettings.load()
            matching = find_matching_volumes(settings, volumes_root=Path("/Volumes"))
        except Exception as error:  # noqa: BLE001
            logger.debug(f"Initial volume scan skipped due to error: {error}")
            return

        if not matching:
            logger.info("🔎 Initial scan: no matching volumes already mounted")
            return

        names = ", ".join(volume.name for volume in matching)
        logger.info(
            f"🔎 Initial scan: found {len(matching)} matching volume(s): {names}"
        )

        self._last_trigger_time = time.time()
        try:
            self.callback()
        except Exception as error:  # noqa: BLE001
            logger.error(
                f"Error in callback during initial scan: {error}", exc_info=True
            )
    
    def _should_process_volume(self, volume_path: Path, settings: UserSettings) -> bool:
        """Check if volume should be processed based on watch mode.

        Thin wrapper around :func:`src.volume_utils.should_process_volume` so
        ``Transcriber`` and ``FileMonitor`` share one source of truth.

        Args:
            volume_path: Path to the volume (e.g., /Volumes/SD_CARD)
            settings: UserSettings instance with watch configuration

        Returns:
            True if volume should be processed, False otherwise
        """
        return should_process_volume(volume_path, settings)

    def _has_audio_files(self, path: Path, max_depth: int = None) -> bool:
        """Check if folder contains audio files.

        Thin wrapper around :func:`src.volume_utils.has_audio_files` retained
        for backward compatibility with existing tests.

        Args:
            path: Path to check
            max_depth: Maximum depth to scan (defaults to defaults.MAX_SCAN_DEPTH)

        Returns:
            True if audio files found, False otherwise
        """
        return has_audio_files(path, max_depth=max_depth)
    
    def stop(self) -> None:
        """Stop monitoring."""
        if not self.observer:
            return
        
        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.is_monitoring = False
            logger.info("✓ FSEvents monitor stopped")
        except Exception as e:
            logger.error(f"Error stopping monitor: {e}", exc_info=True)

