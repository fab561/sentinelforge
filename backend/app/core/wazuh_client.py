import ssl

import httpx

from app.core.config import settings


class WazuhIndexerClient:
    """Queries Wazuh Indexer (OpenSearch) for alerts."""

    def __init__(self) -> None:
        self.base_url = settings.WAZUH_INDEXER_URL
        auth: httpx.BasicAuth | None = None
        if settings.WAZUH_INDEXER_USER:
            auth = httpx.BasicAuth(
                settings.WAZUH_INDEXER_USER,
                settings.WAZUH_INDEXER_PASSWORD,
            )
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            verify=False,
            timeout=30.0,
            auth=auth,
        )

    async def search_alerts(
        self, since: str | None = None, size: int = 100
    ) -> list[dict]:
        """Fetch alerts from wazuh-alerts-* index, optionally since a timestamp."""
        query: dict = {"size": size, "sort": [{"timestamp": {"order": "asc"}}]}

        if since:
            query["query"] = {"range": {"timestamp": {"gt": since}}}
        else:
            query["query"] = {"match_all": {}}

        resp = await self.client.post(
            "/wazuh-alerts-*/_search",
            json=query,
        )
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        return [{"_id": h["_id"], **h["_source"]} for h in hits]

    async def close(self) -> None:
        await self.client.aclose()


class WazuhManagerClient:
    """Communicates with Wazuh Manager REST API (port 55000)."""

    def __init__(self) -> None:
        self.base_url = settings.WAZUH_MANAGER_URL
        self.username = settings.WAZUH_API_USER
        self.password = settings.WAZUH_API_PASSWORD
        self._token: str | None = None
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            verify=False,
            timeout=30.0,
        )

    async def _authenticate(self) -> str:
        """Get JWT token from Wazuh Manager API."""
        resp = await self.client.post(
            "/security/user/authenticate",
            auth=(self.username, self.password),
        )
        resp.raise_for_status()
        self._token = resp.json().get("data", {}).get("token", resp.text)
        return self._token

    async def _get_headers(self) -> dict[str, str]:
        if not self._token:
            await self._authenticate()
        return {"Authorization": f"Bearer {self._token}"}

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an authenticated request, re-auth on 401."""
        headers = await self._get_headers()
        resp = await self.client.request(method, path, headers=headers, **kwargs)
        if resp.status_code == 401:
            await self._authenticate()
            headers = await self._get_headers()
            resp = await self.client.request(method, path, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def get_agents(self) -> list[dict]:
        """List all registered Wazuh agents."""
        data = await self._request("GET", "/agents", params={"limit": 500})
        return data.get("data", {}).get("affected_items", [])

    async def get_agent(self, agent_id: str) -> dict:
        data = await self._request("GET", f"/agents/{agent_id}")
        items = data.get("data", {}).get("affected_items", [])
        return items[0] if items else {}

    async def active_response(
        self, agent_id: str, command: str, arguments: list[str] | None = None
    ) -> dict:
        """Trigger active response on an agent."""
        body = {"command": command, "arguments": arguments or []}
        return await self._request(
            "PUT", f"/active-response/{agent_id}", json=body
        )

    async def close(self) -> None:
        await self.client.aclose()
