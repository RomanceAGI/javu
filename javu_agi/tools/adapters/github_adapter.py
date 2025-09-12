from __future__ import annotations
import os, requests
from typing import Dict, Any


class GitHubAdapter:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.repo = os.getenv("GITHUB_REPO", "")  # e.g. user/repo

    def create_issue(
        self, title: str, body: str = "", repo: str = ""
    ) -> Dict[str, Any]:
        if not self.token:
            return {"status": "error", "reason": "no_token"}
        rp = repo or self.repo
        if not rp:
            return {"status": "error", "reason": "no_repo"}
        url = f"https://api.github.com/repos/{rp}/issues"
        try:
            r = requests.post(
                url,
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github+json",
                },
                json={"title": title, "body": body},
                timeout=8,
            )
            return {
                "status": "ok" if r.status_code < 300 else "error",
                "code": r.status_code,
                "data": r.json(),
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
