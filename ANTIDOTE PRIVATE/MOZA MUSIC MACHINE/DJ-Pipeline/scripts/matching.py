"""
Track Matching and Deduplication
Fuzzy matching on artist+title, BPM proximity, and key compatibility.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from difflib import SequenceMatcher
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MatchScore:
    """Score for a track match."""
    track_id: int
    artist_similarity: float
    title_similarity: float
    bpm_compatibility: float
    key_compatibility: float
    overall_score: float

    def __repr__(self) -> str:
        return (f"MatchScore(id={self.track_id}, "
                f"artist={self.artist_similarity:.2f}, "
                f"title={self.title_similarity:.2f}, "
                f"bpm={self.bpm_compatibility:.2f}, "
                f"key={self.key_compatibility:.2f}, "
                f"overall={self.overall_score:.2f})")


class TrackMatcher:
    """Match and deduplicate tracks using fuzzy matching."""

    def __init__(self, artist_weight: float = 0.3, title_weight: float = 0.4,
                 bpm_weight: float = 0.15, key_weight: float = 0.15):
        """
        Initialize matcher with scoring weights.

        Args:
            artist_weight: Weight for artist similarity (0-1)
            title_weight: Weight for title similarity (0-1)
            bpm_weight: Weight for BPM compatibility (0-1)
            key_weight: Weight for key compatibility (0-1)
        """
        total_weight = artist_weight + title_weight + bpm_weight + key_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights don't sum to 1.0: {total_weight}")

        self.artist_weight = artist_weight
        self.title_weight = title_weight
        self.bpm_weight = bpm_weight
        self.key_weight = key_weight

    def string_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity (0-1).

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0 and 1
        """
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()

        if str1 == str2:
            return 1.0

        # Remove common words and articles
        stop_words = {'the', 'a', 'an', 'and', 'or'}
        words1 = {w for w in str1.split() if w not in stop_words}
        words2 = {w for w in str2.split() if w not in stop_words}

        # Calculate intersection over union
        if not words1 or not words2:
            return SequenceMatcher(None, str1, str2).ratio()

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 0.0

        word_similarity = intersection / union

        # Also check character-level similarity
        char_similarity = SequenceMatcher(None, str1, str2).ratio()

        # Weight character similarity more for exact substrings
        if str1 in str2 or str2 in str1:
            char_similarity = min(1.0, char_similarity * 1.2)

        # Return weighted average
        return (word_similarity * 0.6) + (char_similarity * 0.4)

    def bpm_compatibility(self, bpm1: Optional[float], bpm2: Optional[float],
                         tolerance: float = 2.0) -> float:
        """
        Calculate BPM compatibility (0-1).

        Args:
            bpm1: First track BPM
            bpm2: Second track BPM
            tolerance: Acceptable BPM difference percentage

        Returns:
            Compatibility score
        """
        if not bpm1 or not bpm2:
            return 0.5  # Unknown BPM gets neutral score

        # Also check if BPMs are related by common DJ pitch shifts (±4-8%)
        bpm_ratio = bpm2 / bpm1
        compatible_ratios = [0.92, 0.96, 1.0, 1.04, 1.08]  # ±8%, ±4%, etc

        # Check if BPMs match within tolerance
        diff_pct = abs(bpm1 - bpm2) / ((bpm1 + bpm2) / 2) * 100

        if diff_pct <= tolerance:
            return 1.0

        # Check compatible ratios (time-stretching)
        for ratio in compatible_ratios:
            if abs(bpm_ratio - ratio) < 0.01:
                return 0.8

        # Penalize based on difference
        max_diff_pct = 20.0
        if diff_pct > max_diff_pct:
            return 0.0

        compatibility = 1.0 - (diff_pct / max_diff_pct)
        return max(0.0, compatibility)

    def key_compatibility(self, key1: Optional[str], key2: Optional[str]) -> float:
        """
        Calculate key compatibility using Camelot wheel.

        Args:
            key1: First track key (Camelot format like "12A")
            key2: Second track key

        Returns:
            Compatibility score (0-1)
        """
        if not key1 or not key2:
            return 0.5  # Unknown key gets neutral score

        key1 = key1.strip().upper()
        key2 = key2.strip().upper()

        if key1 == key2:
            return 1.0

        # Try to parse Camelot notation
        try:
            num1, mode1 = int(key1[:-1]), key1[-1]
            num2, mode2 = int(key2[:-1]), key2[-1]

            # Calculate distance on Camelot wheel
            num_distance = min(abs(num1 - num2), 12 - abs(num1 - num2))
            mode_distance = 0 if mode1 == mode2 else 1

            total_distance = num_distance + mode_distance

            # Compatible if within 1 step
            if total_distance <= 1:
                return 1.0
            # Acceptable if within 2 steps
            elif total_distance == 2:
                return 0.7
            # Poor compatibility
            else:
                return max(0.0, 1.0 - (total_distance / 12.0))

        except (ValueError, IndexError):
            # Fallback to string similarity if not Camelot format
            return self.string_similarity(key1, key2) * 0.5

    def match_tracks(self, track1: Dict[str, Any], track2: Dict[str, Any]) -> MatchScore:
        """
        Calculate match score between two tracks.

        Args:
            track1: First track dictionary
            track2: Second track dictionary

        Returns:
            MatchScore object
        """
        # Get fields
        artist1 = track1.get('artist', '')
        title1 = track1.get('title', '')
        bpm1 = track1.get('bpm')
        key1 = track1.get('key') or track1.get('camelot_key')

        artist2 = track2.get('artist', '')
        title2 = track2.get('title', '')
        bpm2 = track2.get('bpm')
        key2 = track2.get('key') or track2.get('camelot_key')

        # Calculate individual scores
        artist_sim = self.string_similarity(artist1, artist2)
        title_sim = self.string_similarity(title1, title2)
        bpm_comp = self.bpm_compatibility(bpm1, bpm2)
        key_comp = self.key_compatibility(key1, key2)

        # Calculate weighted overall score
        overall = (
            artist_sim * self.artist_weight +
            title_sim * self.title_weight +
            bpm_comp * self.bpm_weight +
            key_comp * self.key_weight
        )

        return MatchScore(
            track_id=track2.get('id', -1),
            artist_similarity=artist_sim,
            title_similarity=title_sim,
            bpm_compatibility=bpm_comp,
            key_compatibility=key_comp,
            overall_score=overall
        )

    def find_duplicates(self, tracks: List[Dict[str, Any]],
                       threshold: float = 0.85) -> List[List[int]]:
        """
        Find duplicate tracks in a list.

        Args:
            tracks: List of track dictionaries
            threshold: Minimum match score to consider duplicates

        Returns:
            List of lists containing indices of duplicate groups
        """
        duplicates = []
        processed = set()

        for i, track1 in enumerate(tracks):
            if i in processed:
                continue

            duplicate_group = [i]

            for j, track2 in enumerate(tracks[i + 1:], start=i + 1):
                if j in processed:
                    continue

                score = self.match_tracks(track1, track2)
                if score.overall_score >= threshold:
                    duplicate_group.append(j)
                    processed.add(j)

            if len(duplicate_group) > 1:
                duplicates.append(duplicate_group)
                processed.update(duplicate_group)

        return duplicates

    def find_best_mix_matches(self, track: Dict[str, Any],
                             candidates: List[Dict[str, Any]],
                             limit: int = 10) -> List[MatchScore]:
        """
        Find best tracks to mix with a given track.

        Args:
            track: Reference track
            candidates: Pool of candidate tracks
            limit: Maximum number of matches to return

        Returns:
            List of MatchScore objects, sorted by compatibility
        """
        scores = []

        for candidate in candidates:
            if candidate.get('artist') == track.get('artist') and \
               candidate.get('title') == track.get('title'):
                continue  # Skip the same track

            score = self.match_tracks(track, candidate)
            scores.append(score)

        # Sort by overall score and return top matches
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        return scores[:limit]


class KeyCompatibilityChart:
    """Reference chart for Camelot wheel key compatibility."""

    # Camelot wheel arranged in harmonic order
    CAMELOT_WHEEL = [
        ('8B', '5B', '2B', '11B', '6B', '1B', '8A', '3A', '10A', '5A', '12A', '7A'),
        ('1A', '8A', '3A', '10A', '5A', '12A', '7A', '2A', '9A', '4A', '11A', '6A'),
    ]

    @staticmethod
    def get_compatible_keys(key: str, distance: int = 1) -> List[str]:
        """
        Get compatible keys within distance on Camelot wheel.

        Args:
            key: Reference key in Camelot format
            distance: Distance to search (1-2 steps)

        Returns:
            List of compatible keys
        """
        compatible = [key]  # Include the key itself

        try:
            num = int(key[:-1])
            mode = key[-1]

            # Find adjacent positions
            for d in range(1, distance + 1):
                # Same mode, different positions
                next_num = ((num - 1 + d) % 12) + 1
                next_key = f"{next_num}{mode}"
                compatible.append(next_key)

                prev_num = ((num - 1 - d) % 12) + 1
                prev_key = f"{prev_num}{mode}"
                compatible.append(prev_key)

                # Same position, different mode
                if d == 1:
                    other_mode = 'B' if mode == 'A' else 'A'
                    compatible.append(f"{num}{other_mode}")

        except (ValueError, IndexError):
            pass

        return list(set(compatible))  # Remove duplicates


def main():
    """Test track matching."""
    matcher = TrackMatcher()

    track1 = {
        'artist': 'The Weeknd',
        'title': 'Blinding Lights',
        'bpm': 87.0,
        'key': '11A'
    }

    track2 = {
        'artist': 'The Weeknd',
        'title': 'Blinding Lights',
        'bpm': 88.0,
        'key': '11A'
    }

    score = matcher.match_tracks(track1, track2)
    print(f"Match score: {score}")
    print(f"Overall compatibility: {score.overall_score:.2%}")


if __name__ == '__main__':
    main()
