from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
load_dotenv()


class Config(BaseSettings):
    """It will automatically read environment variables into fields.
    """

    AIML_API_KEY: str = os.getenv("AIML_API_KEY","")
    MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER","")
    MODEL_NAME: str = os.getenv("MODEL_NAME","")
    MONGODB_URI: str = os.getenv("MONGODB_URI","")
    POSTGRESQL_URI: str = os.getenv("POSTGRESQL_URI","")

config = Config()
