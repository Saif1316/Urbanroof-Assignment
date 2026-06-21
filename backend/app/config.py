"""
Application configuration, loaded from environment variables.
Copy .env.example to .env and fill in GROQ_API_KEY before running.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_api_base: str = "https://api.groq.com/openai/v1"

    nuextract_model_name: str = "numind/NuExtract-tiny-v1.5"
    use_local_extraction_model: bool = True  # set False to skip NuExtract and rely on Groq only

    upload_dir: str = "storage/uploads"
    extracted_images_dir: str = "storage/extracted_images"
    generated_reports_dir: str = "storage/generated_reports"

    cors_allow_origins: list[str] = ["http://localhost:5173"]

    # Thermal severity thresholds (degrees C delta vs surrounding baseline)
    thermal_high_severity_delta_c: float = 8.0
    thermal_medium_severity_delta_c: float = 4.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
