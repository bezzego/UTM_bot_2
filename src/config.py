from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    bot_token: str
    clc_api_key: str
    bot_access_password: str = Field(alias="BOT_ACCESS_PASSWORD")
    database_path: str = Field(default="data/bot_state.sqlite3")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
