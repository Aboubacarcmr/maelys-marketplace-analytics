"""Hook Airflow spécifique à l'API REST Marketplace (auth Bearer depuis Connection)."""
from __future__ import annotations

from airflow.sdk import BaseHook
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class MarketplaceAPIHook(BaseHook):
    conn_name_attr = "marketplace_conn_id"
    default_conn_name = "marketplace_api"
    conn_type = "http"
    hook_name = "Marketplace API"

    def __init__(self, marketplace_conn_id: str = "marketplace_api") -> None:
        super().__init__()
        self.marketplace_conn_id = marketplace_conn_id

    def _get_session(self) -> tuple[Session, str]:
        connection = self.get_connection(self.marketplace_conn_id)
        if not connection.password:
            raise ValueError("Token Bearer absent dans le mot de passe de la Connection")
        raw_host = connection.host or ""
        if raw_host.startswith(("http://", "https://")):
            base_url = raw_host.rstrip("/")
        else:
            scheme = connection.schema or "http"
            port = f":{connection.port}" if connection.port else ""
            base_url = f"{scheme}://{raw_host}{port}"
        session = Session()
        session.headers.update({"Authorization": f"Bearer {connection.password}"})
        retries = Retry(total=3, connect=3, read=3, backoff_factor=0.7,
                        status_forcelist=[429, 500, 502, 503, 504],
                        allowed_methods=frozenset(["GET"]))
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session, base_url

    def _get_list(self, endpoint: str, params: dict | None = None) -> list[dict]:
        session, base_url = self._get_session()
        try:
            response = session.get(f"{base_url}{endpoint}", params=params, timeout=(5, 30))
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise ValueError(f"Réponse API inattendue pour {endpoint}: liste JSON attendue")
            return data
        finally:
            session.close()

    def get_orders(self, day: str) -> list[dict]:
        return self._get_list("/orders", {"date": day})

    def get_sellers(self) -> list[dict]:
        return self._get_list("/sellers")

    def get_products(self) -> list[dict]:
        return self._get_list("/products")
