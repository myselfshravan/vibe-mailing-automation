"""
Configuration Loader for VibeMailing
Handles loading YAML configuration files and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Cache for loaded configurations
_config_cache: Dict[str, Any] = {}


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config or {}


def resolve_env_value(value: str) -> str:
    """
    Resolve environment variable references in config values.
    Handles "ENV:KEY" syntax.

    Args:
        value: Configuration value (may contain ENV:KEY)

    Returns:
        Resolved value

    Example:
        "ENV:GROQ_API_KEY" -> returns value of GROQ_API_KEY env var
    """
    if isinstance(value, str) and value.startswith("ENV:"):
        env_key = value[4:]  # Remove "ENV:" prefix
        env_value = os.environ.get(env_key)

        if env_value is None:
            raise ValueError(
                f"Environment variable '{env_key}' not found. "
                f"Please set it in your .env file or system environment."
            )

        return env_value

    return value


def resolve_env_values_recursive(config: Any) -> Any:
    """
    Recursively resolve environment variables in config.

    Args:
        config: Configuration value (dict, list, or primitive)

    Returns:
        Configuration with resolved environment variables
    """
    if isinstance(config, dict):
        return {k: resolve_env_values_recursive(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [resolve_env_values_recursive(item) for item in config]
    elif isinstance(config, str):
        return resolve_env_value(config)
    else:
        return config


def load_settings() -> Dict[str, Any]:
    """
    Load main settings configuration.

    Returns:
        Settings dictionary with resolved environment variables

    Raises:
        FileNotFoundError: If settings.yaml doesn't exist
    """
    cache_key = "settings"

    if cache_key not in _config_cache:
        config_path = "config/settings.yaml"
        config = load_yaml_config(config_path)
        config = resolve_env_values_recursive(config)
        _config_cache[cache_key] = config

    return _config_cache[cache_key]


def load_accounts() -> List[Dict[str, str]]:
    """
    Load Gmail accounts configuration.

    Returns:
        List of account dictionaries

    Raises:
        FileNotFoundError: If accounts.yaml doesn't exist
    """
    cache_key = "accounts"

    if cache_key not in _config_cache:
        config_path = "config/accounts.yaml"
        config = load_yaml_config(config_path)
        _config_cache[cache_key] = config.get('accounts', [])

    return _config_cache[cache_key]


def load_prompts() -> Dict[str, Any]:
    """
    Load email templates and LLM prompts configuration.

    Returns:
        Prompts configuration dictionary

    Raises:
        FileNotFoundError: If prompts.yaml doesn't exist
    """
    cache_key = "prompts"

    if cache_key not in _config_cache:
        config_path = "config/prompts.yaml"
        config = load_yaml_config(config_path)
        _config_cache[cache_key] = config

    return _config_cache[cache_key]


def get_env_variable(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable value.

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)


def clear_config_cache() -> None:
    """Clear configuration cache (useful for testing)"""
    global _config_cache
    _config_cache.clear()


def get_project_root() -> Path:
    """
    Get project root directory.

    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent


def get_absolute_path(relative_path: str) -> str:
    """
    Convert relative path to absolute path from project root.

    Args:
        relative_path: Relative path from project root

    Returns:
        Absolute path
    """
    if os.path.isabs(relative_path):
        return relative_path

    return str(get_project_root() / relative_path)
