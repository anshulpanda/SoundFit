from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str
    genius_access_token: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
