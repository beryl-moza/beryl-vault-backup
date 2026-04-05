"""
DJ Pool Source Integrations
Package for all DJ pool source modules and classes.
"""

from .base import SourceBase
from .djcity import DJCitySource
from .beatport import BeatportSource
from .bpmsupreme import BPMSupremeSource
from .traxsource import TraxsourceSource
from .itunes import iTunesSource

__all__ = [
    'SourceBase',
    'DJCitySource',
    'BeatportSource',
    'BPMSupremeSource',
    'TraxsourceSource',
    'iTunesSource',
]

# Source registry for easy access
SOURCE_REGISTRY = {
    'djcity': DJCitySource,
    'beatport': BeatportSource,
    'bpmsupreme': BPMSupremeSource,
    'traxsource': TraxsourceSource,
    'itunes': iTunesSource,
}


def get_source(source_name: str) -> SourceBase:
    """
    Get source instance by name.

    Args:
        source_name: Name of source (djcity, beatport, etc)

    Returns:
        Source instance

    Raises:
        ValueError: If source not found
    """
    source_class = SOURCE_REGISTRY.get(source_name.lower())
    if not source_class:
        raise ValueError(f"Unknown source: {source_name}")
    return source_class()


def get_all_sources() -> dict:
    """
    Get all available sources.

    Returns:
        Dictionary mapping source names to instances
    """
    return {name: cls() for name, cls in SOURCE_REGISTRY.items()}
