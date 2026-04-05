"""
Step 2: Source Checker for Track Availability
Checks availability of parsed tracks across multiple DJ pool sources.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrackAvailability:
    """Track availability information."""
    artist: str
    title: str
    bpm: Optional[float]
    key: Optional[str]
    genre: Optional[str]
    original_source: str
    availability: Dict[str, bool]
    available_count: int
    checked_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SourceChecker:
    """Check track availability across multiple DJ pool sources."""

    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize checker.

        Args:
            input_dir: Directory containing parsed JSON files
            output_dir: Directory for checked output
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Import source modules
        from sources import DJCitySource, BeatportSource, BPMSupremeSource, TraxsourceSource, iTunesSource

        self.sources = {
            'djcity': DJCitySource(),
            'beatport': BeatportSource(),
            'bpmsupreme': BPMSupremeSource(),
            'traxsource': TraxsourceSource(),
            'itunes': iTunesSource()
        }

    def check_availability(self, track: Dict[str, Any]) -> TrackAvailability:
        """
        Check availability of a track across all sources.

        Args:
            track: Track dictionary from parsed JSON

        Returns:
            TrackAvailability object with availability info
        """
        artist = track.get('artist', '')
        title = track.get('title', '')
        bpm = track.get('bpm')
        key = track.get('key')
        genre = track.get('genre')
        original_source = track.get('source', 'unknown')

        availability = {}
        available_count = 0

        # Check each source
        for source_name, source_instance in self.sources.items():
            try:
                # Check if track is available in this source
                is_available = source_instance.check_availability(
                    artist=artist,
                    title=title,
                    bpm=bpm
                )
                availability[source_name] = is_available
                if is_available:
                    available_count += 1
                logger.debug(f"Checked {source_name}: {source_name}={is_available}")
            except Exception as e:
                logger.warning(f"Error checking {source_name} for {artist} - {title}: {e}")
                availability[source_name] = False

        track_availability = TrackAvailability(
            artist=artist,
            title=title,
            bpm=bpm,
            key=key,
            genre=genre,
            original_source=original_source,
            availability=availability,
            available_count=available_count,
            checked_timestamp=datetime.now().isoformat()
        )

        return track_availability

    def process_parsed_tracks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process all parsed track files and check availability.

        Returns:
            Dictionary mapping input filenames to checked tracks
        """
        results = {}
        all_checked_tracks = []

        # Find all parsed JSON files
        parsed_files = sorted(self.input_dir.glob('*_parsed.json'))
        logger.info(f"Found {len(parsed_files)} parsed track files")

        for parsed_file in parsed_files:
            logger.info(f"Processing: {parsed_file}")

            try:
                with open(parsed_file, 'r', encoding='utf-8') as f:
                    tracks = json.load(f)

                checked_tracks = []
                for track in tracks:
                    availability = self.check_availability(track)
                    checked_track_dict = availability.to_dict()
                    checked_tracks.append(checked_track_dict)
                    all_checked_tracks.append(checked_track_dict)

                # Save individual file results
                output_name = parsed_file.stem.replace('_parsed', '_checked') + '.json'
                output_path = self.output_dir / output_name

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(checked_tracks, f, indent=2, ensure_ascii=False)

                logger.info(f"Checked {len(checked_tracks)} tracks from {parsed_file.name}")
                results[parsed_file.name] = checked_tracks

            except Exception as e:
                logger.error(f"Error processing {parsed_file}: {e}")

        # Create master checked file
        master_path = self.output_dir / 'all_tracks_checked.json'
        with open(master_path, 'w', encoding='utf-8') as f:
            json.dump(all_checked_tracks, f, indent=2, ensure_ascii=False)

        # Create summary report
        summary = self._create_summary(all_checked_tracks)
        summary_path = self.output_dir / 'availability_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Availability check complete. {len(all_checked_tracks)} total tracks checked")

        return results

    def _create_summary(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create summary statistics of availability checks.

        Args:
            tracks: List of checked track dictionaries

        Returns:
            Summary statistics dictionary
        """
        source_stats = {
            'djcity': {'available': 0, 'checked': 0},
            'beatport': {'available': 0, 'checked': 0},
            'bpmsupreme': {'available': 0, 'checked': 0},
            'traxsource': {'available': 0, 'checked': 0},
            'itunes': {'available': 0, 'checked': 0}
        }

        for track in tracks:
            availability = track.get('availability', {})
            for source, available in availability.items():
                if source in source_stats:
                    source_stats[source]['checked'] += 1
                    if available:
                        source_stats[source]['available'] += 1

        # Calculate percentages
        for source in source_stats:
            total = source_stats[source]['checked']
            available = source_stats[source]['available']
            pct = (available / total * 100) if total > 0 else 0
            source_stats[source]['availability_percentage'] = round(pct, 2)

        # Count tracks by availability
        tracks_by_availability = {
            'available_all_sources': sum(1 for t in tracks if t['available_count'] == 5),
            'available_most_sources': sum(1 for t in tracks if 3 <= t['available_count'] < 5),
            'available_some_sources': sum(1 for t in tracks if 1 <= t['available_count'] < 3),
            'unavailable': sum(1 for t in tracks if t['available_count'] == 0)
        }

        return {
            'timestamp': datetime.now().isoformat(),
            'total_tracks_checked': len(tracks),
            'tracks_by_availability': tracks_by_availability,
            'source_statistics': source_stats
        }


def main():
    """Run source checker on all parsed tracks."""
    import sys
    from config_loader import ConfigLoader

    config = ConfigLoader().load()

    input_dir = os.path.join(config['base_path'], 'input', 'parsed')
    output_dir = os.path.join(config['base_path'], 'input', 'checked')

    checker = SourceChecker(input_dir, output_dir)
    results = checker.process_parsed_tracks()

    return results


if __name__ == '__main__':
    import os
    main()
