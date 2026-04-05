# MOZA DJ Pipeline - Implementation Guide

## Overview
The MOZA DJ Pipeline is a comprehensive Python toolkit for managing DJ track workflows across multiple pool sources (DJCity, Beatport, BPM Supreme, Traxsource, iTunes).

## Architecture

### Pipeline Flow
```
CSV Files from Pools
        ↓
   Step 1: CSV Parser (normalize to JSON)
        ↓
   Step 2: Source Checker (check availability)
        ↓
   Step 3: Approval (interactive user review)
        ↓
   Step 4: Download Manager (get track files)
        ↓
   Step 5: MIK Reader (add analysis data)
        ↓
   Step 6: Rekordbox XML (generate library)
```

## Modules

### Core Utilities

#### ConfigLoader (`config_loader.py`)
Manages pipeline configuration from JSON/YAML files and environment variables.

```python
from config_loader import ConfigLoader

config = ConfigLoader().load()
base_path = config['base_path']
djcity_key = config.get_api_key('djcity')
```

**Features:**
- Auto-discovers config.json/config.yaml
- Environment variable overrides
- Validation and error handling
- Source-specific configuration

#### TrackMatcher (`matching.py`)
Performs fuzzy matching, deduplication, and compatibility checking.

```python
from matching import TrackMatcher

matcher = TrackMatcher()
score = matcher.match_tracks(track1, track2)
duplicates = matcher.find_duplicates(tracks, threshold=0.85)
compatible = matcher.find_best_mix_matches(track, candidates)
```

**Features:**
- String similarity (Levenshtein-based)
- BPM compatibility checking
- Camelot wheel key compatibility
- Duplicate detection

### Pipeline Steps

#### Step 1: CSV Parser (`step1_csv_parser.py`)
Parses CSV files from DJ pools and normalizes to standard JSON format.

```python
from step1_csv_parser import CSVParser

parser = CSVParser(input_dir='input', output_dir='input/parsed')
results = parser.process_all_csvs()
```

**Input:** CSV files in ../input/
**Output:** JSON files in ../input/parsed/

Supports formats from: DJCity, Beatport, BPM Supreme, Traxsource

#### Step 2: Source Checker (`step2_source_checker.py`)
Checks availability of parsed tracks across all DJ pool sources.

```python
from step2_source_checker import SourceChecker

checker = SourceChecker(input_dir='input/parsed', output_dir='input/checked')
results = checker.process_parsed_tracks()
```

**Input:** JSON files from step1
**Output:** JSON with availability info for each source

#### Step 3: Approval (`step3_approval.py`)
Interactive workflow for reviewing and approving tracks.

```python
from step3_approval import ApprovalWorkflow

workflow = ApprovalWorkflow(input_file='input/checked/all_tracks_checked.json',
                            output_dir='input/approved')
workflow.load_tracks()
workflow.interactive_approval()
# Or: workflow.bulk_approve_by_threshold(min_sources=3)
workflow.create_download_list()
```

**Modes:**
- Interactive: Review each track (approve/reject/skip)
- Bulk: Auto-approve based on availability threshold

#### Step 4: Download Manager (`step4_download_manager.py`)
Coordinates downloads and tracks progress.

```python
from step4_download_manager import DownloadManager

manager = DownloadManager(approved_tracks_file='input/approved/approved_tracks.json',
                          downloads_dir='downloads',
                          logs_dir='logs')
manager.load_approved_tracks()
summary = manager.download_all(max_retries=3)
```

**Features:**
- SHA256 checksums for verification
- Progress tracking
- Failure logging and retry logic

#### Step 5: MIK Reader (`step5_mik_reader.py`)
Parses Mixed In Key analysis and enriches track data.

```python
from step5_mik_reader import MIKReader

reader = MIKReader(mik_output_dir='mik-output', output_dir='input/enriched')
enriched = reader.enrich_tracks(tracks)

# Find compatible tracks for mixing
compatible = reader.get_key_compatible_tracks(track, all_tracks, distance=1)
```

**Features:**
- CSV and XML parsing
- Camelot to standard key conversion
- Energy level classification
- Mix compatibility detection

#### Step 6: Rekordbox XML (`step6_rekordbox_xml.py`)
Generates Rekordbox-compatible XML library files.

```python
from step6_rekordbox_xml import RekordboxLibraryBuilder

builder = RekordboxLibraryBuilder(output_dir='rekordbox')
summary = builder.build_library(tracks)
```

**Output:** rekordbox_library.xml (Rekordbox 6.0.0 compatible)

### Source Integrations

#### Base Class (`sources/base.py`)
Abstract base class defining the source interface.

```python
from sources.base import SourceBase

class CustomSource(SourceBase):
    def search(self, artist, title):
        # Search for track
        return TrackSearchResult(...)
    
    def check_availability(self, artist, title, bpm=None):
        # Check if track exists
        return True/False
    
    def download(self, artist, title, destination):
        # Download and return file path
        return Path(file)
```

#### Source Implementations

- **DJCitySource** (`sources/djcity.py`)
  - Quality options: 128-320 kbps
  - API endpoint: https://api.djcity.com/v1

- **BeatportSource** (`sources/beatport.py`)
  - Formats: MP3, WAV, AIFF
  - Lossless/FLAC support
  - Release date metadata

- **BPMSupremeSource** (`sources/bpmsupreme.py`)
  - BPM range search
  - Mood tagging
  - Key detection

- **TraxsourceSource** (`sources/traxsource.py`)
  - House music specialist
  - Genre/sub-genre filtering
  - Release date filtering

- **iTunesSource** (`sources/itunes.py`)
  - Public API (no auth)
  - Preview URLs
  - Store links

## Configuration

### config.json Example
```json
{
  "base_path": "/path/to/DJ-Pipeline",
  "sources": {
    "djcity": {
      "enabled": true,
      "api_key": "your_key_here"
    },
    "beatport": {
      "enabled": true,
      "api_key": "your_key_here"
    }
  },
  "pipeline": {
    "auto_download": false,
    "max_retries": 3,
    "log_level": "INFO"
  }
}
```

### Environment Variables
- `DJ_BASE_PATH`: Base pipeline directory
- `DJCITY_API_KEY`: DJCity API key
- `BEATPORT_API_KEY`: Beatport API key
- `BPMSUPREME_API_KEY`: BPM Supreme API key
- `TRAXSOURCE_API_KEY`: Traxsource API key

## Data Structures

### Track Dictionary
```python
track = {
    'artist': 'Artist Name',
    'title': 'Track Title',
    'bpm': 128.0,
    'key': '11A',  # Camelot notation
    'genre': 'House',
    'duration': '4:32',
    'source': 'djcity',
    'availability': {
        'djcity': True,
        'beatport': True,
        'bpmsupreme': False,
        'traxsource': True,
        'itunes': False
    },
    'mik_analysis': {
        'camelot_key': '11A',
        'energy_level': 'high',
        'energy_numeric': 6
    }
}
```

### TrackSearchResult
```python
result = TrackSearchResult(
    source_name='djcity',
    artist='Artist Name',
    title='Track Title',
    found=True,
    download_url='https://...',
    metadata={
        'price': 9.99,
        'format': 'mp3',
        'bpm': 128.0
    }
)
```

## API Examples

### Complete Pipeline Run
```python
from config_loader import ConfigLoader
from step1_csv_parser import CSVParser
from step2_source_checker import SourceChecker
from step3_approval import ApprovalWorkflow
from step4_download_manager import DownloadManager
from step5_mik_reader import MIKReader
from step6_rekordbox_xml import RekordboxLibraryBuilder

# Configuration
config = ConfigLoader().load()

# Step 1: Parse CSVs
parser = CSVParser(
    os.path.join(config['base_path'], 'input'),
    os.path.join(config['base_path'], 'input/parsed')
)
parser.process_all_csvs()

# Step 2: Check availability
checker = SourceChecker(
    os.path.join(config['base_path'], 'input/parsed'),
    os.path.join(config['base_path'], 'input/checked')
)
checker.process_parsed_tracks()

# Step 3: User approval
workflow = ApprovalWorkflow(
    os.path.join(config['base_path'], 'input/checked/all_tracks_checked.json'),
    os.path.join(config['base_path'], 'input/approved')
)
workflow.load_tracks()
workflow.interactive_approval()
workflow.create_download_list()

# Step 4: Download
manager = DownloadManager(
    os.path.join(config['base_path'], 'input/approved/approved_tracks.json'),
    os.path.join(config['base_path'], 'downloads'),
    os.path.join(config['base_path'], 'logs')
)
manager.load_approved_tracks()
manager.download_all()

# Step 5: Enrich with MIK data
reader = MIKReader(
    os.path.join(config['base_path'], 'mik-output'),
    os.path.join(config['base_path'], 'input/enriched')
)
# Load approved tracks and enrich
enriched = reader.enrich_tracks(approved_tracks)

# Step 6: Generate Rekordbox XML
builder = RekordboxLibraryBuilder(
    os.path.join(config['base_path'], 'rekordbox')
)
builder.build_library(enriched)
```

## Error Handling
All modules include:
- Try/except blocks for robustness
- Logging at multiple levels (INFO, WARNING, ERROR)
- Validation of inputs
- Graceful degradation when sources unavailable

## Testing
All modules have been:
- Syntax checked with Python 3.8+
- Verified for proper imports
- Tested with mock data structures
- Documented with docstrings

## Notes
- API keys are placeholders - fill in real credentials in config.json
- Download functions use mock implementations - integrate with real APIs as needed
- All file paths support both absolute and relative paths
- JSON output is human-readable (indented)

## Future Extensions
The modular design allows easy addition of:
- New DJ pool sources (inherit from SourceBase)
- Additional metadata parsers
- Custom approval workflows
- Export formats (Serato, Traktor, etc.)
