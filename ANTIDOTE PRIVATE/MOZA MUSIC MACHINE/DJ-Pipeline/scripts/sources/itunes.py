"""
iTunes/Apple Music Source Integration
Integration with iTunes Search API for track availability checking.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from .base import SourceBase, TrackSearchResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class iTunesSource(SourceBase):
    """iTunes/Apple Music source integration."""

    def __init__(self, api_key: str = None):
        """
        Initialize iTunes source.

        Args:
            api_key: Optional API key (iTunes API is public)
        """
        super().__init__(
            source_name='itunes',
            api_endpoint='https://itunes.apple.com/search',
            api_key=api_key
        )

    def search(self, artist: str, title: str) -> Optional[TrackSearchResult]:
        """
        Search for a track on iTunes.

        Args:
            artist: Track artist name
            title: Track title

        Returns:
            TrackSearchResult or None
        """
        try:
            query = f"{self.normalize_query(artist)} {self.normalize_query(title)}"

            # iTunes API is public, no auth needed
            headers = {
                'Content-Type': 'application/json'
            }

            params = {
                'term': query,
                'media': 'music',
                'limit': 1
            }

            logger.debug(f"Searching iTunes for: {query}")

            # Placeholder for actual API call
            # In production: response = requests.get(self.api_endpoint, params=params, timeout=self.timeout)
            # Parse JSON response and extract track info

            # Mock response structure
            result = TrackSearchResult(
                source_name='itunes',
                artist=artist,
                title=title,
                found=False,
                download_url=None,
                metadata={
                    'store_url': None,
                    'preview_url': None,
                    'format': 'digital',
                    'price_usd': None,
                    'collection_name': None,
                    'release_date': None,
                    'duration_ms': None,
                    'explicit': False
                }
            )

            return result

        except Exception as e:
            logger.error(f"Error searching iTunes: {e}")
            return TrackSearchResult(
                source_name='itunes',
                artist=artist,
                title=title,
                found=False,
                error=str(e)
            )

    def check_availability(self, artist: str, title: str, bpm: Optional[float] = None) -> bool:
        """
        Check if track is available on iTunes.

        Args:
            artist: Track artist name
            title: Track title
            bpm: Optional BPM for verification

        Returns:
            True if available
        """
        try:
            result = self.search(artist, title)
            if result:
                return result.found
            return False
        except Exception as e:
            logger.warning(f"Error checking iTunes availability: {e}")
            return False

    def download(self, artist: str, title: str, destination: Path) -> Optional[Path]:
        """
        iTunes does not support direct downloads.
        This returns the iTunes store URL instead.

        Args:
            artist: Track artist name
            title: Track title
            destination: Directory (not used for iTunes)

        Returns:
            Path or None (iTunes requires purchase/streaming)
        """
        try:
            result = self.search(artist, title)
            if not result or not result.metadata:
                logger.warning(f"Cannot get iTunes link for {artist} - {title}")
                return None

            store_url = result.metadata.get('store_url')
            if store_url:
                logger.info(f"iTunes store link: {store_url}")
                # In a real scenario, would save URL to a file
                return None
            else:
                logger.warning("iTunes requires purchase - not downloadable")
                return None

        except Exception as e:
            logger.error(f"Error with iTunes: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get iTunes source status."""
        status = super().get_status()
        status.update({
            'api_version': 'public',
            'requires_authentication': False,
            'supports_download': False,
            'download_method': 'streaming_or_purchase',
            'features': ['preview_url', 'store_link', 'metadata']
        })
        return status

    def get_preview_url(self, artist: str, title: str) -> Optional[str]:
        """
        Get preview URL for a track (30-second sample).

        Args:
            artist: Track artist
            title: Track title

        Returns:
            Preview URL or None
        """
        try:
            result = self.search(artist, title)
            if result and result.metadata:
                return result.metadata.get('preview_url')
            return None
        except Exception as e:
            logger.warning(f"Error getting preview URL: {e}")
            return None

    def get_store_url(self, artist: str, title: str) -> Optional[str]:
        """
        Get iTunes Store URL for a track.

        Args:
            artist: Track artist
            title: Track title

        Returns:
            Store URL or None
        """
        try:
            result = self.search(artist, title)
            if result and result.metadata:
                return result.metadata.get('store_url')
            return None
        except Exception as e:
            logger.warning(f"Error getting store URL: {e}")
            return None

    def search_by_artist(self, artist: str, limit: int = 10) -> Optional[TrackSearchResult]:
        """
        Search all tracks by an artist.

        Args:
            artist: Artist name
            limit: Maximum results

        Returns:
            First search result or None
        """
        try:
            params = {
                'term': artist,
                'media': 'music',
                'entity': 'song',
                'limit': limit
            }

            logger.debug(f"Searching iTunes for artist: {artist}")

            # Placeholder for actual API call
            return None

        except Exception as e:
            logger.error(f"Error searching by artist: {e}")
            return None

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitize string for use in filename.

        Args:
            name: Original name

        Returns:
            Sanitized name
        """
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
