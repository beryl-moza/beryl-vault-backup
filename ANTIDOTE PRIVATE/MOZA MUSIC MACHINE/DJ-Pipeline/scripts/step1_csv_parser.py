"""
Step 1: CSV Parser for DJ Pool Track Lists
Parses CSV files from DJ pools (DJCity, Beatport, etc.) and normalizes to standardized JSON format.
"""

import csv
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CSVParser:
    """Parse DJ pool CSV files and normalize to standard format."""

    # Column mapping for different DJ pool formats
    COLUMN_MAPPINGS = {
        'djcity': {
            'artist': ['artist', 'artist name'],
            'title': ['title', 'track name', 'song title'],
            'bpm': ['bpm', 'tempo'],
            'key': ['key', 'musical key'],
            'genre': ['genre', 'category'],
            'duration': ['duration', 'length'],
            'source': 'djcity'
        },
        'beatport': {
            'artist': ['artist', 'artists'],
            'title': ['track title', 'title', 'name'],
            'bpm': ['bpm', 'tempo'],
            'key': ['key', 'musical key', 'initial key'],
            'genre': ['genre', 'primary genre'],
            'duration': ['duration', 'length'],
            'source': 'beatport'
        },
        'bpmsupreme': {
            'artist': ['artist', 'artist name'],
            'title': ['title', 'track title'],
            'bpm': ['bpm', 'tempo'],
            'key': ['key', 'musical key'],
            'genre': ['genre', 'category'],
            'duration': ['duration', 'length'],
            'source': 'bpmsupreme'
        },
        'traxsource': {
            'artist': ['artist', 'artist name'],
            'title': ['title', 'track name'],
            'bpm': ['bpm', 'tempo'],
            'key': ['key', 'musical key'],
            'genre': ['genre', 'category'],
            'duration': ['duration', 'length'],
            'source': 'traxsource'
        },
        'generic': {
            'artist': ['artist', 'artist name', 'artist_name'],
            'title': ['title', 'track name', 'track_name', 'song title'],
            'bpm': ['bpm', 'tempo', 'tempo_bpm'],
            'key': ['key', 'musical key', 'musical_key'],
            'genre': ['genre', 'category', 'genre_category'],
            'duration': ['duration', 'length', 'track_duration'],
            'source': 'unknown'
        }
    }

    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize parser.

        Args:
            input_dir: Directory containing CSV files
            output_dir: Directory for parsed JSON output
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def detect_pool_source(self, headers: List[str]) -> str:
        """
        Detect which DJ pool format based on headers.

        Args:
            headers: Column headers from CSV

        Returns:
            Source name or 'generic'
        """
        headers_lower = [h.lower().strip() for h in headers]

        # Check for DJCity characteristics
        if any('djcity' in h for h in headers_lower):
            return 'djcity'

        # Check for Beatport characteristics
        if any('beatport' in h for h in headers_lower) or any('primary genre' in h for h in headers_lower):
            return 'beatport'

        # Check for BPM Supreme characteristics
        if any('bpmsupreme' in h for h in headers_lower):
            return 'bpmsupreme'

        # Check for Traxsource characteristics
        if any('traxsource' in h for h in headers_lower):
            return 'traxsource'

        return 'generic'

    def normalize_track(self, row: Dict[str, str], pool_source: str) -> Optional[Dict[str, Any]]:
        """
        Normalize a track row to standard format.

        Args:
            row: CSV row as dictionary
            pool_source: Detected pool source

        Returns:
            Normalized track dictionary or None if required fields missing
        """
        mapping = self.COLUMN_MAPPINGS.get(pool_source, self.COLUMN_MAPPINGS['generic'])

        # Find matching columns (case-insensitive)
        row_keys_lower = {k.lower().strip(): k for k in row.keys()}

        def get_field(field_name: str) -> Optional[str]:
            """Get field value from row with fallback to alternatives."""
            alternatives = mapping.get(field_name, [])
            if isinstance(alternatives, str):
                return alternatives

            for alt in alternatives:
                alt_lower = alt.lower().strip()
                if alt_lower in row_keys_lower:
                    value = row[row_keys_lower[alt_lower]]
                    return value.strip() if value else None
            return None

        # Extract required fields
        artist = get_field('artist')
        title = get_field('title')

        if not artist or not title:
            logger.warning(f"Skipping track with missing artist/title: {row}")
            return None

        # Extract optional fields
        bpm_str = get_field('bpm')
        bpm = None
        if bpm_str:
            try:
                bpm = float(bpm_str)
            except ValueError:
                logger.warning(f"Invalid BPM value: {bpm_str}")

        key = get_field('key')
        genre = get_field('genre')
        duration = get_field('duration')

        normalized = {
            'artist': artist.strip(),
            'title': title.strip(),
            'bpm': bpm,
            'key': key.strip() if key else None,
            'genre': genre.strip() if genre else None,
            'duration': duration.strip() if duration else None,
            'source': pool_source
        }

        return normalized

    def parse_csv(self, csv_file: Path) -> List[Dict[str, Any]]:
        """
        Parse a single CSV file.

        Args:
            csv_file: Path to CSV file

        Returns:
            List of normalized tracks
        """
        logger.info(f"Parsing CSV: {csv_file}")
        tracks = []

        try:
            with open(csv_file, 'r', encoding='utf-8', errors='replace') as f:
                # Try to detect delimiter
                sample = f.read(1024)
                f.seek(0)

                has_semicolon = sample.count(';') > sample.count(',')
                delimiter = ';' if has_semicolon else ','

                reader = csv.DictReader(f, delimiter=delimiter)

                if reader.fieldnames is None:
                    logger.error(f"Could not read CSV headers: {csv_file}")
                    return tracks

                pool_source = self.detect_pool_source(reader.fieldnames)
                logger.info(f"Detected pool source: {pool_source}")

                for row_num, row in enumerate(reader, start=2):
                    normalized = self.normalize_track(row, pool_source)
                    if normalized:
                        tracks.append(normalized)
                    else:
                        logger.warning(f"Skipped row {row_num}")

            logger.info(f"Successfully parsed {len(tracks)} tracks from {csv_file}")

        except Exception as e:
            logger.error(f"Error parsing {csv_file}: {e}")

        return tracks

    def save_tracks(self, tracks: List[Dict[str, Any]], output_file: Path) -> None:
        """
        Save normalized tracks to JSON.

        Args:
            tracks: List of normalized track dictionaries
            output_file: Output JSON file path
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(tracks)} tracks to {output_file}")

    def process_all_csvs(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Process all CSV files in input directory.

        Returns:
            Dictionary mapping filenames to track lists
        """
        results = {}

        csv_files = sorted(self.input_dir.glob('*.csv'))
        logger.info(f"Found {len(csv_files)} CSV files")

        for csv_file in csv_files:
            tracks = self.parse_csv(csv_file)

            # Save to JSON
            output_name = csv_file.stem + '_parsed.json'
            output_path = self.output_dir / output_name
            self.save_tracks(tracks, output_path)

            results[csv_file.name] = tracks

        # Create summary
        summary_path = self.output_dir / 'parsing_summary.json'
        summary = {
            'timestamp': datetime.now().isoformat(),
            'files_processed': len(results),
            'total_tracks': sum(len(tracks) for tracks in results.values()),
            'files': {
                filename: {
                    'track_count': len(tracks),
                    'output_file': f"{Path(filename).stem}_parsed.json"
                }
                for filename, tracks in results.items()
            }
        }

        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Parsing complete. Summary saved to {summary_path}")

        return results


def main():
    """Run CSV parser on all files in input directory."""
    import sys
    from config_loader import ConfigLoader

    config = ConfigLoader().load()

    input_dir = os.path.join(config['base_path'], 'input')
    output_dir = os.path.join(input_dir, 'parsed')

    parser = CSVParser(input_dir, output_dir)
    results = parser.process_all_csvs()

    return results


if __name__ == '__main__':
    main()
