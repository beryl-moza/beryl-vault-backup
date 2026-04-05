"""
Step 6: Rekordbox XML Generator
Generate Rekordbox-compatible XML library file from enriched track data.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RekordboxXMLGenerator:
    """Generate Rekordbox-compatible XML library files."""

    # Rekordbox key notation mapping (Camelot to Rekordbox)
    CAMELOT_TO_REKORDBOX_KEY = {
        '1A': '11', '1B': '8',      # B major / G# minor
        '2A': '6', '2B': '3',       # F# major / D# minor
        '3A': '1', '3B': '10',      # C# major / A# minor
        '4A': '8', '4B': '5',       # Ab major / F minor
        '5A': '3', '5B': '12',      # Eb major / C minor
        '6A': '10', '6B': '7',      # Bb major / G minor
        '7A': '5', '7B': '2',       # F major / D minor
        '8A': '12', '8B': '9',      # B major / G# minor
        '9A': '7', '9B': '4',       # G major / E minor
        '10A': '2', '10B': '11',    # D major / B minor
        '11A': '9', '11B': '6',     # A major / F# minor
        '12A': '4', '12B': '1',     # E major / C# minor
    }

    def __init__(self, output_dir: str = None):
        """
        Initialize Rekordbox XML generator.

        Args:
            output_dir: Directory for output XML files
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_rekordbox_xml(self, tracks: List[Dict[str, Any]],
                            library_name: str = "MOZA DJ Library") -> ET.Element:
        """
        Create Rekordbox XML library structure.

        Args:
            tracks: List of enriched track dictionaries
            library_name: Name for the library

        Returns:
            Root XML element
        """
        root = ET.Element('DJ_PLAYLISTS')
        root.set('Version', '1.0.0')

        # Create product element
        product = ET.SubElement(root, 'PRODUCT')
        product.set('Name', 'rekordbox')
        product.set('Version', '6.0.0')
        product.set('Company', 'Pioneer')

        # Create playlists section
        playlists = ET.SubElement(root, 'PLAYLISTS')
        playlists.set('entries', str(len(tracks)))

        # Add tracks to library
        for idx, track in enumerate(tracks, 1):
            self._add_track_to_playlist(playlists, track, idx)

        return root

    def _add_track_to_playlist(self, parent: ET.Element, track: Dict[str, Any],
                              track_id: int) -> None:
        """
        Add a track to the playlist.

        Args:
            parent: Parent XML element
            track: Track dictionary
            track_id: Unique track ID
        """
        track_elem = ET.SubElement(parent, 'TRACK')
        track_elem.set('TrackID', str(track_id))

        # Basic info
        self._add_element(track_elem, 'Name', track.get('title', ''))
        self._add_element(track_elem, 'Artist', track.get('artist', ''))
        self._add_element(track_elem, 'Album', track.get('genre', ''))

        # Duration
        duration = track.get('duration')
        if duration:
            seconds = self._parse_duration(duration)
            if seconds:
                self._add_element(track_elem, 'Duration', str(int(seconds)))

        # BPM
        bpm = track.get('bpm')
        if bpm:
            tempo = ET.SubElement(track_elem, 'TEMPO')
            tempo.set('Inizio', '1')
            tempo.set('Bpm', str(bpm))

        # Key - use MIK data if available, otherwise use original
        key = self._get_rekordbox_key(track)
        if key:
            self._add_element(track_elem, 'KEY', key)

        # File path - construct if we have download info
        file_path = track.get('file_path') or self._construct_file_path(track)
        if file_path:
            self._add_element(track_elem, 'Location', file_path)

        # Genre
        genre = track.get('genre')
        if genre:
            self._add_element(track_elem, 'Genre', genre)

        # Comments - add metadata
        comments = self._build_comments(track)
        if comments:
            self._add_element(track_elem, 'Comments', comments)

        # Year
        self._add_element(track_elem, 'Year', '')

        # Rating/Color
        self._add_element(track_elem, 'Rating', '0')

    def _get_rekordbox_key(self, track: Dict[str, Any]) -> Optional[str]:
        """
        Get Rekordbox key notation for a track.

        Args:
            track: Track dictionary

        Returns:
            Rekordbox key notation or None
        """
        # Try to get from MIK analysis first
        mik_analysis = track.get('mik_analysis')
        if mik_analysis:
            camelot_key = mik_analysis.get('camelot_key')
            if camelot_key:
                return self.CAMELOT_TO_REKORDBOX_KEY.get(camelot_key)

        # Fall back to original key
        original_key = track.get('key')
        if original_key:
            return original_key

        return None

    def _construct_file_path(self, track: Dict[str, Any]) -> Optional[str]:
        """
        Construct file path for track.

        Args:
            track: Track dictionary

        Returns:
            File path or None
        """
        artist = track.get('artist', 'Unknown')
        title = track.get('title', 'Unknown')
        source = track.get('source', 'unknown')

        # Format: file:///path/to/downloads/source/artist - title.mp3
        # This is a template; actual path would need to be set during download
        safe_artist = self._sanitize_filename(artist)
        safe_title = self._sanitize_filename(title)
        filename = f"{safe_artist} - {safe_title}.mp3"

        # URL-encoded path
        relative_path = f"downloads/{source}/{filename}"
        return f"file:///{quote(relative_path)}"

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """
        Parse duration string to seconds.

        Args:
            duration_str: Duration in format "MM:SS" or seconds

        Returns:
            Duration in seconds or None
        """
        if not duration_str:
            return None

        try:
            if ':' in duration_str:
                parts = duration_str.split(':')
                minutes = int(parts[0])
                seconds = int(parts[1]) if len(parts) > 1 else 0
                return minutes * 60 + seconds
            else:
                return int(duration_str)
        except ValueError:
            logger.warning(f"Could not parse duration: {duration_str}")
            return None

    def _build_comments(self, track: Dict[str, Any]) -> str:
        """
        Build comments string from track metadata.

        Args:
            track: Track dictionary

        Returns:
            Comments string
        """
        parts = []

        # Add energy level if available
        energy = track.get('energy_level')
        if energy:
            parts.append(f"Energy: {energy}")

        # Add availability info
        availability = track.get('availability', {})
        if availability:
            available_sources = [s for s, v in availability.items() if v]
            if available_sources:
                parts.append(f"Available in: {', '.join(available_sources)}")

        # Add source
        source = track.get('original_source')
        if source:
            parts.append(f"Source: {source}")

        return " | ".join(parts) if parts else ""

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitize name for use in filename.

        Args:
            name: Original name

        Returns:
            Sanitized name
        """
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    @staticmethod
    def _add_element(parent: ET.Element, tag: str, text: str) -> ET.Element:
        """
        Add text element to parent.

        Args:
            parent: Parent element
            tag: Element tag name
            text: Element text

        Returns:
            Created element
        """
        elem = ET.SubElement(parent, tag)
        elem.text = str(text)
        return elem

    def generate_xml_file(self, tracks: List[Dict[str, Any]],
                         output_filename: str = "rekordbox_library.xml") -> Path:
        """
        Generate and save Rekordbox XML file.

        Args:
            tracks: List of enriched track dictionaries
            output_filename: Name for output XML file

        Returns:
            Path to output file
        """
        logger.info(f"Generating Rekordbox XML for {len(tracks)} tracks")

        root = self.create_rekordbox_xml(tracks)

        # Format XML with indentation
        self._indent_xml(root)

        # Create tree and save
        tree = ET.ElementTree(root)
        output_path = self.output_dir / output_filename

        try:
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"Saved Rekordbox XML to {output_path}")
        except Exception as e:
            logger.error(f"Error writing XML file: {e}")
            raise

        return output_path

    @staticmethod
    def _indent_xml(elem: ET.Element, level: int = 0) -> None:
        """
        Add indentation to XML for readability.

        Args:
            elem: XML element
            level: Indentation level
        """
        indent = "\n" + ("  " * level)
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                RekordboxXMLGenerator._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


class RekordboxLibraryBuilder:
    """Build complete Rekordbox library with playlists."""

    def __init__(self, output_dir: str):
        """
        Initialize library builder.

        Args:
            output_dir: Directory for output files
        """
        self.generator = RekordboxXMLGenerator(output_dir)
        self.output_dir = Path(output_dir)

    def build_library(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build complete Rekordbox library.

        Args:
            tracks: List of enriched track dictionaries

        Returns:
            Dictionary with build results
        """
        output_file = self.generator.generate_xml_file(tracks)

        # Create summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_tracks': len(tracks),
            'output_file': str(output_file),
            'rekordbox_format': '6.0.0',
            'tracks_with_mik_analysis': sum(1 for t in tracks if t.get('mik_analysis')),
            'tracks_with_key_data': sum(1 for t in tracks if t.get('camelot_key') or t.get('key'))
        }

        summary_path = self.output_dir / 'rekordbox_build_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Library build complete: {summary}")

        return summary


def main():
    """Run Rekordbox XML generator."""
    import sys
    from config_loader import ConfigLoader

    config = ConfigLoader().load()

    # Load enriched tracks
    enriched_file = os.path.join(config['base_path'], 'input', 'enriched', 'tracks_enriched_with_mik.json')

    try:
        with open(enriched_file, 'r', encoding='utf-8') as f:
            tracks = json.load(f)
    except FileNotFoundError:
        logger.warning(f"Enriched tracks file not found: {enriched_file}")
        logger.info("Using approved tracks instead")
        approved_file = os.path.join(config['base_path'], 'input', 'approved', 'approved_tracks.json')
        with open(approved_file, 'r', encoding='utf-8') as f:
            tracks = json.load(f)

    output_dir = os.path.join(config['base_path'], 'rekordbox')

    builder = RekordboxLibraryBuilder(output_dir)
    summary = builder.build_library(tracks)

    return summary


if __name__ == '__main__':
    main()
