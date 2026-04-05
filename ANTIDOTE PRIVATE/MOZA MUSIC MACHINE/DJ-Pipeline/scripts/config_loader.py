"""
Configuration Loader for DJ Pipeline
Loads configuration from JSON/YAML files and environment variables.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load pipeline configuration from files and environment."""

    DEFAULT_CONFIG = {
        'base_path': os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'input_dir': 'input',
        'output_dir': 'output',
        'downloads_dir': 'downloads',
        'logs_dir': 'logs',
        'mik_output_dir': 'mik-output',
        'rekordbox_dir': 'rekordbox',
        'sources': {
            'djcity': {
                'enabled': True,
                'api_endpoint': 'https://api.djcity.com',
                'timeout': 30
            },
            'beatport': {
                'enabled': True,
                'api_endpoint': 'https://api.beatport.com',
                'timeout': 30
            },
            'bpmsupreme': {
                'enabled': True,
                'api_endpoint': 'https://api.bpmsupreme.com',
                'timeout': 30
            },
            'traxsource': {
                'enabled': True,
                'api_endpoint': 'https://api.traxsource.com',
                'timeout': 30
            },
            'itunes': {
                'enabled': True,
                'api_endpoint': 'https://itunes.apple.com/search',
                'timeout': 30
            }
        },
        'pipeline': {
            'auto_download': False,
            'max_retries': 3,
            'retry_delay': 5,
            'log_level': 'INFO'
        },
        'mik': {
            'key_format': 'camelot',
            'parse_csv': True,
            'parse_xml': True
        },
        'rekordbox': {
            'version': '6.0.0',
            'format': 'xml',
            'company': 'Pioneer'
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.

        Args:
            config_path: Optional path to config file. If not provided, will search
                        for config.json, config.yaml in pipeline root
        """
        self.config_path = Path(config_path) if config_path else self._find_config_file()
        self.config = self.DEFAULT_CONFIG.copy()

    def _find_config_file(self) -> Optional[Path]:
        """
        Search for config file in standard locations.

        Returns:
            Path to config file or None
        """
        # Get pipeline root (parent of scripts directory)
        script_dir = Path(__file__).parent
        pipeline_root = script_dir.parent

        # Search for config files
        for filename in ['config.json', 'config.yaml', 'config.yml']:
            config_path = pipeline_root / filename
            if config_path.exists():
                logger.info(f"Found config file: {config_path}")
                return config_path

        # Check for .config.json (hidden)
        hidden_config = pipeline_root / '.config.json'
        if hidden_config.exists():
            logger.info(f"Found config file: {hidden_config}")
            return hidden_config

        logger.warning("No config file found, using defaults")
        return None

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file and environment.

        Returns:
            Configuration dictionary
        """
        if self.config_path and self.config_path.exists():
            self._load_from_file()

        self._override_from_env()

        logger.info(f"Configuration loaded: base_path={self.config.get('base_path')}")

        return self.config

    def _load_from_file(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                self._load_yaml()
            else:
                self._load_json()
        except Exception as e:
            logger.error(f"Error loading config file {self.config_path}: {e}")
            logger.info("Using default configuration")

    def _load_json(self) -> None:
        """Load JSON configuration file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            file_config = json.load(f)
            self.config.update(file_config)
            logger.info(f"Loaded config from {self.config_path}")

    def _load_yaml(self) -> None:
        """Load YAML configuration file."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                self.config.update(file_config)
                logger.info(f"Loaded config from {self.config_path}")

    def _override_from_env(self) -> None:
        """Override configuration with environment variables."""
        env_overrides = {
            'DJ_BASE_PATH': 'base_path',
            'DJ_LOG_LEVEL': ('pipeline', 'log_level'),
            'DJCITY_API_KEY': ('sources', 'djcity', 'api_key'),
            'BEATPORT_API_KEY': ('sources', 'beatport', 'api_key'),
            'BPMSUPREME_API_KEY': ('sources', 'bpmsupreme', 'api_key'),
            'TRAXSOURCE_API_KEY': ('sources', 'traxsource', 'api_key'),
        }

        for env_var, config_key in env_overrides.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_config(config_key, value)
                logger.info(f"Overriding {config_key} from environment variable {env_var}")

    def _set_nested_config(self, key_path, value: Any) -> None:
        """
        Set nested configuration value.

        Args:
            key_path: Key path (string or tuple of strings)
            value: Value to set
        """
        if isinstance(key_path, str):
            self.config[key_path] = value
        else:
            current = self.config
            for key in key_path[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[key_path[-1]] = value

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if configuration is valid
        """
        required_keys = ['base_path', 'sources', 'pipeline']

        for key in required_keys:
            if key not in self.config:
                logger.error(f"Missing required config key: {key}")
                return False

        # Check that base_path exists
        base_path = Path(self.config['base_path'])
        if not base_path.exists():
            logger.error(f"Base path does not exist: {base_path}")
            return False

        logger.info("Configuration validation passed")
        return True

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)

    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific DJ pool source.

        Args:
            source_name: Source name (djcity, beatport, etc)

        Returns:
            Source configuration dictionary
        """
        sources = self.config.get('sources', {})
        return sources.get(source_name, {})

    def is_source_enabled(self, source_name: str) -> bool:
        """
        Check if source is enabled.

        Args:
            source_name: Source name

        Returns:
            True if source is enabled
        """
        source_config = self.get_source_config(source_name)
        return source_config.get('enabled', True)

    def get_api_key(self, source_name: str) -> Optional[str]:
        """
        Get API key for a source.

        Args:
            source_name: Source name

        Returns:
            API key or None
        """
        source_config = self.get_source_config(source_name)
        return source_config.get('api_key')

    def save_config(self, output_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.

        Args:
            output_path: Path to save config file
        """
        if not output_path:
            output_path = self.config_path or Path(self.config['base_path']) / 'config.json'

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

        logger.info(f"Configuration saved to {output_path}")


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration dictionary.

    Returns:
        Default configuration
    """
    return ConfigLoader.DEFAULT_CONFIG.copy()


def main():
    """Test configuration loading."""
    loader = ConfigLoader()
    config = loader.load()

    if loader.validate():
        print("Configuration valid!")
        print(json.dumps(config, indent=2))
    else:
        print("Configuration validation failed!")


if __name__ == '__main__':
    main()
