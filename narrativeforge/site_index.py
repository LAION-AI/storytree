"""Build a landing page over several projects.

Each project keeps its own self-contained viewer; this page is the shelf they
sit on. It reads the artifacts directly so the figures are counted rather than
declared, and it says plainly which are finished and which are still being
written.

One rule is enforced here rather than left to care: a project whose prose comes
from a source document the pipeline did not write (a reconstruction) is
published as *structure only*. The derived graph is a description and travels
freely; the document it describes stays in the user's own files.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectCard:
    slug: str
    href: str
    title: str
    kind: str            # "written" | "reconstructed"
    model: str
    status: str          # "complete" | "in progress" | "structure only"
    logline: str
    summary: str
    counts: dict
    dominant: list
    note: str = ""


def read_project(root: Path, *, href: str, kind: str, model: str, note: str = "") -> ProjectCard | None:
    art = root / "artifacts"
    if not (art / "story_root.json").exists():
        return None
    j = lambda n: json.loads((art / n).read_text()) if (art / n).exists() else {}
    sr, ex = j("story_root.json"), j("expose.json")
    plots = j("plots.json").get("plots", [])
    ents = j("entities.json").get("entities", {})
    events = j("events.json").get("events", {})
    scenes = j("scenes.json").get("scenes", {})
    prose = list((root / "prose").glob("sc-*.md")) if (root / "prose").exists() else []

    beats = sum(len(s.get("beats", [])) for s in scenes.values())
    ops = sum(len(b.get("changes", [])) for s in scenes.values() for b in s.get("beats", []))
    counts = {"plots": len(plots), "entities": len(ents), "events": len(events),
              "scenes": len(scenes), "beats": beats, "patch ops": ops,
              "pages": len(prose)}

    if kind == "reconstructed":
        status = "structure only"
        counts.pop("pages", None)
    elif scenes and len(prose) >= len(scenes) and scenes:
        status = "complete"
    else:
        status = "in progress"

    emb = sr.get("plot_embedding") or {}
    g = emb.get("genres", {})
    dominant = [(k, g[k].get("score")) for k in (emb.get("dominant") or []) if k in g][:4]

    return ProjectCard(
        slug=root.name, href=href, title=sr.get("title") or root.name,
        kind=kind, model=model, status=status,
        logline=sr.get("logline") or "",
        summary=(ex.get("plot_summary_short") or "")[:420],
        counts=counts, dominant=dominant, note=note,
    )


# --------------------------------------------------------------------------

CSS = """
:root{
  --ground:#e9ebee;--surface:#f7f8fa;--surface-2:#eef0f3;--sunken:#dfe3e8;
  --ink:#161a1f;--ink-2:#39424d;--muted:#66717e;--faint:#93a0ae;
  --line:#cfd6de;--line-soft:#dde3ea;
  --heat:#c2451a;--heat-soft:#f0d5c9;--heat-ink:#8f3212;
  --quench:#2f6f8f;--quench-soft:#cfdfe8;--quench-ink:#23566f;
  --good:#3f7d55;--good-soft:#d6e6db;--warn:#8a6a12;--warn-soft:#f0e6cc;
  --shadow:0 1px 2px rgba(20,28,38,.07),0 10px 28px -14px rgba(20,28,38,.25);
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#101419;--surface:#171d24;--surface-2:#1d242c;--sunken:#0b0e12;
  --ink:#e4e8ec;--ink-2:#b9c2cc;--muted:#8b96a3;--faint:#5f6b78;
  --line:#2b343e;--line-soft:#222a33;
  --heat:#e2723f;--heat-soft:#3a2318;--heat-ink:#f0a077;
  --quench:#6aa8c6;--quench-soft:#152935;--quench-ink:#9cc9dd;
  --good:#67a97e;--good-soft:#17281d;--warn:#c99b45;--warn-soft:#2b2415;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 12px 32px -16px rgba(0,0,0,.75);
}}
:root[data-theme="dark"]{
  --ground:#101419;--surface:#171d24;--surface-2:#1d242c;--sunken:#0b0e12;
  --ink:#e4e8ec;--ink-2:#b9c2cc;--muted:#8b96a3;--faint:#5f6b78;
  --line:#2b343e;--line-soft:#222a33;
  --heat:#e2723f;--heat-soft:#3a2318;--heat-ink:#f0a077;
  --quench:#6aa8c6;--quench-soft:#152935;--quench-ink:#9cc9dd;
  --good:#67a97e;--good-soft:#17281d;--warn:#c99b45;--warn-soft:#2b2415;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 12px 32px -16px rgba(0,0,0,.75);
}
*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
h1,h2,h3{font-family:var(--serif);font-weight:600;text-wrap:balance;margin:0}
a{color:inherit;text-decoration:none}
:focus-visible{outline:2px solid var(--heat);outline-offset:3px;border-radius:6px}
.wrap{max-width:1120px;margin:0 auto;padding:0 26px 90px}
header{border-bottom:1px solid var(--line);background:var(--surface)}
header .wrap{padding:46px 26px 34px}
.mark{display:flex;align-items:baseline;gap:10px;font-family:var(--serif);
  font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);
  font-weight:700;margin-bottom:14px}
.mark .dot{width:9px;height:9px;border-radius:50%;background:var(--heat);
  transform:translateY(-1px)}
h1{font-size:clamp(28px,4.4vw,40px);letter-spacing:-.02em;line-height:1.14;margin-bottom:14px}
.lede{font-size:18px;color:var(--ink-2);max-width:66ch;font-family:var(--serif)}
.topstats{display:flex;gap:26px;flex-wrap:wrap;margin-top:24px;font-family:var(--mono);
  font-size:12.5px;color:var(--faint)}
.topstats b{color:var(--ink-2);font-weight:700}
h2.sec{font-size:14px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);
  font-family:var(--sans);font-weight:700;margin:44px 0 4px}
.secnote{font-size:13.5px;color:var(--muted);margin:0 0 18px;max-width:64ch}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}
.card{display:flex;flex-direction:column;background:var(--surface);
  border:1px solid var(--line-soft);border-radius:11px;padding:22px 24px 20px;
  box-shadow:var(--shadow)}
a.card:hover{border-color:var(--heat)}
a.card:hover h3{color:var(--heat)}
.card .top{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}
.card h3{font-size:21px;letter-spacing:-.01em;line-height:1.2}
.pill{font-family:var(--mono);font-size:10.5px;padding:3px 8px;border-radius:20px;
  white-space:nowrap;font-weight:600;margin-left:auto}
.pill.complete{background:var(--good-soft);color:var(--good)}
.pill.progress{background:var(--warn-soft);color:var(--warn)}
.pill.structure{background:var(--quench-soft);color:var(--quench-ink)}
.card .logline{font-family:var(--serif);font-size:15.5px;color:var(--ink-2);
  line-height:1.5;margin-bottom:12px}
.card .summary{font-size:13.5px;color:var(--muted);line-height:1.55;margin-bottom:14px}
.tags{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px}
.tag{font-family:var(--mono);font-size:11px;padding:3px 8px;border-radius:5px;
  background:var(--surface-2);border:1px solid var(--line-soft);color:var(--muted)}
.tag.hot{background:var(--heat-soft);border-color:transparent;color:var(--heat-ink)}
.counts{display:flex;flex-wrap:wrap;gap:14px;padding-top:14px;margin-top:auto;
  border-top:1px solid var(--line-soft)}
.counts div{font-family:var(--mono);font-size:12px;color:var(--faint)}
.counts b{display:block;font-size:17px;color:var(--ink);font-weight:700;
  font-variant-numeric:tabular-nums}
.provenance{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:12px}
.note{font-size:12.5px;color:var(--warn);margin-top:10px;line-height:1.5}
.links{display:flex;gap:10px;flex-wrap:wrap;margin-top:26px}
.links a{padding:9px 15px;border-radius:8px;background:var(--surface-2);
  border:1px solid var(--line);font-size:13.5px;font-weight:600;color:var(--ink-2)}
.links a:hover{border-color:var(--heat);color:var(--heat)}
.links a.primary{background:var(--heat);border-color:var(--heat);color:#fff}
footer{color:var(--faint);font-size:13px;border-top:1px solid var(--line);
  padding-top:20px;margin-top:54px}
"""


def build_index(cards: list[ProjectCard], out: Path, *, extra_links: list[tuple[str, str]] | None = None) -> Path:
    e = html.escape
    written = [c for c in cards if c.kind == "written"]
    recon = [c for c in cards if c.kind == "reconstructed"]

    def card_html(c: ProjectCard) -> str:
        pill = {"complete": "complete", "in progress": "progress",
                "structure only": "structure"}[c.status]
        tags = "".join(
            f'<span class="tag hot">{e(k.replace("_", " "))} {v}</span>'
            for k, v in c.dominant)
        counts = "".join(f"<div><b>{v}</b>{e(k)}</div>" for k, v in c.counts.items() if v)
        note = f'<div class="note">{e(c.note)}</div>' if c.note else ""
        summary = f'<div class="summary">{e(c.summary)}…</div>' if c.summary else ""
        return f"""
    <a class="card" href="{e(c.href)}">
      <div class="top"><h3>{e(c.title)}</h3><span class="pill {pill}">{e(c.status)}</span></div>
      <div class="logline">{e(c.logline)}</div>
      {summary}
      <div class="tags">{tags}</div>
      <div class="counts">{counts}</div>
      <div class="provenance">{e(c.kind)} · {e(c.model)}</div>
      {note}
    </a>"""

    total = {}
    for c in cards:
        for k, v in c.counts.items():
            total[k] = total.get(k, 0) + v
    topstats = " ".join(f"<span><b>{v:,}</b> {e(k)}</span>" for k, v in total.items() if v)
    links = "".join(f'<a href="{e(h)}">{e(t)}</a>' for t, h in (extra_links or []))

    body = f"""<meta charset="utf-8">
<title>Narrativeforge Projects</title>
<style>{CSS}</style>
<header><div class="wrap">
  <div class="mark"><span class="dot"></span>narrativeforge</div>
  <h1>Story graphs</h1>
  <p class="lede">Each of these is a complete narrative structure — story root, exposé,
  plots, entity dossiers, a causal event graph and scene beats carrying literal patch
  operations — built either forward from a brief or recovered backwards from a finished
  screenplay. Open one to walk it.</p>
  <div class="topstats">{topstats}</div>
  <div class="links">{links}</div>
</div></header>
<div class="wrap">

  <h2 class="sec">Written forward</h2>
  <p class="secnote">Invented from a brief: the structure was decided before any prose
  existed, and the pages were written last, from the scene definitions.</p>
  <div class="grid">{"".join(card_html(c) for c in written)}</div>

  {"" if not recon else f'''
  <h2 class="sec">Recovered backwards</h2>
  <p class="secnote">Given a finished screenplay, the pipeline reconstructs the layers
  above it — with every scene node bound to exactly one passage of the source. These are
  published as structure only: the derived graph is a description, and the document it
  describes stays where it came from.</p>
  <div class="grid">{"".join(card_html(c) for c in recon)}</div>'''}

  <footer>Counts are read from the artifacts on disk, not declared. Projects marked
  <em>in progress</em> are still being generated; reload to see them fill in.</footer>
</div>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body)
    return out
