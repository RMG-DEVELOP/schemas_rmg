from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    # tg_token: str

    # postgres_dsn: PostgresDsn
    # rabbitmq_host: str
    # rabbitmq_port: int
    # rabbitmq_username: str
    # rabbitmq_password: str
        
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding="utf-8", extra="ignore")


settings = _Settings()
