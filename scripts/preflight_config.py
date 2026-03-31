from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_ENV_KEYS = [
    "DATABASE_URL",
    "EODHD_API_KEY",
    "GOOGLE_CLIENT_ID",
    "JWT_SECRET",
    "GCP_PROJECT_ID",
    "INTERNAL_DISPATCH_TOKEN",
]

REQUIRED_TFVARS_KEYS = [
    "project_id",
    "api_image",
    "worker_image",
    "dispatcher_internal_token",
    "database_url",
    "eodhd_api_key",
    "google_client_ids",
    "jwt_secret",
]

PLACEHOLDER_PATTERNS = (
    "change-me",
    "replace-with",
    "your-gcp-project-id",
    "example.com",
    "us-docker.pkg.dev/cloudrun/container/hello",
    "<user>",
    "<password>",
    "<host>",
    "<db>",
)

TFVARS_LINE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$")


def _normalize_value(raw: str) -> str:
    value = raw.strip()
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        return value[1:-1].strip()
    return value


def _is_missing(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return True
    lowered = normalized.lower()
    return any(pattern in lowered for pattern in PLACEHOLDER_PATTERNS)


def parse_dotenv(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        result[key.strip()] = _normalize_value(value)
    return result


def parse_tfvars(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        matched = TFVARS_LINE.match(stripped)
        if not matched:
            continue
        key, raw_value = matched.groups()
        result[key] = _normalize_value(raw_value)
    return result


def find_missing(config: dict[str, str], required_keys: list[str]) -> list[str]:
    missing: list[str] = []
    for key in required_keys:
        if _is_missing(config.get(key, "")):
            missing.append(key)
    return missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate EcoAlarm config files before deployment")
    parser.add_argument("--env-file", default=".env", help="Path to .env file")
    parser.add_argument(
        "--tfvars-file",
        default="infra/terraform/terraform.tfvars",
        help="Path to terraform tfvars file",
    )
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    tfvars_path = Path(args.tfvars_file)

    if not env_path.exists():
        print(f"[ERROR] .env file not found: {env_path}")
        return 1
    if not tfvars_path.exists():
        print(f"[ERROR] terraform tfvars file not found: {tfvars_path}")
        return 1

    env_values = parse_dotenv(env_path)
    tfvars_values = parse_tfvars(tfvars_path)

    missing_env = find_missing(env_values, REQUIRED_ENV_KEYS)
    missing_tfvars = find_missing(tfvars_values, REQUIRED_TFVARS_KEYS)

    if missing_env:
        print("[ERROR] Missing or placeholder values in .env:")
        for key in missing_env:
            print(f"  - {key}")

    if missing_tfvars:
        print("[ERROR] Missing or placeholder values in terraform.tfvars:")
        for key in missing_tfvars:
            print(f"  - {key}")

    if missing_env or missing_tfvars:
        return 1

    print("[OK] Preflight config validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
