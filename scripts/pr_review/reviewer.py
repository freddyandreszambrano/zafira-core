#!/usr/bin/env python3
"""AI PR reviewer for GitHub. Stdlib-only.

Lee el diff del PR, lo manda a un LLM (Gemini/OpenAI/OpenAI-compatible)
y postea comentarios inline + un summary con marker para evitar duplicados.

Inspirado en hey-support/scripts/mr_review/reviewer.py (GitLab edition).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

GITHUB_API = "https://api.github.com"
MARKER_PREFIX = "<!-- ai-review-marker: head_sha="
SEVERITIES = {"critical": "🔴", "improvement": "🟡", "suggestion": "🟢"}


# ── HTTP helpers ───────────────────────────────────────────────────────


def http(method: str, url: str, headers: dict, body: Any = None) -> dict:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code} on {method} {url}: {e.read().decode()}\n")
        raise


# ── GitHub API ─────────────────────────────────────────────────────────


def gh_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "zafira-pr-reviewer",
    }


def get_pr(repo: str, number: int, token: str) -> dict:
    return http("GET", f"{GITHUB_API}/repos/{repo}/pulls/{number}", gh_headers(token))


def get_pr_diff(repo: str, number: int, token: str) -> str:
    headers = {**gh_headers(token), "Accept": "application/vnd.github.v3.diff"}
    req = urllib.request.Request(
        f"{GITHUB_API}/repos/{repo}/pulls/{number}",
        headers=headers,
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def list_pr_comments(repo: str, number: int, token: str) -> list:
    return http("GET", f"{GITHUB_API}/repos/{repo}/issues/{number}/comments", gh_headers(token)) or []


def post_issue_comment(repo: str, number: int, body: str, token: str) -> None:
    http(
        "POST",
        f"{GITHUB_API}/repos/{repo}/issues/{number}/comments",
        gh_headers(token),
        {"body": body},
    )


def post_review(repo: str, number: int, commit_id: str, body: str, comments: list, token: str) -> None:
    payload = {"commit_id": commit_id, "body": body, "event": "COMMENT", "comments": comments}
    http(
        "POST",
        f"{GITHUB_API}/repos/{repo}/pulls/{number}/reviews",
        gh_headers(token),
        payload,
    )


# ── LLM providers ──────────────────────────────────────────────────────


def call_gemini(prompt: str, key: str, model: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    resp = http("POST", url, {}, payload)
    return resp["candidates"][0]["content"]["parts"][0]["text"]


def call_openai_compat(prompt: str, key: str, model: str, base_url: str) -> str:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    resp = http("POST", f"{base_url}/chat/completions", {"Authorization": f"Bearer {key}"}, payload)
    return resp["choices"][0]["message"]["content"]


def call_llm(prompt: str) -> str:
    provider = os.environ["AI_PROVIDER"].lower()
    key = os.environ["AI_API_KEY"]
    if provider == "gemini":
        return call_gemini(prompt, key, os.environ.get("AI_MODEL", "gemini-1.5-flash"))
    if provider == "openai":
        return call_openai_compat(prompt, key, os.environ.get("AI_MODEL", "gpt-4o-mini"), "https://api.openai.com/v1")
    if provider == "custom":
        return call_openai_compat(
            prompt, key, os.environ["AI_MODEL"], os.environ["AI_BASE_URL"].rstrip("/")
        )
    raise SystemExit(f"AI_PROVIDER inválido: {provider}")


# ── Review logic ───────────────────────────────────────────────────────


PROMPT_TEMPLATE = """Eres revisor de código senior en un proyecto Django (ZAFIRA-CORE).
Convenciones del proyecto:
- CRUD: 4 views explícitas con post() inline (List/Create/Update/Delete), action en if/elif.
- PermissionMixin obligatorio en toda view CRUD.
- Templates y JS app-local por entidad; nunca JS inline en templates.
- Modelos requieren to_json().
- Modularizar si un archivo pasa de ~200 líneas.

Revisa este diff de un PR y devuelve SOLO un JSON válido con esta forma:
{{
  "summary": "1-3 frases sobre el cambio global",
  "findings": [
    {{
      "path": "ruta/relativa.py",
      "line": 42,
      "severity": "critical|improvement|suggestion",
      "message": "qué está mal y cómo arreglarlo"
    }}
  ]
}}

Reglas:
- Máximo 8 findings, ordenados por severidad.
- Solo comenta LÍNEAS QUE APARECEN COMO AÑADIDAS (+) en el diff.
- Si no hay nada que comentar, devuelve findings: [].

Diff:
```
{diff}
```
"""


def already_reviewed(comments: list, head_sha: str) -> bool:
    marker = f"{MARKER_PREFIX}{head_sha}"
    return any(marker in (c.get("body") or "") for c in comments)


def truncate(s: str, n: int) -> str:
    if len(s) <= n:
        return s
    return s[:n] + f"\n\n[diff truncado: {len(s) - n} chars omitidos]"


def parse_llm_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE)
    return json.loads(raw)


def main() -> int:
    repo = os.environ["GITHUB_REPOSITORY"]
    pr_number = int(os.environ["PR_NUMBER"])
    gh_token = os.environ["GITHUB_TOKEN"]
    max_chars = int(os.environ.get("MAX_DIFF_CHARS", "40000"))

    pr = get_pr(repo, pr_number, gh_token)
    head_sha = pr["head"]["sha"]

    if already_reviewed(list_pr_comments(repo, pr_number, gh_token), head_sha):
        print(f"PR #{pr_number} ya revisado para {head_sha[:8]} — skip.")
        return 0

    diff = truncate(get_pr_diff(repo, pr_number, gh_token), max_chars)
    raw = call_llm(PROMPT_TEMPLATE.format(diff=diff))
    review = parse_llm_json(raw)

    findings = review.get("findings", []) or []
    summary = review.get("summary", "Sin observaciones.")

    inline = []
    for f in findings[:8]:
        sev = f.get("severity", "suggestion")
        icon = SEVERITIES.get(sev, "🟢")
        body = f"{icon} **{sev}** — {f.get('message', '')}"
        if f.get("path") and f.get("line"):
            inline.append({"path": f["path"], "line": int(f["line"]), "side": "RIGHT", "body": body})

    marker = f"{MARKER_PREFIX}{head_sha} -->"
    summary_body = f"🤖 **AI Review**\n\n{summary}\n\n{marker}"

    if inline:
        post_review(repo, pr_number, head_sha, summary_body, inline, gh_token)
    else:
        post_issue_comment(repo, pr_number, summary_body, gh_token)

    print(f"PR #{pr_number} revisado: {len(inline)} findings inline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
