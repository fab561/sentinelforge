from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sf_admin:changeme@localhost:5432/sentinelforge"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Wazuh
    WAZUH_INDEXER_URL: str = "http://wazuh-indexer:9200"
    WAZUH_MANAGER_URL: str = "https://wazuh-manager:55000"
    WAZUH_API_USER: str = "wazuh-wui"
    WAZUH_API_PASSWORD: str = "MyS3cr3tP4ssw0rd!"

    # App
    SECRET_KEY: str = "changeme-in-production"
    DEBUG: bool = True
    POLL_INTERVAL: int = 30  # seconds between Wazuh alert polls

    # Alert ID prefix
    ALERT_ID_PREFIX: str = "sf"

    # ── Module 2: Threat Intel API Keys ─────────────────────────────
    VIRUSTOTAL_API_KEY: str = ""   # https://www.virustotal.com/gui/my-apikey
    ABUSEIPDB_API_KEY: str = ""    # https://www.abuseipdb.com/account/api
    GREYNOISE_API_KEY: str = ""    # https://viz.greynoise.io/account/api-key
    OTX_API_KEY: str = ""          # https://otx.alienvault.com/api

    # Enrichment worker settings
    ENRICHMENT_CACHE_TTL: int = 3600   # seconds to cache provider responses
    ENRICHMENT_CONCURRENT_LIMIT: int = 5  # max concurrent provider API calls

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
