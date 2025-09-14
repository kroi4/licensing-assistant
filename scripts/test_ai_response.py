#!/usr/bin/env python
"""
Quick tester for the Licensing Assistant API to view the AI report.

Usage examples:
  python scripts/test_ai_response.py \
      --area 50 --seats 7 --features gas,meat

  LIC_ASSISTANT_API_URL=http://localhost:8000 python scripts/test_ai_response.py

Notes:
- This script does NOT require your OpenAI key; it calls your local API only.
- Ensure the backend server is running and has access to OPENAI_API_KEY.
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import urllib.request
import urllib.error


def build_payload(area: float, seats: int, features_csv: str) -> dict:
    """Construct the request payload for /api/assess.

    Args:
        area: Business area in square meters.
        seats: Number of seats.
        features_csv: Comma-separated features string (e.g., "gas,meat").

    Returns:
        A dict ready to be sent as JSON.
    """
    features = [f.strip() for f in (features_csv or "").split(",") if f.strip()]
    return {
        "area": float(area),
        "seats": int(seats),
        "features": features,
    }


def post_json(url: str, data: dict) -> tuple[int, dict | str]:
    """Send a JSON POST request using urllib (no external deps).

    Returns (status_code, parsed_json_or_text)
    """
    req = urllib.request.Request(
        url=url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.getcode(), json.loads(body)
            except json.JSONDecodeError:
                return resp.getcode(), body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, body
    except urllib.error.URLError as e:
        return 0, f"Connection error: {e}"


def pretty_print_ai_result(status: int, payload: dict, result: dict | str) -> None:
    """Print a concise, helpful view of the API result for debugging."""
    print("== Request ==")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()

    print(f"== Response Status ==\n{status}")

    if isinstance(result, str):
        # Non-JSON response
        print("\n== Raw Response Body ==")
        print(result)
        return

    # JSON response
    print("\n== Full JSON ==")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # If server enforces AI-only, success response includes ai_report
    ai_report = result.get("ai_report") if isinstance(result, dict) else None
    if ai_report:
        print("\n== AI Report Summary ==")
        summary = ai_report.get("summary", {})
        print(json.dumps(summary, ensure_ascii=False, indent=2))

        actions = ai_report.get("actions", [])
        print(f"\nActions: {len(actions)} item(s)")
        if actions:
            print("- First action:")
            print(json.dumps(actions[0], ensure_ascii=False, indent=2))

        risks = ai_report.get("potential_risks", [])
        print(f"\nRisks: {len(risks)} item(s)")

        tips = ai_report.get("tips", [])
        print(f"Tips: {len(tips)} item(s)")

    # Error path (e.g., 503 when AI is unavailable)
    if status != 200:
        print("\n== Error Message ==")
        err = result.get("error") if isinstance(result, dict) else None
        print(err or "Unknown error")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test /api/assess AI response")
    parser.add_argument("--area", type=float, default=100.0, help="Business area (m^2)")
    parser.add_argument("--seats", type=int, default=30, help="Number of seats")
    parser.add_argument(
        "--features",
        type=str,
        default="gas,meat",
        help='Comma-separated features (e.g., "gas,delivery,alcohol,hood,meat")',
    )
    parser.add_argument(
        "--api",
        type=str,
        default=os.getenv("LIC_ASSISTANT_API_URL", "http://localhost:8000"),
        help="Base API URL (default: http://localhost:8000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    payload = build_payload(args.area, args.seats, args.features)
    url = args.api.rstrip("/") + "/api/assess"

    status, result = post_json(url, payload)
    pretty_print_ai_result(status, payload, result)

    # Exit code: 0 on success (200 with ai_report), 1 otherwise
    if isinstance(result, dict) and status == 200 and result.get("ai_report"):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


