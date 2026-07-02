#!/usr/bin/env python3
"""A tiny local web page to add papers to your Zotero library (with PDFs).

    python3 scripts/zotero_ui.py           # opens http://localhost:8000
    python3 scripts/zotero_ui.py --port 8123 --no-open

It lists every arXiv paper in the README with a checkbox and an "Add to Zotero"
button. Clicking it downloads each PDF and uploads it to your library via the
Zotero Web API (see scripts/zotero_lib.py for credential setup). Runs locally so
it can hold your API key and fetch the PDFs without cross-origin limits.
"""
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_site import arxiv_ref, load_cache, parse_readme  # noqa: E402
from zotero_lib import SETUP_HELP, ConfigError, load_config, push  # noqa: E402


def list_papers():
    cache = load_cache()
    out = []
    for p in parse_readme():
        aid, _ = arxiv_ref(p["links"])
        if not aid:
            continue
        title = (cache.get(aid) or {}).get("title") or p["title"]
        out.append({"id": aid, "title": title, "year": p["year"], "venue": p["venue"]})
    return out


PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Add to Zotero</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         margin: 0 auto; max-width: 820px; padding: 1.5rem; line-height: 1.45; }}
  h1 {{ font-size: 1.4rem; margin: 0 0 .3rem; }}
  .warn {{ background: #cc29361a; border: 1px solid #cc293655; border-radius: 8px;
           padding: .7rem .9rem; white-space: pre-wrap; font-size: .85rem; }}
  .ok {{ color: #15803d; }} .bad {{ color: #b91c1c; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: .35rem .2rem; border-bottom: 1px solid #8883; }}
  li label {{ cursor: pointer; }}
  .yr {{ color: #777; font-size: .85rem; margin-left: .3rem; }}
  .bar {{ position: sticky; top: 0; background: Canvas; padding: .8rem 0; border-bottom: 1px solid #8884; }}
  button {{ font-size: 1rem; padding: .5rem 1rem; border-radius: 8px; border: 1px solid #8886;
            background: #cc2936; color: #fff; cursor: pointer; }}
  button:disabled {{ opacity: .5; cursor: default; }}
  .res {{ font-size: .85rem; margin-left: 1.7rem; }}
</style></head>
<body>
  <h1>📚 Add papers to Zotero</h1>
  {banner}
  <div class="bar">
    <label><input type="checkbox" id="all"> select all</label>
    &nbsp;&nbsp;<button id="go">Add selected to Zotero</button>
    <span id="status"></span>
  </div>
  <ul id="list">{items}</ul>
<script>
const list = document.getElementById('list');
document.getElementById('all').onchange = e =>
  list.querySelectorAll('input[type=checkbox]').forEach(c => c.checked = e.target.checked);

document.getElementById('go').onclick = async () => {{
  const boxes = [...list.querySelectorAll('input[type=checkbox]:checked')];
  if (!boxes.length) return;
  const ids = boxes.map(b => b.value);
  const go = document.getElementById('go'), status = document.getElementById('status');
  go.disabled = true; status.textContent = ' working… (downloading PDFs + uploading)';
  boxes.forEach(b => {{ const r = document.getElementById('res-'+b.value); if (r) r.textContent = '…'; }});
  try {{
    const resp = await fetch('/add', {{method:'POST', headers:{{'Content-Type':'application/json'}},
                                       body: JSON.stringify({{ids}})}});
    const data = await resp.json();
    for (const r of data) {{
      const el = document.getElementById('res-'+r.id);
      if (el) {{ el.textContent = (r.ok ? '✓ ' : '✗ ') + r.msg; el.className = 'res ' + (r.ok ? 'ok' : 'bad'); }}
    }}
    status.textContent = ' done';
  }} catch (e) {{ status.textContent = ' error: ' + e; }}
  go.disabled = false;
}};
</script>
</body></html>
"""


def render_page():
    configured = load_config() is not None
    banner = ("" if configured else
              f'<div class="warn">{SETUP_HELP}</div>')
    items = "".join(
        f'<li><label><input type="checkbox" value="{p["id"]}"> {esc(p["title"])}'
        f'<span class="yr">{esc(p["venue"])} {esc(p["year"])}</span></label>'
        f'<div class="res" id="res-{p["id"]}"></div></li>'
        for p in list_papers()
    )
    return PAGE.format(banner=banner, items=items)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, render_page())
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/add":
            self._send(404, "not found", "text/plain")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            ids = json.loads(self.rfile.read(length) or b"{}").get("ids", [])
            results = push(ids)
        except ConfigError as e:
            results = [{"id": i, "ok": False, "msg": str(e)} for i in ids]
        except Exception as e:
            results = [{"id": i, "ok": False, "msg": f"{type(e).__name__}: {e}"} for i in (ids or [])]
        self._send(200, json.dumps(results), "application/json")

    def log_message(self, *_):  # quiet
        pass


def main(argv):
    port = 8000
    if "--port" in argv:
        port = int(argv[argv.index("--port") + 1])
    url = f"http://localhost:{port}"
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Add-to-Zotero UI running at {url}  (Ctrl-C to stop)")
    if "--no-open" not in argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main(sys.argv[1:])
