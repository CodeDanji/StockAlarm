from __future__ import annotations

import json
import os
from typing import Any, Callable

import httpx

RUN_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

JOB_ENV_CONFIG = {
    "ingestor": ("INGESTOR_JOB_NAME", "ecoalarm-ingestor"),
    "evaluator": ("EVALUATOR_JOB_NAME", "ecoalarm-evaluator"),
    "digest": ("DIGEST_JOB_NAME", "ecoalarm-digest"),
}


def _default_token_provider() -> str:
    from google.auth import default
    from google.auth.transport.requests import Request

    credentials, _ = default(scopes=[RUN_SCOPE])
    credentials.refresh(Request())
    token = credentials.token
    if not token:
        raise ValueError("unable to obtain google access token")
    return token


class CloudRunJobDispatcher:
    def __init__(
        self,
        *,
        project_id: str | None = None,
        region: str | None = None,
        http_client: Any | None = None,
        token_provider: Callable[[], str] | None = None,
    ) -> None:
        self.project_id = (project_id or os.getenv("GCP_PROJECT_ID", "")).strip()
        self.region = (region or os.getenv("GCP_REGION", "asia-northeast3")).strip()
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID is not configured")

        self._http_client = http_client or httpx.Client(timeout=15.0)
        self._owns_http_client = http_client is None
        self._token_provider = token_provider or _default_token_provider

    def close(self) -> None:
        if self._owns_http_client:
            self._http_client.close()

    def run_job(self, *, job_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        token = self._token_provider()
        url = (
            f"https://run.googleapis.com/v2/projects/{self.project_id}"
            f"/locations/{self.region}/jobs/{job_name}:run"
        )
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        body = {
            "overrides": {
                "containerOverrides": [
                    {
                        "env": [
                            {
                                "name": "DISPATCH_PAYLOAD_JSON",
                                "value": payload_json,
                            }
                        ]
                    }
                ]
            }
        }
        response = self._http_client.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        response.raise_for_status()
        response_json = response.json()
        operation = response_json.get("name", "")
        return {"job_name": job_name, "operation": operation}


def run_named_worker_job(*, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized_key = job_key.strip().lower()
    if normalized_key not in JOB_ENV_CONFIG:
        raise ValueError("unknown worker job key")

    env_name, default_job_name = JOB_ENV_CONFIG[normalized_key]
    job_name = os.getenv(env_name, default_job_name).strip()
    if not job_name:
        raise ValueError(f"{env_name} is not configured")

    dispatcher = CloudRunJobDispatcher()
    try:
        return dispatcher.run_job(job_name=job_name, payload=payload)
    finally:
        dispatcher.close()
