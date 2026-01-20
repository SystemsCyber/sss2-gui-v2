"""Application configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Serial port configuration
    SSS2_SERIAL_PORT: str = "/dev/tty.usbmodem40768801"  # Mac default
    SSS2_BAUDRATE: int = 115200
    
    # Override serial port from environment
    # Default on Mac: /dev/tty.usbmodem40768801
    # Allow override by env var SSS2_SERIAL_PORT
    
    # Store paths
    BASE_DIR: Path = Path(__file__).parent.parent
    STORE_DIR: Path = BASE_DIR / "store" / "data"
    CATALOG_FILE: str = "peripheral_catalog.json"
    STATE_FILE: str = "current_device_state.json"
    SNAPSHOTS_DIR: str = "snapshots"
    
    # Application version
    VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
