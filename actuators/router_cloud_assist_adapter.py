"""RouterCloudAssistAdapter: IAM quota checks and sealed envelope formatting."""

from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from typing import Any, Dict, Optional


class RouterCloudAssistAdapterError(Exception):
    """Base error for RouterCloudAssistAdapter failures."""


class QuotaCheckError(RouterCloudAssistAdapterError):
    """Raised when an IAM quota check cannot be completed."""


class EnvelopeFormatError(RouterCloudAssistAdapterError):
    """Raised when a task envelope cannot be sealed."""


class RouterCloudAssistAdapter:
    """Adapter bridging router-side task processing with cloud IAM/quota
    services and providing a standard "sealed envelope" wire format for
    downstream task consumers.
    """

    DEFAULT_QUOTA_LIMIT = 1000
    SEALED_ENVELOPE_VERSION = "1.0"

    def __init__(
        self,
        iam_client: Optional[Any] = None,
        quota_store: Optional[Dict[str, Dict[str, int]]] = None,
        signing_key: Optional[bytes] = None,
    ) -> None:
        self._iam_client = iam_client
        self._quota_store: Dict[str, Dict[str, int]] = quota_store or {}
        self._signing_key = signing_key or b"router-cloud-assist-default-key"

    def check_iam_quota(self, project_id: str, service: str) -> dict:
        """Check remaining IAM-scoped quota for a service under a project.

        Returns a dict describing the current quota state:
            {
                "project_id": str,
                "service": str,
                "limit": int,
                "used": int,
                "remaining": int,
                "allowed": bool,
                "checked_at": int,
            }
        """
        if not project_id or not isinstance(project_id, str):
            raise QuotaCheckError("project_id must be a non-empty string")
        if not service or not isinstance(service, str):
            raise QuotaCheckError("service must be a non-empty string")

        try:
            usage = self._fetch_usage(project_id, service)
        except Exception as exc:
            raise QuotaCheckError(
                f"failed to fetch quota usage for {project_id}/{service}: {exc}"
            ) from exc

        limit = usage.get("limit", self.DEFAULT_QUOTA_LIMIT)
        used = usage.get("used", 0)
        remaining = max(limit - used, 0)

        return {
            "project_id": project_id,
            "service": service,
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "allowed": remaining > 0,
            "checked_at": int(time.time()),
        }

    def format_sealed_envelope(self, task_envelope: dict) -> dict:
        """Wrap a task envelope in a sealed, tamper-evident structure suitable
        for cross-boundary transport.

        Returns a dict of the form:
            {
                "version": str,
                "envelope_id": str,
                "sealed_at": int,
                "payload": <base64-encoded JSON of task_envelope>,
                "checksum": <hex digest over the encoded payload>,
            }
        """
        if not isinstance(task_envelope, dict):
            raise EnvelopeFormatError("task_envelope must be a dict")

        try:
            serialized = json.dumps(
                task_envelope, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise EnvelopeFormatError(
                f"task_envelope is not JSON-serializable: {exc}"
            ) from exc

        payload_b64 = base64.b64encode(serialized).decode("ascii")
        checksum = self._sign(serialized)

        return {
            "version": self.SEALED_ENVELOPE_VERSION,
            "envelope_id": str(uuid.uuid4()),
            "sealed_at": int(time.time()),
            "payload": payload_b64,
            "checksum": checksum,
        }

    def _fetch_usage(self, project_id: str, service: str) -> Dict[str, int]:
        if self._iam_client is not None:
            return self._iam_client.get_quota_usage(
                project_id=project_id, service=service
            )

        project_usage = self._quota_store.setdefault(project_id, {})
        used = project_usage.get(service, 0)
        return {"limit": self.DEFAULT_QUOTA_LIMIT, "used": used}

    def _sign(self, data: bytes) -> str:
        return hashlib.sha256(self._signing_key + data).hexdigest()
