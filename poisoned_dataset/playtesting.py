"""Credential-free playtest records and a retryable GitHub archive writer."""

from base64 import b64encode
from dataclasses import dataclass, field
from hashlib import sha1
import json
import re
from threading import Lock, Thread
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

BRANCH = "play-testing"
DEFAULT_REPOSITORY = "haydn-s/poisoned-dataset-game"


def target_directory(value):
    """Limit archive writes to an ordinary subdirectory, never repository metadata."""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", value):
        raise ValueError("Use an archive directory such as playtests or results/playtests.")
    return value


def game_record(state):
    """A public archive snapshot: no unrevealed truth, attack, seed, or credentials."""
    record = {k: state[k] for k in ("version", "match_id", "code", "created_at", "revision", "phase", "edition")}
    record["schema_version"] = 1
    record["players"] = {seat: p["name"] for seat, p in state["players"].items()}
    record["budgets"] = {"flips": 4, "audits": 4}
    record["events"] = state["events"]
    record["rounds"] = []
    for r in state["rounds"]:
        public = {k: r[k] for k in ("number", "attacker", "defender", "deck", "cards", "started_at")}
        if "supplied" in r:
            public.update({k: r[k] for k in ("labels", "audits", "attack_rule", "attack_committed_at")})
        if "result" in r:
            public.update({k: r[k] for k in ("truth", "clean", "flips", "supplied", "result", "finished_at")})
        record["rounds"].append(public)
    for key in ("started_at", "finished_at"):
        if key in state:
            record[key] = state[key]
    if state["phase"] == "complete":
        record["seed"] = state["seed"]
    return record


@dataclass(frozen=True)
class ArchiveConfig:
    repository: str = DEFAULT_REPOSITORY
    directory: str = "playtests"
    token: str = field(default="", repr=False)

    def __post_init__(self):
        target_directory(self.directory)
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repository):
            raise ValueError("Use a GitHub repository in owner/repository format.")


class ArchiveError(Exception):
    """A safe operator message, with no token or response body."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHubArchive:
    def __init__(self, config, opener=None):
        self.config = config
        self.opener = opener or build_opener(_NoRedirect()).open

    def _request(self, method, path, data=None):
        request = Request(f"https://api.github.com/repos/{self.config.repository}/{path}",
                          data=json.dumps(data).encode() if data is not None else None,
                          method=method, headers={"Authorization": f"Bearer {self.config.token}",
                                                  "Accept": "application/vnd.github+json",
                                                  "Content-Type": "application/json",
                                                  "X-GitHub-Api-Version": "2022-11-28"})
        # Do not follow redirects with a bearer token. A renamed repository must
        # be corrected in configuration rather than redirecting credentials.
        try:
            with self.opener(request, timeout=10) as response:
                if response.geturl() != request.full_url:
                    raise ArchiveError("The repository moved. Update the archive repository setting.")
                return json.load(response)
        except HTTPError:
            raise
        except (URLError, OSError, ValueError):
            raise ArchiveError("GitHub is unreachable. The saved records will be retried.") from None

    def write(self, path, payload):
        if not path.startswith(self.config.directory + "/") or ".." in path.split("/"):
            raise ArchiveError("Archive path is outside the configured directory.")
        # Git blob SHA lets a retry after a lost response succeed without a
        # duplicate commit. All writes name the data branch explicitly.
        content = payload.encode()
        expected = sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        endpoint = "contents/" + quote(path, safe="/")
        for _ in range(3):
            try:
                try:
                    current = self._request("GET", endpoint + f"?ref={BRANCH}")
                except HTTPError as exc:
                    if exc.code != 404:
                        raise
                    current = {}
                if current.get("sha") == expected:
                    return
                data = {"message": f"Save playtest {path.split('/')[-2]}",
                        "branch": BRANCH, "content": b64encode(content).decode()}
                if "sha" in current:
                    data["sha"] = current["sha"]
                self._request("PUT", endpoint, data)
                return
            except HTTPError as exc:
                if exc.code in (409, 422):
                    continue  # Another file may have advanced this branch.
                advice = {401: "Check the archive token.", 403: "Check token permissions or GitHub rate limits.",
                          404: "Check the repository and play-testing branch."}.get(exc.code, "Retry later.")
                raise ArchiveError(f"GitHub HTTP {exc.code}. {advice}") from None
        raise ArchiveError("GitHub had concurrent updates. The saved record will be retried.")


class ArchiveSync:
    """One background writer per app process; a failed upload never blocks play."""

    def __init__(self, store, config, writer=None):
        self.store, self.config = store, config
        self.writer = writer or GitHubArchive(config)
        self.lock = Lock()

    def flush(self):
        if not self.config.token or not self.lock.acquire(blocking=False):
            return
        try:
            for item in self.store.pending_uploads():
                try:
                    self.writer.write(item["path"], item["payload"])
                except ArchiveError as exc:
                    self.store.upload_failed(item, str(exc))
                else:
                    self.store.upload_succeeded(item)
        finally:
            self.lock.release()

    def kick(self):
        if self.config.token and not self.lock.locked():
            Thread(target=self.flush, name="playtest-archive", daemon=True).start()
