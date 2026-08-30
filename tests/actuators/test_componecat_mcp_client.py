"""Unit tests for ComponecatMCPClient."""

from unittest.mock import MagicMock, patch
import pytest
import requests

from actuators.componecat_mcp_client import ComponecatMCPClient


class TestComponecatMCPClient:
    def test_init_and_headers(self):
        client = ComponecatMCPClient(base_url="https://app.componecat.ai/api", api_key="secret-key")
        headers = client._headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer secret-key"

    @patch("requests.Session.post")
    def test_list_remote_tools(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {"name": "componecat_search", "description": "Search remote capabilities"}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = ComponecatMCPClient(base_url="https://app.componecat.ai/api")
        tools = client.list_remote_tools(organization_id="org-123")
        assert len(tools) == 1
        assert tools[0]["name"] == "componecat_search"

    @patch("requests.Session.post")
    def test_execute_remote_tool(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"status": "SUCCESS", "output": "catalog data"}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        client = ComponecatMCPClient(base_url="https://app.componecat.ai/api")
        result = client.execute_remote_tool("componecat_search", {"query": "vertex"})
        assert result["status"] == "SUCCESS"

    @patch("requests.Session.get")
    def test_check_connection_health_healthy(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        client = ComponecatMCPClient(base_url="https://app.componecat.ai/api")
        health = client.check_connection_health("https://app.componecat.ai/api")
        assert health["healthy"] is True
        assert health["status_code"] == 200
        assert health["latency_ms"] >= 0

    @patch("requests.Session.get")
    def test_check_connection_health_unhealthy(self, mock_get):
        mock_get.side_effect = requests.RequestException("Connection refused")

        client = ComponecatMCPClient(base_url="https://app.componecat.ai/api")
        health = client.check_connection_health("https://app.componecat.ai/api")
        assert health["healthy"] is False
        assert "Connection refused" in health["error"]
