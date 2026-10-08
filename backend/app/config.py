from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    language: str = "fr"
    embedding_model_path: str = "data/cc.fr.300.vec"
    similarity_threshold: float = 0.35
    max_article_words: int = 500
    auto_reveal_common_words: bool = False
    use_lemmatization: bool = False
    database_url: str = "sqlite:///./game.db"
    
    class Config:
        env_file = ".env"


settings = Settings()
