"""
Step 5: Mixed In Key Reader
Parse Mixed In Key analysis data and enrich track metadata.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MIKAnalyzer:
    """Parse and process Mixed In Key analysis data."""

    # Energy level mapping
    ENERGY_LEVELS = {
        'very low': 1,
        'low': 2,
        'medium-low': 3,
        'medium': 4,
        'medium-high': 5,
        'high': 6,
        'very high': 7
    }

    # Camelot wheel key conversion
    CAMELOT_TO_STANDARD = {
        '1A': 'B major', '1B': 'G# minor',
        '2A': 'F# major', '2B': 'D# minor',
        '3A': 'C# major', '3B': 'A# minor',
        '4A': 'G# major', '4B': 'F minor',
        '5A': 'D# major', '5B': 'C minor',
        '6A': 'A# major', '6B': 'G minor',
        '7A': 'F# major', '7B': 'D# minor',
        '8A': 'C# major', '8B': 'A# minor',
        '9A': 'G# major', '9B': 'E# minor',
        '10A': 'D# major', '10B': 'B# minor',
        '11A': 'A major', '11B': 'F# minor',
        '12A': 'E major', '12B': 'C# minor',
    }

    def __init__(self, mik_output_dir: str, download_dir: str, output_dir: str):
        """
        Initialize MIK reader.

        Args:
            mik_output_dir: Directory containing MIK analysis files
            download_dir: Directory containing downloaded tracks
            output_dir: Directory for enriched output
        """
        self.mik_output_dir = Path(mik_output_dir)
        self.download_dir = Path(download_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_mik_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse Mixed In Key CSV export.

        Args:
            file_path: Path to MIK CSV file

        Returns:
            List of track analysis dictionaries
        """
        import csv

        tracks = []
        logger.info(f"Parsing MIK CSV: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    analysis = self._parse_mik_row(row)
                    if analysis:
                        tracks.append(analysis)

            logger.info(f"Parsed {len(tracks)} tracks from {file_path}")
        except Exception as e:
            logger.error(f"Error parsing MIK CSV {file_path}: {e}")

        return tracks

    def parse_mik_xml(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse Mixed In Key XML export.

        Args:
            file_path: Path to MIK XML file

        Returns:
            List of track analysis dictionaries
        """
        tracks = []
        logger.info(f"Parsing MIK XML: {file_path}")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            for track_elem in root.findall('.//track'):
                analysis = self._parse_mik_xml_element(track_elem)
                if analysis:
                    tracks.append(analysis)

            logger.info(f"Parsed {len(tracks)} tracks from {file_path}")
        except Exception as e:
            logger.error(f"Error parsing MIK XML {file_path}: {e}")

        return tracks

    def _parse_mik_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse a single MIK CSV row.

        Args:
            row: CSV row dictionary

        Returns:
            Parsed analysis dictionary or None
        """
        try:
            # Extract file path to match with tracks
            file_path = row.get('Filename', '') or row.get('filename', '')

            # Extract analysis fields
            key_camelot = row.get('Key', '') or row.get('key', '')
            bpm = row.get('BPM', '') or row.get('bpm', '')
            energy = row.get('Energy Level', '') or row.get('energy', '')
            beatgrid = row.get('Beatgrid', '') or row.get('beatgrid', '')

            analysis = {
                'file_path': file_path.strip(),
                'camelot_key': key_camelot.strip(),
                'standard_key': self.CAMELOT_TO_STANDARD.get(key_camelot.strip(), key_camelot.strip()),
                'bpm': self._parse_bpm(bpm),
                'energy_level': energy.strip().lower(),
                'energy_numeric': self.ENERGY_LEVELS.get(energy.strip().lower(), None),
                'beatgrid': beatgrid.strip(),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return analysis
        except Exception as e:
            logger.warning(f"Error parsing MIK row: {e}")
            return None

    def _parse_mik_xml_element(self, elem) -> Optional[Dict[str, Any]]:
        """
        Parse a single MIK XML track element.

        Args:
            elem: XML element

        Returns:
            Parsed analysis dictionary or None
        """
        try:
            file_path = elem.findtext('filename', '')
            key_camelot = elem.findtext('key', '')
            bpm = elem.findtext('bpm', '')
            energy = elem.findtext('energy', '')

            analysis = {
                'file_path': file_path.strip(),
                'camelot_key': key_camelot.strip(),
                'standard_key': self.CAMELOT_TO_STANDARD.get(key_camelot.strip(), key_camelot.strip()),
                'bpm': self._parse_bpm(bpm),
                'energy_level': energy.strip().lower(),
                'energy_numeric': self.ENERGY_LEVELS.get(energy.strip().lower(), None),
                'analysis_timestamp': datetime.now().isoformat()
            }

            return analysis
        except Exception as e:
            logger.warning(f"Error parsing MIK XML element: {e}")
            return None

    def _parse_bpm(self, bpm_str: str) -> Optional[float]:
        """
        Parse BPM value.

        Args:
            bpm_str: BPM string (may contain range)

        Returns:
            BPM as float or None
        """
        if not bpm_str:
            return None

        try:
            # Handle ranges like "120-124"
            if '-' in bpm_str:
                parts = bpm_str.split('-')
                bpm1 = float(parts[0].strip())
                bpm2 = float(parts[1].strip())
                return (bpm1 + bpm2) / 2
            else:
                return float(bpm_str.strip())
        except ValueError:
            logger.warning(f"Could not parse BPM: {bpm_str}")
            return None

    def match_with_tracks(self, mik_analyses: List[Dict[str, Any]],
                         tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Match MIK analysis data with downloaded tracks.

        Args:
            mik_analyses: List of MIK analysis dictionaries
            tracks: List of track dictionaries

        Returns:
            Enriched track list with MIK data
        """
        enriched_tracks = []

        for track in tracks:
            artist = track.get('artist', '')
            title = track.get('title', '')

            # Try to find matching MIK analysis
            best_match = None
            best_score = 0

            for analysis in mik_analyses:
                file_path = analysis.get('file_path', '').lower()

                # Fuzzy match on artist/title
                if artist.lower() in file_path or title.lower() in file_path:
                    best_match = analysis
                    break

            enriched = track.copy()
            if best_match:
                enriched['mik_analysis'] = best_match
                enriched['camelot_key'] = best_match.get('camelot_key')
                enriched['standard_key'] = best_match.get('standard_key')
                enriched['energy_level'] = best_match.get('energy_level')
                enriched['energy_numeric'] = best_match.get('energy_numeric')
            else:
                enriched['mik_analysis'] = None

            enriched_tracks.append(enriched)

        return enriched_tracks

    def process_all_analyses(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all MIK analysis files and enrich tracks.

        Args:
            tracks: List of track dictionaries

        Returns:
            Enriched track list
        """
        all_analyses = []

        # Find and parse all MIK files
        for file_path in self.mik_output_dir.glob('*.csv'):
            analyses = self.parse_mik_csv(file_path)
            all_analyses.extend(analyses)

        for file_path in self.mik_output_dir.glob('*.xml'):
            analyses = self.parse_mik_xml(file_path)
            all_analyses.extend(analyses)

        logger.info(f"Found {len(all_analyses)} MIK analyses")

        # Match with tracks and enrich
        enriched_tracks = self.match_with_tracks(all_analyses, tracks)

        # Save enriched tracks
        output_path = self.output_dir / 'tracks_enriched_with_mik.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_tracks, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(enriched_tracks)} enriched tracks to {output_path}")

        return enriched_tracks


class MIKReader:
    """Main interface for MIK data reading and enrichment."""

    def __init__(self, mik_output_dir: str, output_dir: str):
        """
        Initialize MIK reader.

        Args:
            mik_output_dir: Directory with MIK output files
            output_dir: Directory for enriched output
        """
        self.analyzer = MIKAnalyzer(mik_output_dir, '', output_dir)

    def enrich_tracks(self, tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich tracks with MIK analysis data.

        Args:
            tracks: List of track dictionaries

        Returns:
            Enriched track list
        """
        return self.analyzer.process_all_analyses(tracks)

    def get_key_compatible_tracks(self, track: Dict[str, Any],
                                  all_tracks: List[Dict[str, Any]],
                                  camelot_distance: int = 1) -> List[Dict[str, Any]]:
        """
        Find tracks compatible for mixing based on Camelot key.

        Args:
            track: Reference track
            all_tracks: Pool of all tracks
            camelot_distance: Maximum Camelot wheel distance for compatibility

        Returns:
            List of compatible tracks
        """
        compatible = []
        ref_key = track.get('camelot_key', '')

        if not ref_key:
            return compatible

        ref_num = int(ref_key[:-1])  # Extract number from "12A"
        ref_mode = ref_key[-1]  # Extract mode (A or B)

        for candidate in all_tracks:
            cand_key = candidate.get('camelot_key', '')
            if not cand_key or cand_key == ref_key:
                continue

            try:
                cand_num = int(cand_key[:-1])
                cand_mode = cand_key[-1]

                # Check distance
                num_distance = min(abs(ref_num - cand_num), 12 - abs(ref_num - cand_num))
                mode_distance = 0 if ref_mode == cand_mode else 1

                if num_distance <= camelot_distance:
                    compatible.append(candidate)
            except (ValueError, IndexError):
                continue

        return compatible


def main():
    """Run MIK enrichment."""
    import sys
    from config_loader import ConfigLoader

    config = ConfigLoader().load()

    mik_output_dir = os.path.join(config['base_path'], 'mik-output')
    download_dir = os.path.join(config['base_path'], 'downloads')
    output_dir = os.path.join(config['base_path'], 'input', 'enriched')

    # Load approved tracks
    approved_file = os.path.join(config['base_path'], 'input', 'approved', 'approved_tracks.json')
    try:
        with open(approved_file, 'r', encoding='utf-8') as f:
            tracks = json.load(f)
    except Exception as e:
        logger.error(f"Error loading approved tracks: {e}")
        return

    # Process with MIK data
    reader = MIKReader(mik_output_dir, output_dir)
    enriched = reader.enrich_tracks(tracks)

    return enriched


if __name__ == '__main__':
    main()
