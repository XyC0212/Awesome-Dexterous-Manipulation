#!/usr/bin/env python3
"""Generate docs/index.html (an interactive, filterable view) from the README table.

The README table is the single source of truth. Run this after editing it:

    python3 scripts/gen_site.py

Each paper also gets a lightweight citation page under docs/p/<arxiv-id>.html
carrying Highwire metadata (citation_title/author/date + citation_pdf_url). The
list page links to it via a red "Z"; when you open that page and click the
Zotero Connector browser extension, it saves a full record *with the arXiv PDF
attached* (COinS on the list could only carry citation fields, never the PDF).
Author/title/abstract metadata is fetched from the arXiv API at build time and
cached in scripts/zotero_cache.json (committed), so re-runs are offline-safe and
only new arXiv papers trigger a network request.

Then commit docs/index.html, docs/p/ and zotero_cache.json. Serve it with GitHub
Pages (Settings -> Pages -> deploy from branch -> /docs).
"""
import html
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
PAPERS_DIR = ROOT / "docs" / "p"
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


# --- Zotero citation pages ------------------------------------------------

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


DETAIL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Awesome Dexterous Manipulation</title>
{metas}
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         margin: 0 auto; max-width: 760px; padding: 1.5rem; line-height: 1.5; }}
  a {{ color: #2563eb; }}
  h1 {{ font-size: 1.35rem; margin: .3rem 0; }}
  h2 {{ font-size: 1rem; color: #777; margin: 1.5rem 0 .4rem; }}
  .authors {{ color: #444; }}
  .venue {{ color: #777; margin: .2rem 0 1rem; }}
  .save {{ background: #cc29361a; border: 1px solid #cc293655; border-radius: 8px;
           padding: .6rem .8rem; }}
  .save b {{ color: #cc2936; }}
  .links a {{ margin-right: .8rem; }}
  .back {{ color: #777; font-size: .9rem; }}
</style>
</head>
<body>
  <p><a class="back" href="../index.html">← All papers</a></p>
  <h1>{title_html}</h1>
  <p class="authors">{authors_html}</p>
  <p class="venue">{venue_html} · {year}</p>
  <p class="save">📚 Click your <b>Zotero Connector</b> toolbar button now to save this paper
     <b>with its PDF</b> attached.</p>
  <p class="links">{links_html}</p>
  <h2>Abstract</h2>
  <p>{abstract_html}</p>
</body>
</html>
"""


def prepare_details_dir():
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    for f in PAPERS_DIR.glob("*.html"):  # drop stale pages before regenerating
        f.unlink()


def write_detail_page(paper, meta, arxiv_id, paper_url):
    """Write docs/p/<arxiv_id>.html with Highwire metadata the Zotero Connector reads.

    citation_pdf_url is the key line: it tells the Connector to fetch and attach
    the arXiv PDF when the item is saved from this page.
    """
    meta = meta or {}
    e = lambda s: html.escape(s or "", quote=True)
    title = meta.get("title") or paper["title"]
    authors = meta.get("authors", [])
    abstract = meta.get("abstract", "")
    year = meta.get("year") or paper["year"]
    venue = paper["venue"] or "arXiv"
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    metas = [f'<meta name="citation_title" content="{e(title)}">']
    for a in authors:
        metas.append(f'<meta name="citation_author" content="{e(to_lastfirst(a))}">')
    if year:
        metas.append(f'<meta name="citation_publication_date" content="{e(year)}">')
    metas.append(f'<meta name="citation_journal_title" content="{e(venue)}">')
    metas.append(f'<meta name="citation_arxiv_id" content="{e(arxiv_id)}">')
    metas.append(f'<meta name="citation_pdf_url" content="{e(pdf_url)}">')
    if paper_url:
        metas.append(f'<meta name="citation_public_url" content="{e(paper_url)}">')
    if abstract:
        metas.append(f'<meta name="citation_abstract" content="{e(abstract)}">')
    if meta.get("doi"):
        metas.append(f'<meta name="citation_doi" content="{e(meta["doi"])}">')

    link_items = list(paper["links"])
    if not any("pdf" in l["label"].lower() for l in link_items):
        link_items.append({"label": "PDF", "url": pdf_url})
    links_html = " · ".join(
        f'<a href="{e(l["url"])}" target="_blank" rel="noopener">{e(l["label"])}</a>'
        for l in link_items
    )

    doc = DETAIL.format(
        title=e(title),
        metas="\n".join(metas),
        title_html=e(title),
        authors_html=e(", ".join(authors)),
        venue_html=e(venue),
        year=e(year),
        links_html=links_html,
        abstract_html=e(abstract) if abstract else "<em>Abstract unavailable.</em>",
    )
    (PAPERS_DIR / f"{arxiv_id}.html").write_text(doc, encoding="utf-8")


def enrich(papers):
    """Fetch/cache arXiv metadata, write a citation page per paper, and set
    each paper's `detail` link (relative to docs/index.html) or None."""
    cache = load_cache()
    dirty = False
    prepare_details_dir()
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
        if arxiv_id:
            write_detail_page(p, meta, arxiv_id, paper_url)
            p["detail"] = f"p/{arxiv_id}.html"
        else:
            p["detail"] = None
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
             text-decoration: none; vertical-align: middle; }}
  a.zotero:hover {{ background: #a81f2b; }}
  .note {{ font-size: .85rem; color: #777; margin: .25rem 0 0; }}
  .note b {{ color: #cc2936; }}
  tr.hide {{ display: none; }}
  mark {{ background: #fde047; color: #000; }}
</style>
</head>
<body>
  <h1>Awesome Dexterous Manipulation</h1>
  <p class="sub">A curated, filterable collection of dexterous robotic manipulation papers.</p>
  <p class="note">📚 <b>Save to Zotero with the PDF:</b> click a paper's red <b>Z</b> to open its
     citation page, then click your <b>Zotero Connector</b> toolbar button — it saves the full
     record with the arXiv PDF attached.</p>
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
    const zot = p.detail ? ' <a class="zotero" href="'+esc(p.detail)+'" target="_blank" rel="noopener" title="Open citation page, then click the Zotero Connector to save with the PDF">Z</a>' : '';
    return '<tr data-title="'+esc(p.title.toLowerCase())+'" data-venue="'+esc(p.venue.toLowerCase())+'" data-affil="'+esc((p.affiliation||'').toLowerCase())+'" data-tags="'+p.tags.join(',')+'">'
      + '<td class="num">'+p.n+'</td>'
      + '<td class="title">'+esc(p.title)+'</td>'
      + '<td>'+esc(p.venue)+'</td>'
      + '<td class="year">'+esc(p.year)+'</td>'
      + '<td>'+esc(p.affiliation||'')+'</td>'
      + '<td>'+pills+'</td>'
      + '<td class="links">'+links+zot+'</td></tr>';
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
