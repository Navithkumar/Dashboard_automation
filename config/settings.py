"""Application settings and configuration management."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration with environment variable override support."""

    # OrangeHRM demo configuration
    orangehrm_url: str = "https://opensource-demo.orangehrmlive.com"
    default_username: str = "Admin"
    default_password: str = "admin123"

    # Server settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # Automation defaults
    headless: bool = True
    browser_timeout_ms: int = 45000
    browser_channel: str = "chrome"

    # Base path computation
    base_dir: Path = Path(__file__).resolve().parent.parent
    output_dir_name: str = "outputs"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def output_dir(self) -> Path:
        path = self.base_dir / self.output_dir_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_dir(self) -> Path:
        path = self.output_dir / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def logs_dir(self) -> Path:
        path = self.output_dir / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def screenshots_dir(self) -> Path:
        path = self.output_dir / "screenshots"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
