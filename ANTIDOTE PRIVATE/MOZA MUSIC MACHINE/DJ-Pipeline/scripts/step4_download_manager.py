"""
Step 4: Download Manager
Downloads approved tracks from DJ pool sources and tracks progress.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DownloadRecord:
    """Record of a downloaded track."""
    artist: str
    title: str
    source: str
    file_path: str
    file_size: int
    download_time: str
    checksum: str
    success: bool
    error_message: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class DownloadManager:
    """Manage downloads from DJ pool sources."""

    def __init__(self, approved_tracks_file: str, downloads_dir: str, logs_dir: str):
        """
        Initialize download manager.

        Args:
            approved_tracks_file: Path to approved tracks JSON
            downloads_dir: Base downloads directory
            logs_dir: Directory for download logs
        """
        self.approved_tracks_file = Path(approved_tracks_file)
        self.downloads_dir = Path(downloads_dir)
        self.logs_dir = Path(logs_dir)

        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.approved_tracks = []
        self.download_records = []
        self.failed_downloads = []

        # Import source modules
        from sources import DJCitySource, BeatportSource, BPMSupremeSource, TraxsourceSource, iTunesSource

        self.sources = {
            'djcity': DJCitySource(),
            'beatport': BeatportSource(),
            'bpmsupreme': BPMSupremeSource(),
            'traxsource': TraxsourceSource(),
            'itunes': iTunesSource()
        }

    def load_approved_tracks(self) -> bool:
        """
        Load approved tracks from file.

        Returns:
            True if successful
        """
        try:
            with open(self.approved_tracks_file, 'r', encoding='utf-8') as f:
                self.approved_tracks = json.load(f)
            logger.info(f"Loaded {len(self.approved_tracks)} approved tracks")
            return True
        except Exception as e:
            logger.error(f"Error loading approved tracks: {e}")
            return False

    def calculate_checksum(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Calculate file checksum.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm

        Returns:
            Hex digest of file hash
        """
        hash_obj = hashlib.new(algorithm)
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            logger.warning(f"Error calculating checksum for {file_path}: {e}")
            return ""

    def download_track(self, track: Dict[str, Any]) -> DownloadRecord:
        """
        Download a single track from best available source.

        Args:
            track: Track dictionary with availability info

        Returns:
            DownloadRecord with success/failure info
        """
        artist = track.get('artist', 'Unknown')
        title = track.get('title', 'Unknown')

        # Find best source
        availability = track.get('availability', {})
        original_source = track.get('original_source', '')

        source_name = None
        if availability.get(original_source):
            source_name = original_source
        else:
            for source, available in availability.items():
                if available:
                    source_name = source
                    break

        if not source_name:
            error_msg = "Track not available in any source"
            logger.warning(f"Cannot download {artist} - {title}: {error_msg}")
            return DownloadRecord(
                artist=artist,
                title=title,
                source="none",
                file_path="",
                file_size=0,
                download_time=datetime.now().isoformat(),
                checksum="",
                success=False,
                error_message=error_msg
            )

        try:
            source_instance = self.sources.get(source_name)
            if not source_instance:
                raise ValueError(f"Unknown source: {source_name}")

            logger.info(f"Downloading from {source_name}: {artist} - {title}")

            # Call source download method
            file_path = source_instance.download(
                artist=artist,
                title=title,
                destination=self.downloads_dir / source_name
            )

            if file_path and Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                checksum = self.calculate_checksum(Path(file_path))

                logger.info(f"Downloaded: {file_path} ({file_size} bytes)")

                return DownloadRecord(
                    artist=artist,
                    title=title,
                    source=source_name,
                    file_path=str(file_path),
                    file_size=file_size,
                    download_time=datetime.now().isoformat(),
                    checksum=checksum,
                    success=True
                )
            else:
                error_msg = "Download returned no file path"
                logger.error(error_msg)
                return DownloadRecord(
                    artist=artist,
                    title=title,
                    source=source_name,
                    file_path="",
                    file_size=0,
                    download_time=datetime.now().isoformat(),
                    checksum="",
                    success=False,
                    error_message=error_msg
                )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error downloading {artist} - {title}: {error_msg}")
            return DownloadRecord(
                artist=artist,
                title=title,
                source=source_name or "unknown",
                file_path="",
                file_size=0,
                download_time=datetime.now().isoformat(),
                checksum="",
                success=False,
                error_message=error_msg
            )

    def download_all(self, max_retries: int = 3) -> Dict[str, Any]:
        """
        Download all approved tracks.

        Args:
            max_retries: Number of retry attempts for failed downloads

        Returns:
            Download summary dictionary
        """
        if not self.approved_tracks:
            logger.warning("No approved tracks to download")
            return {}

        logger.info(f"Starting download of {len(self.approved_tracks)} tracks")

        for idx, track in enumerate(self.approved_tracks, 1):
            logger.info(f"[{idx}/{len(self.approved_tracks)}] Processing: {track.get('artist')} - {track.get('title')}")

            record = self.download_track(track)
            self.download_records.append(record)

            if not record.success:
                self.failed_downloads.append(record)

        self.save_download_log()
        return self._create_summary()

    def save_download_log(self) -> None:
        """Save download records to log file."""
        # Save all records
        log_path = self.logs_dir / 'downloads.json'
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(
                [record.to_dict() for record in self.download_records],
                f,
                indent=2
            )

        # Save failed downloads separately
        if self.failed_downloads:
            failed_path = self.logs_dir / 'failed_downloads.json'
            with open(failed_path, 'w', encoding='utf-8') as f:
                json.dump(
                    [record.to_dict() for record in self.failed_downloads],
                    f,
                    indent=2
                )

        logger.info(f"Saved download log to {log_path}")

    def _create_summary(self) -> Dict[str, Any]:
        """
        Create download summary.

        Returns:
            Summary dictionary
        """
        successful = sum(1 for r in self.download_records if r.success)
        failed = len(self.download_records) - successful
        total_size = sum(r.file_size for r in self.download_records if r.success)

        # Group by source
        by_source = {}
        for record in self.download_records:
            if record.success:
                source = record.source
                if source not in by_source:
                    by_source[source] = 0
                by_source[source] += 1

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tracks': len(self.download_records),
            'successful_downloads': successful,
            'failed_downloads': failed,
            'success_rate': round(successful / len(self.download_records) * 100, 2) if self.download_records else 0,
            'total_download_size_bytes': total_size,
            'downloads_by_source': by_source
        }

        # Save summary
        summary_path = self.logs_dir / 'download_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Download summary: {successful}/{len(self.download_records)} successful")

        return summary


def main():
    """Run download manager."""
    import sys
    from config_loader import ConfigLoader

    config = ConfigLoader().load()

    approved_tracks_file = os.path.join(config['base_path'], 'input', 'approved', 'approved_tracks.json')
    downloads_dir = os.path.join(config['base_path'], 'downloads')
    logs_dir = os.path.join(config['base_path'], 'logs')

    manager = DownloadManager(approved_tracks_file, downloads_dir, logs_dir)

    if manager.load_approved_tracks():
        summary = manager.download_all()
        return summary


if __name__ == '__main__':
    main()
