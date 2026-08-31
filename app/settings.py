from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # The Pi's wlan0 IP/hostname - what the browser uses to reach MediaMTX's HLS output.
    public_host: str = "127.0.0.1"
    mediamtx_hls_port: int = 8888
    app_port: int = 8000

    cameras_config_path: str = "config/cameras.yaml"

    # Optional HTTP Basic auth. Leave unset to disable.
    basic_auth_user: str | None = None
    basic_auth_pass: str | None = None


settings = Settings()
