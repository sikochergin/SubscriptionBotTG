from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    admin_ids: str
    group_chat_id: int

    timezone: str = "Europe/Moscow"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def admin_id_list(self) -> list[int]:
        return [int(user_id.strip()) for user_id in self.admin_ids.split(",") if user_id.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()