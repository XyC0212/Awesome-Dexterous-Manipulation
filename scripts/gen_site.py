#!/usr/bin/env python3
"""Generate docs/index.html (an interactive, filterable view) from the README table.

The README table is the single source of truth. Run this after editing it:

    python3 scripts/gen_site.py

Each paper gets an "Add to Zotero" icon that downloads a full RIS record. Author
and abstract metadata is fetched from the arXiv API at build time and cached in
scripts/zotero_cache.json (committed), so re-runs are offline-safe and only new
arXiv papers trigger a network request.

Then commit docs/index.html (and zotero_cache.json). Serve it with GitHub Pages
(Settings -> Pages -> deploy from branch -> /docs).
"""
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
OUT = ROOT / "docs" / "index.html"
CACHE = ROOT / "scripts" / "zotero_cache.json"

TAGS = ["RL", "IL", "WM", "HV", "Tac", "HW", "Tele"]
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
ARXIV_RE = re.compile(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", re.I)

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIVNS = "{http://arxiv.org/schemas/atom}"


def parse_links(cell):
    return [{"label": m.group(1), "url": m.group(2)} for m in LINK_RE.finditer(cell)]


def parse_readme():
    papers = []
    for line in README.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # cells: #, Title, Venue, Year, Affiliation, RL, IL, WM, HV, Tac, HW, Tele, Links
        if len(cells) < 13:
            continue
        num, title, venue, year, affiliation = cells[0], cells[1], cells[2], cells[3], cells[4]
        tag_cells = cells[5:12]
        tags = [TAGS[i] for i, c in enumerate(tag_cells) if "✅" in c]
        papers.append({
            "n": int(num),
            "title": title,
            "venue": venue,
            "year": year,
            "affiliation": affiliation,
            "tags": tags,
            "links": parse_links(cells[12]),
        })
    return papers


# --- Zotero / RIS ---------------------------------------------------------

def arxiv_ref(links):
    """Return (arxiv_id, paper_url) from a paper's links, or (None, url|None)."""
    url = None
    for l in links:
        m = ARXIV_RE.search(l["url"])
        if m:
            # prefer the abstract page as the canonical URL
            return m.group(1), f"https://arxiv.org/abs/{m.group(1)}"
        if l["label"].lower() == "paper" and url is None:
            url = l["url"]
    if url is None and links:
        url = links[0]["url"]
    return None, url


def load_cache():
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def fetch_arxiv_meta(arxiv_id):
    """Fetch {title, authors, abstract, year, doi} from the arXiv API, or None."""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "awesome-dexman-gen/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read()
        entry = ET.fromstring(raw).find(f"{ATOM}entry")
        if entry is None:
            return None
        title = " ".join((entry.findtext(f"{ATOM}title") or "").split())
        authors = [
            " ".join((a.findtext(f"{ATOM}name") or "").split())
            for a in entry.findall(f"{ATOM}author")
        ]
        authors = [a for a in authors if a]
        if title.lower() == "error" and not authors:
            return None
        return {
            "title": title,
            "authors": authors,
            "abstract": " ".join((entry.findtext(f"{ATOM}summary") or "").split()),
            "year": (entry.findtext(f"{ATOM}published") or "")[:4],
            "doi": (entry.findtext(f"{ARXIVNS}doi") or "").strip(),
        }
    except Exception as e:  # network error, bad XML, timeout, ...
        print(f"  ! arXiv fetch failed for {arxiv_id}: {e}", file=sys.stderr)
        return None


def to_lastfirst(name):
    parts = name.split()
    if len(parts) < 2:
        return name
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60] or "paper"


def build_ris(paper, meta, arxiv_id, paper_url):
    meta = meta or {}
    lines = ["TY  - JOUR"]
    lines.append("TI  - " + (meta.get("title") or paper["title"]))
    for a in meta.get("authors", []):
        lines.append("AU  - " + to_lastfirst(a))
    year = meta.get("year") or paper["year"]
    if year:
        lines.append("PY  - " + year)
    venue = paper["venue"]
    if arxiv_id and (not venue or venue.lower() == "arxiv"):
        venue = f"arXiv preprint arXiv:{arxiv_id}"
    if venue:
        lines.append("T2  - " + venue)
    if meta.get("abstract"):
        lines.append("AB  - " + meta["abstract"])
    if paper_url:
        lines.append("UR  - " + paper_url)
    if meta.get("doi"):
        lines.append("DO  - " + meta["doi"])
    if arxiv_id:
        # L1 = PDF attachment; Zotero fetches and attaches it on import.
        lines.append("L1  - https://arxiv.org/pdf/" + arxiv_id + ".pdf")
        lines.append("N1  - arXiv:" + arxiv_id)
    lines.append("ER  - ")
    return "\n".join(lines)


def enrich(papers):
    """Attach a full RIS string and a download slug to each paper."""
    cache = load_cache()
    dirty = False
    for p in papers:
        arxiv_id, paper_url = arxiv_ref(p["links"])
        meta = None
        if arxiv_id:
            if arxiv_id in cache:
                meta = cache[arxiv_id]
            else:
                print(f"  fetching arXiv:{arxiv_id} ...")
                meta = fetch_arxiv_meta(arxiv_id)
                if meta:
                    cache[arxiv_id] = meta
                    dirty = True
                    time.sleep(1)  # be gentle with the arXiv API
        p["ris"] = build_ris(p, meta, arxiv_id, paper_url)
        p["slug"] = slugify(p["title"].split(":")[0])
    if dirty:
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Updated cache: {CACHE}")
    return papers


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Awesome Dexterous Manipulation</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         margin: 0; padding: 1.5rem; max-width: 1100px; margin: 0 auto; line-height: 1.45; }}
  h1 {{ margin: 0 0 .25rem; font-size: 1.6rem; }}
  .sub {{ color: #777; margin: 0 0 1.25rem; }}
  .controls {{ position: sticky; top: 0; background: Canvas; padding: .75rem 0;
               border-bottom: 1px solid #8884; z-index: 5; }}
  #search {{ width: 100%; padding: .6rem .8rem; font-size: 1rem; box-sizing: border-box;
             border: 1px solid #8886; border-radius: 8px; background: Canvas; color: inherit; }}
  .tagbar {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .6rem; align-items: center; }}
  .tag {{ cursor: pointer; user-select: none; border: 1px solid #8886; border-radius: 999px;
          padding: .25rem .7rem; font-size: .85rem; }}
  .tag.on {{ background: #3b82f6; border-color: #3b82f6; color: #fff; }}
  .meta {{ margin-left: auto; color: #777; font-size: .85rem; }}
  .mode {{ font-size: .8rem; color: #777; cursor: pointer; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: .5rem .6rem; border-bottom: 1px solid #8883; vertical-align: top; }}
  th {{ font-size: .8rem; text-transform: uppercase; letter-spacing: .03em; color: #777; }}
  td.year, td.num {{ white-space: nowrap; color: #777; }}
  .pill {{ display: inline-block; font-size: .72rem; padding: .05rem .45rem; margin: 0 .2rem .2rem 0;
           border-radius: 999px; background: #8882; }}
  .links a {{ margin-right: .5rem; white-space: nowrap; }}
  a.zotero {{ display: inline-flex; align-items: center; justify-content: center;
             width: 1.2rem; height: 1.2rem; border-radius: 4px; background: #cc2936;
             color: #fff !important; font-weight: 700; font-size: .8rem; line-height: 1;
             text-decoration: none; vertical-align: middle; margin-right: 0; }}
  a.zotero:hover {{ background: #a81f2b; }}
  tr.hide {{ display: none; }}
  mark {{ background: #fde047; color: #000; }}
</style>
</head>
<body>
  <h1>Awesome Dexterous Manipulation</h1>
  <p class="sub">A curated, filterable collection of dexterous robotic manipulation papers.
     Click the red <b>Z</b> to download a paper's citation for Zotero.</p>
  <div class="controls">
    <input id="search" type="search" placeholder="Search title, venue or affiliation…" autocomplete="off">
    <div class="tagbar" id="tagbar">
      <span class="mode" id="mode" title="Toggle AND/OR matching">match: <b>all</b></span>
      <span class="meta" id="count"></span>
    </div>
  </div>
  <table>
    <thead><tr><th>#</th><th>Title</th><th>Venue</th><th>Year</th><th>Affiliation</th><th>Tags</th><th>Links</th></tr></thead>
    <tbody id="rows"></tbody>
  </table>
<script>
const PAPERS = {data};
const TAGS = {tags};
let active = new Set();
let andMode = true;

const tagbar = document.getElementById('tagbar');
const mode = document.getElementById('mode');
TAGS.forEach(t => {{
  const el = document.createElement('span');
  el.className = 'tag'; el.textContent = t; el.dataset.tag = t;
  el.onclick = () => {{ active.has(t) ? active.delete(t) : active.add(t); el.classList.toggle('on'); render(); }};
  tagbar.insertBefore(el, mode);
}});
mode.onclick = () => {{ andMode = !andMode; mode.querySelector('b').textContent = andMode ? 'all' : 'any'; render(); }};

const rows = document.getElementById('rows');
const search = document.getElementById('search');
const count = document.getElementById('count');

function esc(s) {{ return s.replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c])); }}
function hl(text, q) {{
  if (!q) return esc(text);
  const i = text.toLowerCase().indexOf(q);
  if (i < 0) return esc(text);
  return esc(text.slice(0,i)) + '<mark>' + esc(text.slice(i,i+q.length)) + '</mark>' + esc(text.slice(i+q.length));
}}

function build() {{
  rows.innerHTML = PAPERS.map(p => {{
    const pills = p.tags.map(t => '<span class="pill">'+t+'</span>').join('');
    const links = p.links.map(l => '<a href="'+l.url+'" target="_blank" rel="noopener">'+esc(l.label)+'</a>').join(' · ');
    const ris = 'data:application/x-research-info-systems;charset=utf-8,' + encodeURIComponent(p.ris);
    const zot = '<a class="zotero" href="'+ris+'" download="'+esc(p.slug)+'.ris" title="Add to Zotero (download .ris)">Z</a>';
    return '<tr data-title="'+esc(p.title.toLowerCase())+'" data-venue="'+esc(p.venue.toLowerCase())+'" data-affil="'+esc((p.affiliation||'').toLowerCase())+'" data-tags="'+p.tags.join(',')+'">'
      + '<td class="num">'+p.n+'</td>'
      + '<td class="title">'+esc(p.title)+'</td>'
      + '<td>'+esc(p.venue)+'</td>'
      + '<td class="year">'+esc(p.year)+'</td>'
      + '<td>'+esc(p.affiliation||'')+'</td>'
      + '<td>'+pills+'</td>'
      + '<td class="links">'+links+' '+zot+'</td></tr>';
  }}).join('');
}}

function render() {{
  const q = search.value.trim().toLowerCase();
  let shown = 0;
  for (const tr of rows.children) {{
    const tags = tr.dataset.tags ? tr.dataset.tags.split(',') : [];
    const tagOk = active.size === 0 || (andMode
      ? [...active].every(t => tags.includes(t))
      : [...active].some(t => tags.includes(t)));
    const textOk = !q || tr.dataset.title.includes(q) || tr.dataset.venue.includes(q) || tr.dataset.affil.includes(q);
    const ok = tagOk && textOk;
    tr.classList.toggle('hide', !ok);
    if (ok) {{ shown++;
      tr.querySelector('.title').innerHTML = hl(tr.querySelector('.title').textContent, q);
    }}
  }}
  count.textContent = shown + ' / ' + PAPERS.length + ' papers';
}}

build();
search.addEventListener('input', render);
render();
</script>
</body>
</html>
"""


def main():
    papers = enrich(parse_readme())
    html = HTML.format(
        data=json.dumps(papers, ensure_ascii=False),
        tags=json.dumps(TAGS),
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} with {len(papers)} papers.")


if __name__ == "__main__":
    main()
