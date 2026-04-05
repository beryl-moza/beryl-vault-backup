"""
Base class for DJ pool sources.
Abstract base class defining the interface for all DJ pool integrations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrackSearchResult:
    """Result of a track search."""
    source_name: str
    artist: str
    title: str
    found: bool
    download_url: Optional[str] = None
    metadata: Dict[str, Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_name': self.source_name,
            'artist': self.artist,
            'title': self.title,
            'found': self.found,
            'download_url': self.download_url,
            'metadata': self.metadata,
            'error': self.error
        }


class SourceBase(ABC):
    """Abstract base class for DJ pool sources."""

    def __init__(self, source_name: str, api_endpoint: str = None, api_key: str = None):
        """
        Initialize source.

        Args:
            source_name: Name of the source (djcity, beatport, etc)
            api_endpoint: API endpoint URL
            api_key: API key for authentication
        """
        self.source_name = source_name
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.session = None
        self.timeout = 30

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.source_name})"

    @abstractmethod
    def search(self, artist: str, title: str) -> Optional[TrackSearchResult]:
        """
        Search for a track in the source.

        Args:
            artist: Track artist name
            title: Track title

        Returns:
            TrackSearchResult or None if not found
        """
        pass

    @abstractmethod
    def check_availability(self, artist: str, title: str, bpm: Optional[float] = None) -> bool:
        """
        Check if a track is available in this source.

        Args:
            artist: Track artist name
            title: Track title
            bpm: Track BPM (optional, for additional verification)

        Returns:
            True if track is available
        """
        pass

    @abstractmethod
    def download(self, artist: str, title: str, destination: Path) -> Optional[Path]:
        """
        Download a track from this source.

        Args:
            artist: Track artist name
            title: Track title
            destination: Directory to save the file

        Returns:
            Path to downloaded file or None if failed
        """
        pass

    def authenticate(self) -> bool:
        """
        Authenticate with the source API.

        Returns:
            True if authentication successful
        """
        if not self.api_key:
            logger.warning(f"No API key configured for {self.source_name}")
            return False

        try:
            self._authenticate()
            logger.info(f"Authenticated with {self.source_name}")
            return True
        except Exception as e:
            logger.error(f"Authentication failed for {self.source_name}: {e}")
            return False

    def _authenticate(self) -> None:
        """
        Perform actual authentication. Override in subclasses.
        """
        pass

    def normalize_query(self, text: str) -> str:
        """
        Normalize search query text.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Remove special characters, convert to lowercase
        text = text.lower().strip()

        # Remove common remixes and versions
        versions = [' remix', ' feat', ' ft.', ' featuring', ' (feat', ' (ft',
                   ' extended mix', ' radio edit', ' dub', ' acapella']
        for version in versions:
            text = text.split(version)[0]

        return text.strip()

    def get_status(self) -> Dict[str, Any]:
        """
        Get source status.

        Returns:
            Status dictionary
        """
        return {
            'source_name': self.source_name,
            'authenticated': self.api_key is not None,
            'api_endpoint': self.api_endpoint,
            'available': True
        }

    def get_metadata(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a track.

        Args:
            artist: Track artist
            title: Track title

        Returns:
            Metadata dictionary or None
        """
        result = self.search(artist, title)
        if result and result.metadata:
            return result.metadata
        return None

    def rate_limit_check(self) -> bool:
        """
        Check if source is currently rate-limited.

        Returns:
            True if rate-limited
        """
        # Override in subclasses if needed
        return False

    def wait_if_rate_limited(self, max_wait: int = 60) -> bool:
        """
        Wait if rate-limited, up to max_wait seconds.

        Args:
            max_wait: Maximum wait time in seconds

        Returns:
            True if no longer rate-limited
        """
        import time

        elapsed = 0
        while self.rate_limit_check() and elapsed < max_wait:
            logger.warning(f"{self.source_name} is rate-limited, waiting...")
            wait_time = min(5, max_wait - elapsed)
            time.sleep(wait_time)
            elapsed += wait_time

        return not self.rate_limit_check()


class SourceFactory:
    """Factory for creating source instances."""

    _sources = {}

    @classmethod
    def register_source(cls, source_class: type) -> None:
        """
        Register a source class.

        Args:
            source_class: Source class to register
        """
        source_name = source_class.__name__.replace('Source', '').lower()
        cls._sources[source_name] = source_class

    @classmethod
    def create_source(cls, source_name: str, **kwargs) -> SourceBase:
        """
        Create a source instance.

        Args:
            source_name: Name of source to create
            **kwargs: Additional arguments for source initialization

        Returns:
            Source instance

        Raises:
            ValueError: If source not found
        """
        source_class = cls._sources.get(source_name.lower())
        if not source_class:
            raise ValueError(f"Unknown source: {source_name}")
        return source_class(**kwargs)

    @classmethod
    def get_available_sources(cls) -> List[str]:
        """
        Get list of available sources.

        Returns:
            List of source names
        """
        return list(cls._sources.keys())
