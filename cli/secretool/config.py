"""
Configuration management for the CLI tool.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class CLIConfig(BaseModel):
    """CLI configuration settings"""
    
    # API settings
    api_base_url: str = "http://localhost:8088"
    api_timeout: int = 30
    
    # Default settings
    default_project: Optional[str] = None
    default_output_dir: str = "."
    
    # File settings
    env_file_name: str = ".env"
    
    # Display settings
    verbose: bool = False
    quiet: bool = False


def get_config() -> CLIConfig:
    """Get CLI configuration from environment variables and defaults"""
    
    return CLIConfig(
        api_base_url=os.getenv("LSEC_API_URL", "http://localhost:8088"),
        api_timeout=int(os.getenv("LSEC_API_TIMEOUT", "30")),
        default_project=os.getenv("LSEC_DEFAULT_PROJECT"),
        default_output_dir=os.getenv("LSEC_OUTPUT_DIR", "."),
        env_file_name=os.getenv("LSEC_ENV_FILE", ".env"),
        verbose=os.getenv("LSEC_VERBOSE", "false").lower() == "true",
        quiet=os.getenv("LSEC_QUIET", "false").lower() == "true"
    )


def get_config_file_path() -> Path:
    """Get the path to the CLI configuration file"""
    config_dir = Path.home() / ".config" / "lsec"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json" 