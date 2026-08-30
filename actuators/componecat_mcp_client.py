"""Client wrapper for interacting with a remote Componecat MCP (Model Context
Protocol) server over HTTP/JSON-RPC."""

from __future__ import annotations

import time
import uuid
from typing import Any

import requests


class ComponecatMCPClient:
    """Thin HTTP client for a Componecat-hosted MCP server."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = session or requests.Session()

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _rpc(self, method: str, params: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
        }
        response = self.session.post(
            f"{self.base_url}/mcp",
            json=payload,
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        body = response.json()
        if "error" in body:
            error = body["error"]
            raise RuntimeError(
                f"MCP error {error.get('code')}: {error.get('message')}"
            )
        return body.get("result", {})

    def list_remote_tools(self, organization_id: str) -> list:
        """Return the list of tools exposed by the remote MCP server for an organization."""
        result = self._rpc("tools/list", {"organization_id": organization_id})
        return result.get("tools", [])

    def execute_remote_tool(self, tool_name: str, arguments: dict) -> dict:
        """Invoke a named tool on the remote MCP server with the given arguments."""
        result = self._rpc(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )
        return result

    def check_connection_health(self, endpoint_url: str) -> dict:
        """Check reachability and latency of an MCP endpoint."""
        started = time.monotonic()
        try:
            response = self.session.get(
                f"{endpoint_url.rstrip('/')}/health",
                headers=self._headers(),
                timeout=self.timeout,
            )
            latency_ms = (time.monotonic() - started) * 1000
            healthy = response.ok
            return {
                "endpoint_url": endpoint_url,
                "healthy": healthy,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "error": None if healthy else response.text,
            }
        except requests.RequestException as exc:
            latency_ms = (time.monotonic() - started) * 1000
            return {
                "endpoint_url": endpoint_url,
                "healthy": False,
                "status_code": None,
                "latency_ms": round(latency_ms, 2),
                "error": str(exc),
            }
