"""
Step 3: Human Approval Checkpoint
Interactive approval workflow for track selection.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Interactive approval workflow for tracks."""

    def __init__(self, input_file: str, output_dir: str):
        """
        Initialize approval workflow.

        Args:
            input_file: Path to checked tracks JSON file
            output_dir: Directory for approval output
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tracks = []
        self.approved_tracks = []
        self.rejected_tracks = []
        self.skipped_tracks = []

    def load_tracks(self) -> bool:
        """
        Load checked tracks from input file.

        Returns:
            True if successful
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.tracks = json.load(f)
            logger.info(f"Loaded {len(self.tracks)} tracks from {self.input_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading tracks: {e}")
            return False

    def format_track_display(self, track: Dict[str, Any], index: int) -> str:
        """
        Format track for display to user.

        Args:
            track: Track dictionary
            index: Track number

        Returns:
            Formatted display string
        """
        artist = track.get('artist', 'Unknown')
        title = track.get('title', 'Unknown')
        bpm = track.get('bpm', 'N/A')
        key = track.get('key', 'N/A')
        genre = track.get('genre', 'N/A')
        available_count = track.get('available_count', 0)

        # Get source breakdown
        availability = track.get('availability', {})
        available_sources = [src for src, avail in availability.items() if avail]

        display = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Track {index}: {artist} - {title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BPM: {bpm}
  Key: {key}
  Genre: {genre}
  Original Source: {track.get('original_source', 'Unknown')}
  Available in {available_count}/5 sources: {', '.join(available_sources) if available_sources else 'None'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return display

    def get_user_decision(self, track_num: int, total: int) -> str:
        """
        Get user decision for a track.

        Args:
            track_num: Current track number
            total: Total tracks

        Returns:
            User decision: 'approve', 'reject', 'skip', 'quit'
        """
        valid_choices = {'a': 'approve', 'r': 'reject', 's': 'skip', 'q': 'quit'}

        while True:
            prompt = f"\n[{track_num}/{total}] Approve (a), Reject (r), Skip (s), or Quit (q)? "
            choice = input(prompt).lower().strip()

            if choice in valid_choices:
                return valid_choices[choice]
            else:
                print("Invalid choice. Please enter a, r, s, or q.")

    def interactive_approval(self) -> None:
        """Run interactive approval workflow."""
        if not self.tracks:
            logger.warning("No tracks loaded")
            return

        print(f"\n{'='*50}")
        print(f"APPROVAL WORKFLOW: {len(self.tracks)} tracks to review")
        print(f"{'='*50}\n")

        for idx, track in enumerate(self.tracks, 1):
            print(self.format_track_display(track, idx))

            decision = self.get_user_decision(idx, len(self.tracks))

            if decision == 'approve':
                self.approved_tracks.append(track)
                logger.info(f"Approved: {track.get('artist')} - {track.get('title')}")
            elif decision == 'reject':
                self.rejected_tracks.append(track)
                logger.info(f"Rejected: {track.get('artist')} - {track.get('title')}")
            elif decision == 'skip':
                self.skipped_tracks.append(track)
                logger.info(f"Skipped: {track.get('artist')} - {track.get('title')}")
            elif decision == 'quit':
                print("\nApproval workflow cancelled.")
                return

        self.save_results()

    def bulk_approve_by_threshold(self, min_sources: int = 3) -> None:
        """
        Bulk approve tracks available in minimum number of sources.

        Args:
            min_sources: Minimum number of sources for auto-approval
        """
        for track in self.tracks:
            if track.get('available_count', 0) >= min_sources:
                self.approved_tracks.append(track)
            else:
                self.skipped_tracks.append(track)

        logger.info(f"Auto-approved {len(self.approved_tracks)} tracks with {min_sources}+ sources")
        self.save_results()

    def save_results(self) -> None:
        """Save approval results to files."""
        # Save approved tracks
        approved_path = self.output_dir / 'approved_tracks.json'
        with open(approved_path, 'w', encoding='utf-8') as f:
            json.dump(self.approved_tracks, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.approved_tracks)} approved tracks to {approved_path}")

        # Save rejected tracks
        if self.rejected_tracks:
            rejected_path = self.output_dir / 'rejected_tracks.json'
            with open(rejected_path, 'w', encoding='utf-8') as f:
                json.dump(self.rejected_tracks, f, indent=2, ensure_ascii=False)

        # Save skipped tracks
        if self.skipped_tracks:
            skipped_path = self.output_dir / 'skipped_tracks.json'
            with open(skipped_path, 'w', encoding='utf-8') as f:
                json.dump(self.skipped_tracks, f, indent=2, ensure_ascii=False)

        # Save summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_reviewed': len(self.tracks),
            'approved': len(self.approved_tracks),
            'rejected': len(self.rejected_tracks),
            'skipped': len(self.skipped_tracks),
            'approval_rate': round(len(self.approved_tracks) / len(self.tracks) * 100, 2) if self.tracks else 0
        }

        summary_path = self.output_dir / 'approval_summary.json'
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Approval summary: {summary}")

    def create_download_list(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create a list organized by best sources for download.

        Returns:
            Dictionary mapping sources to tracks to download
        """
        download_map = {
            'djcity': [],
            'beatport': [],
            'bpmsupreme': [],
            'traxsource': [],
            'itunes': []
        }

        for track in self.approved_tracks:
            availability = track.get('availability', {})
            original_source = track.get('original_source', '')

            # Prefer original source if available
            if availability.get(original_source):
                download_map[original_source].append(track)
            else:
                # Use first available source
                for source, available in availability.items():
                    if available:
                        download_map[source].append(track)
                        break

        # Save download list
        download_path = self.output_dir / 'download_list.json'
        with open(download_path, 'w', encoding='utf-8') as f:
            json.dump(download_map, f, indent=2, ensure_ascii=False)

        logger.info(f"Created download list: {sum(len(v) for v in download_map.values())} tracks")

        return download_map


def main():
    """Run approval workflow."""
    import sys
    from config_loader import ConfigLoader

    config = ConfigLoader().load()

    input_file = os.path.join(config['base_path'], 'input', 'checked', 'all_tracks_checked.json')
    output_dir = os.path.join(config['base_path'], 'input', 'approved')

    workflow = ApprovalWorkflow(input_file, output_dir)

    if workflow.load_tracks():
        # Check for command-line argument for bulk approval
        if len(sys.argv) > 1 and sys.argv[1] == '--bulk':
            min_sources = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            workflow.bulk_approve_by_threshold(min_sources)
        else:
            workflow.interactive_approval()

        workflow.create_download_list()


if __name__ == '__main__':
    main()
