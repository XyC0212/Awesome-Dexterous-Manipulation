#!/usr/bin/env python3
"""Push papers into a Zotero library, with their arXiv PDF attached.

This is the shared engine behind two front-ends:
  * the add-paper skill (auto-push a newly added paper), and
  * scripts/zotero_ui.py (a local web page with an "Add to Zotero" button).

Why a local helper instead of a button on the public site? A web page can't
fetch the arXiv PDF bytes cross-origin (CORS) nor hold your credentials, so it
can only ever store metadata. This runs locally: it downloads the PDF
server-side and uploads the real file into your library via the Zotero Web API.

Credentials (both required) are read from, in order:
  1. env vars   ZOTERO_API_KEY, ZOTERO_LIBRARY_ID, [ZOTERO_LIBRARY_TYPE=user]
  2. scripts/zotero_secrets.json   {"api_key","library_id","library_type"}
Get them at https://www.zotero.org/settings/keys (create a key with write
access; the numeric "userID" shown there is your library_id).

CLI:
  python3 scripts/zotero_lib.py 2607.00033 https://arxiv.org/abs/2606.17055
  python3 scripts/zotero_lib.py 2607.00033 --dry-run      # no writes; just check
  python3 scripts/zotero_lib.py 2607.00033 --best-effort  # never exit non-zero
"""
import json
import os
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_site import ARXIV_RE, fetch_arxiv_meta, load_cache  # noqa: E402

SCRIPTS = Path(__file__).resolve().parent
SECRETS = SCRIPTS / "zotero_secrets.json"
UA = "awesome-dexman-zotero/1.0"

SETUP_HELP = (
    "Zotero is not configured. Set env vars ZOTERO_API_KEY and ZOTERO_LIBRARY_ID,\n"
    f"or create {SECRETS} :\n"
    '  {\n    "api_key": "<key with write access>",\n'
    '    "library_id": "<your numeric userID>",\n    "library_type": "user"\n  }\n'
    "Both come from https://www.zotero.org/settings/keys\n"
    "Also install the client:  pip install pyzotero"
)


class ConfigError(RuntimeError):
    pass


def load_config():
    """Return {api_key, library_id, library_type} or None if not configured."""
    api_key = os.environ.get("ZOTERO_API_KEY")
    library_id = os.environ.get("ZOTERO_LIBRARY_ID")
    library_type = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")
    if (not api_key or not library_id) and SECRETS.exists():
        data = json.loads(SECRETS.read_text(encoding="utf-8"))
        api_key = api_key or data.get("api_key")
        library_id = library_id or data.get("library_id")
        library_type = data.get("library_type", library_type)
    if not api_key or not library_id:
        return None
    return {"api_key": api_key, "library_id": str(library_id), "library_type": library_type}


def extract_id(token):
    """Accept a bare arXiv id or any arxiv.org URL and return the id."""
    m = ARXIV_RE.search(token)
    return m.group(1) if m else token.strip()


def split_name(name):
    parts = name.split()
    if len(parts) < 2:  # single token -> store as a one-field name
        return {"creatorType": "author", "name": name}
    return {"creatorType": "author", "firstName": " ".join(parts[:-1]), "lastName": parts[-1]}


def build_item(arxiv_id, meta):
    """A Zotero 'preprint' item dict built from arXiv metadata."""
    meta = meta or {}
    item = {
        "itemType": "preprint",
        "title": meta.get("title", ""),
        "creators": [split_name(a) for a in meta.get("authors", [])],
        "abstractNote": meta.get("abstract", ""),
        "repository": "arXiv",
        "archiveID": f"arXiv:{arxiv_id}",
        "date": meta.get("year", ""),
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "libraryCatalog": "arXiv.org",
        "extra": f"arXiv:{arxiv_id}",
        "tags": [],
        "collections": [],
        "relations": {},
    }
    if meta.get("doi"):
        item["DOI"] = meta["doi"]
    return item


def download_pdf(arxiv_id, dest_dir=None):
    dest_dir = Path(dest_dir or tempfile.mkdtemp(prefix="dexman-zotero-"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{arxiv_id}.pdf"
    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        shutil.copyfileobj(r, f)
    return str(path)


def _created_key(resp):
    if resp.get("success"):
        return list(resp["success"].values())[0]
    if resp.get("successful"):
        return list(resp["successful"].values())[0]["key"]
    raise RuntimeError(f"item not created: {resp.get('failed')}")


def find_existing(zot, arxiv_id):
    """Best-effort dedupe: return an existing item key for this arXiv id, or None."""
    try:
        hits = zot.items(q=arxiv_id, qmode="everything", limit=10)
    except Exception:
        return None
    for it in hits:
        d = it.get("data", {})
        blob = " ".join(str(d.get(k, "")) for k in ("archiveID", "extra", "url", "DOI")).lower()
        if arxiv_id.lower() in blob:
            return d.get("key")
    return None


def push(arxiv_ids, dry_run=False):
    """Add each arXiv id to Zotero with its PDF. Returns a list of result dicts:
    {id, ok, title, msg, skipped?}. Never raises per-item; raises ConfigError
    only when credentials are missing and dry_run is False."""
    ids = [extract_id(x) for x in arxiv_ids]
    cache = load_cache()
    zot = None
    if not dry_run:
        cfg = load_config()
        if not cfg:
            raise ConfigError(SETUP_HELP)
        try:
            from pyzotero import zotero
        except ImportError:
            raise ConfigError("pyzotero is not installed. Run:  pip install pyzotero")
        zot = zotero.Zotero(cfg["library_id"], cfg["library_type"], cfg["api_key"])

    results = []
    for aid in ids:
        r = {"id": aid, "ok": False, "title": "", "msg": ""}
        try:
            meta = cache.get(aid) or fetch_arxiv_meta(aid)
            if not meta:
                r["msg"] = "could not fetch arXiv metadata"
                results.append(r)
                continue
            r["title"] = meta.get("title", "")
            if dry_run:
                pdf = download_pdf(aid)
                size = Path(pdf).stat().st_size
                r.update(ok=True, msg=f"dry-run OK: item built, PDF downloaded ({size} bytes)")
                results.append(r)
                continue
            existing = find_existing(zot, aid)
            if existing:
                r.update(ok=True, skipped=True, msg=f"already in library ({existing})")
                results.append(r)
                continue
            key = _created_key(zot.create_items([build_item(aid, meta)]))
            pdf = download_pdf(aid)
            att = zot.attachment_simple([pdf], key)
            if att.get("failure"):
                r.update(ok=True, msg=f"item added ({key}) but PDF upload failed: {att['failure']}")
            else:
                r.update(ok=True, msg=f"added + PDF attached ({key})")
            results.append(r)
        except Exception as e:  # keep going for the rest
            r["msg"] = f"{type(e).__name__}: {e}"
            results.append(r)
    return results


def _cli(argv):
    flags = {a for a in argv if a.startswith("-")}
    ids = [a for a in argv if not a.startswith("-")]
    best_effort = "--best-effort" in flags
    dry_run = "--dry-run" in flags
    if not ids:
        print("usage: zotero_lib.py <arxiv-id-or-url> [...] [--dry-run] [--best-effort]")
        return 2
    try:
        results = push(ids, dry_run=dry_run)
    except ConfigError as e:
        print(e, file=sys.stderr)
        return 0 if best_effort else 1
    for r in results:
        mark = "✓" if r["ok"] else "✗"
        label = r["title"] or r["id"]
        print(f"  {mark} {r['id']}  {label[:70]}\n      {r['msg']}")
    all_ok = all(r["ok"] for r in results)
    return 0 if (all_ok or best_effort) else 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
