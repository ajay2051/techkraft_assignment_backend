import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

MODE = os.environ.get("MODE", "development")


class Settings(BaseSettings):
    MODE: str
    database_hostname: str
    database_port: int
    database_username: str
    database_password: str
    database_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int


    REDIS_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

if MODE == 'development':
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'
elif MODE == 'production':
    broker_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    result_backend = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
else:
    broker_url = None
    result_backend = None

broker_connection_retry_on_startup = True
