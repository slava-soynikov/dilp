from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_TTL_MIN: int
    REFRESH_TOKEN_TTL_DAYS: int
    PASSWORD_RESET_TOKEN_TTL_HOURS: int
    PASSWORD_MIN_LENGTH: int
    AUTH_RATE_LIMIT: str

    CMS_BASE_URL: str
    CMS_TOKEN: str
    CMS_TIMEOUT_S: float



settings = Settings()
