# Handshake 2 — Session-Übergabe

Stand: 26.08.2026 · Repo: **github.com/LAION-AI/storytree** (public; transferiert von christophschuhmann/storytree, alte URL redirectet) · Live: https://projects.laion.ai/storytree/webapp/storytree-explorer.html

---

## 🔄 KONTEXT RESET (Status quo nach Muse-1.2-Durchlauf)

Dieser Abschnitt ersetzt alle früheren "aktuellen besten Stand"-Angaben. Der komplette Tree wurde **einmal komplett mit Muse 1.2** (`muse-spark-1.2-contributor-free` via Zen-API) durchlaufen. Ornith (8110/8111) läuft noch als Fallback. Muse-Baseline ist `runs/*_muse*`.

### Muse-Pipeline-Durchlauf — TOTAL 1692s (~28 min)

`tools/run_muse_pipeline.sh` (Stage-Timing in `runs/muse_pipeline_timing.md`, Pro-Stage-Logs `runs/muse_<stage>.log`).

| Stage | Modell | Ergebnis | Score | Zeit | Output |
|---|---|---|---|---|---|
| root  | Muse 1.2 | **PASS** | mean **4.7** | 638s | `runs/story_root_muse` |
| plots | Muse 1.2 | FAIL | **2.6** (P1=2 P2=3 P3=2 P4=4 P5=2) | 695s | `runs/plot_layer_muse` |
| cover | Muse 1.2 | 8 missing Events zugewiesen | **GATE ALL PASS** | 101s | `plot_layer_muse/plots_covered.json` |
| expose| Muse 1.2 | **PASS** | mean **4.44** | 258s | `runs/expose_muse` |
| explorer | — | | 0s | data | `webapp/explorer/storytree.json` (539 kB) |

Artefakte:
- Root: `runs/story_root_muse/story_root.json` + `judgement.json` (PASS, 4.7).
- Plots v1 (Original-Prompt): `runs/plot_layer_muse` — 5 Plots, keine faults, P1/P3/P5 unten.
- Plots v2 (verbesserter Prompt + aggressiver Repair): `runs/plot_layer_muse_v2` — **REGRESSION** 2.6 → 2.0 (siehe unten).
- Exposé: `runs/expose_muse/expose.json`+`.md` (PASS, 8 Sections, 2253 synopsis-words).
- Per-Call-Timing in `runs/muse_timing.jsonl` (`dur_s, attempts, prompt_tokens, completion_tokens, ok, port, model`).

### Plot-Layer: Versuch mit verbessertem Repair — RÜCKGANG (2.6 → 2.0)

`runs/plot_layer_muse_v2`: Prompt verschärft (PERSPECTIVE DISCIPLINE, NON-REDUNDANCY) + mechanischer Repair, der *überlappende* Events entfernt.

- **Ergebnis: mean 2.0** (P4=2, P5=1) — **verschlechtert** gegenüber 2.6.
- **Diagnose**: Überlappung ist **kein Bug**. `ev-010` (Oracle), `ev-032` (Ressurrektion/Wette), `ev-038` (Telefon-Bühne), `ev-046` (Endkampf) sind die **strukturelle Wirbelsäule** → sie müssen 4–5× vorkommen, weil Perspektiven dort konvergieren. Der Repair entfernte sie → **P4 "arcs truncate before true resolutions"**.
- **Lehre**: Frequenz-basierte P5-Reparatur zerstört P4. Overlap per *Streichen* = Counterproduktiv. Gelöst durch **distincte Kontexte** im `caused_by_previous`/`why_in_plot`, nicht durch Entfernen.

### Muse vs Ornith — Vergleich (Layer für Layer)

| Layer | Ornith | Muse 1.2 | Δ | Bemerkung |
|---|---|---|---|---|
| Events / Scenes | baseline build10 | **baseline unverändert** (statischer Input) | — | wurden NICHT regeneriert |
| Meta | meta_layer_v2b | pass | — | unverändert |
| Entities | entity_trial_v2 | 6.4 (eval) | — | Brown/Jones-Differenzierung defizitär |
| Root | v3: 5.0 / **8.7** | Muse: **4.7** | -0.1 (Rubric) |
| Plots | v8: gate-PASS (Quali 5/10) | Muse: **2.6 / 2.0** | Muse deutlich schlechter | Overlap + P3 Membership |
| Expose | v1: 5.0 (mit Jacket-Copy-Bug) | Muse: **4.44** | -0.56 |

> Muse nutzt ein anderes Skalierung (1–5 mean vs Ornith 1–10). 4.44 Muse ≈ stark befriedigend, aber < 5.0 Ornith-Expose.

### GLM-5.3-Panel (26.08. nachmittags) — gemeinsamer Judge über beide Arme

Voller Report: **`docs/glm53-panel-report.md`**. 3×-GLM-5.3-Panel (via Zen,
`tools/glm_panel_judge.py`, Rubrics byte-identisch zu den Layer-Judges,
Arme anonymisiert): Root 4.80 vs 4.73 (tie, PASS), Exposé 4.30 vs 4.44
(tie, PASS), **Plots 2.73 (v8/online) vs 3.33 (Muse) — Ranking invertiert**:
v8s 4.6 war Selbst-Judgement durch den eigenen Composer. P1 (same-plot
enablement) ist auf beiden Armen der Universaldefekt (6/6 Judge-Pässe);
distinkte Kontexte für geteilte Klimax-Events funktionieren (Muse P5 3.33
vs v8 2.00). Jacket-Copy-Truncation liegt im **Default**-Exposé (expose_v1,
online) und kostet dort X1/X5/X7.

**Lokales GLM-5.3-Serving: unmöglich auf dieser Maschine** (8× A100/SM80 —
alle Sparse-MLA-Kernel Hopper-only; vLLM/SGLang-Support nur als frische
PRs, llama.cpp/GGUF gar nicht; FP8 299 GiB, BF16 599 GiB > freie Disk).
Details und H100-Sizing (8×H100 TP8 bzw. 4×H200 TP4) im Report, §3.

### Qwen3.8-Flash-Next lokal (26.08. nachmittags) — LÄUFT auf 4×A100

Volles Protokoll: **`docs/qwen38-flash-next-protokoll.md`** (8 Startup-
Hürden mit Fixes — Pflichtlektüre vor jedem Neustart). Serving:
`tools/serve_qwen38fn.sh` (Port 8130, TP4+EP, GPUs 4–7; **Ornith 8111
dafür gestoppt**, 8110 läuft). Gemessen: 54 tok/s single, **1305 tok/s**
bei 32 Streams. `response_format: json_schema` liefert pures JSON trotz
Reasoner-Modell; gegen den einen Server `--ports 8130,8130,8130,8130`.
Plot-Layer damit generiert: GLM-Panel **2.07 FAIL** (P5=1 — zwei
Ganzfilm-Retellings statt Perspektiven) — schnellster Composer, schwächstes
Plot-Ergebnis (Muse 3.33 > v8 2.73 > Qwen 2.07). Rolle eher Durchsatz/
Draft/Judge als Ein-Schuss-Composer.

### Plot-Layer Zwei-Pass-Kampagne (26.08. abends) — Seed schlaegt Struktur

Voller Report: **`docs/plots-twopass-campaign.md`**. Zwei-Pass
(Membership-Pass, dann Ketten mit Enum-erzwungener Kausalitaet +
Link-Verify; `distill/plot_layer_twopass.py`) mit Ornith UND Muse getestet,
alles per 3x-GLM-Panel: v1-Ornith 2.13, **v2-Muse 2.07 = v2-Ornith 2.07**
(identische Dimensionsform, P5 1.33) — bei gleichem Geruest ist der
Composer egal. Ursache sauber isoliert: Pass-0-Seed aus den
Meta-*Dilemma*-Perspektiven -> alle 5 Plots erzaehlen dieselbe
Spaetfilm-Sequenz (ev-025/030/031/032/034 in 3-4 Plots). Muse Ein-Pass
(3.33, filmweite Identitaeten) bleibt Bestwert. Was BLEIBT: erstmals 0
Strukturfehler in allen Ketten (Enum + Lint), Verify->Regenerate greift.
Naechster Schritt (v3, noch nicht gelaufen): v2-Maschinerie + filmweiter
Throughline-Seed + Arc-Closure-Gate, zuerst mit Muse.

### Plot-Experimente Runde 2 (26.08. spaet) — Ceiling bestaetigt

Addendum in **`docs/plots-twopass-campaign.md`**. (1) Self-Critique->Revise
(`distill/plot_layer_refine.py`): bei Muse verwirft der Guard die eigene
Revision (No-Op), bei Ornith **verschlechtert** sie das Layer 2.73->2.53
bei Selbst-Note 4.0 — Idee in beiden Kalibrierungs-Regimen falsifiziert.
(2) Best-of-5 Muse Ein-Pass: 3.33/3.33/2.93/2.87/2.47 — **3.33 ist das
reproduzierbare Ceiling**, Selektion versichert nur gegen schlechte Draws.
(3) Zwei-Pass v3 (filmweiter Seed): Muse 2.07->3.00 (+0.93, bestes P4=4.0
der Kampagne), Ornith unveraendert 2.07. **P1 nie ueber 3.0, in 11 Armen.**
Naechster Hebel: staerkerer Composer via HYPRLAB (Ein-Pass UND v3-Geruest),
danach Cross-Model-Link-Verify.

### ⚠️ OFFEN / BEKANNT

- **Plot-Layer P5 Non-Redundancy**: endemisch für Muse — die Climax-Events `ev-010/032/038/046` müssen 4–5× vorkommen. Der Judge zählt nur Frequenz. Lösung (a) Judge-Rubric anpassen ("recycled peak mit distinktem Kontext = kein Rehash") oder (b) `prompt_a` um `load_bearing_event` erweitern (je Plot andere Ursache).
- **Exposé Jacket-Copy-Truncation** ("…save one he"): Bug existiert weiter (Handhack-Step 2 offen).
- **Entity Brown/Jones-Differenzierung**: bleibt defizitär.
- **Zeit**: Muse langsam (~32 tok/s Completion; Ø 137s/Call). 3 Shims = echte Parallelität, aber ZeN selbst Engpass (Sublinear-Speedup ab ≥4 Calls; 2× HTTP 503 beobachtet).

---

## 🛠️ NEUER CODE

### 1. `tools/zen_shim.py` (neu geschrieben — der Muse-1.2-Fix)

OpenAI `chat/completions`-Kompatibilitätsschicht → Zen `/v1/responses`.

- **Bug gefixt**: Muse ignoriert `response_format: json_schema` (kein Grammar-Layer). Shim erkennt das Schema, **betet es als Prompt-Zusatz** "Respond with ONLY raw JSON…" + tolerantestes Parsen (Fences strippen, erstes `{`..letztes `}`, 1 Retry mit Reminder).
- **ThreadingHTTPServer**: parallele Requests in einem Port wirklich parallel (jeweils ein Thread pro Request).
- **Zeit-Logging**: je Upstream-Call JSONL in `runs/muse_timing.jsonl` (`dur_s, attempts, prompt_tokens, completion_tokens, ok, port, model`).
- Upstream-Fehler → HTTP **502**, damit `EndpointPool` selbst retried (3×).
- Env: `PORT` (default 8222), `SHIM_LOG`.

### 2. `distill/plot_layer.py` (geändert)

- `work()` → `chain_for(name, mode="initial"|"repair", forbid=())` mit verbessertem Prompt: **PERSPECTIVE DISCIPLINE** / **MEMBERSHIP** (kein Padding) / **SELF-CONTAINED CAUSALITY** (kein Cross-Plot-Enablement).
- **Repair-Runde jetzt strukturell-only**: repariert nur echte Defekte (Duplikate innerhalb einer Chain, falsche Story-Order, unbekannte IDs, Ketten < 5). **Globale Überlappung wird NICHT als Defekt gewertet / gelöscht** — sie wird über distincte Kontexte gelöst.
- `max_workers=2` → `min(4, len(plots))`.

### 3. `tools/plot_cover.py`

- Ports/Model **env-gesteuert**: `MUSE_PORTS`, `MUSE_MODEL` (Default Ornith 8110/8111, unverändert für den Ornith-Fall).

### 4. `tools/run_muse_pipeline.sh` (neu)

Orchestrator mit Stage-Zeit-Tracking:
```
PORTS=8222,8223,8224 MODEL=muse-spark-1.2-contributor-free \
  setsid nohup bash tools/run_muse_pipeline.sh > runs/muse_pipeline.log 2>&1 < /dev/null & disown
```

### 5. Infrastruktur (aktuell laufend)

- **3 Shim-Instanzen** detached (setsid): 8222 / 8223 / 8224.
- `EndpointPool` verteilt Calls round-robin über die Ports.
- Muse-Freigrenzen: ctx 1.05M / out 131k Tokens.
- tmux-Session **storytree** (7 Panes) mit opencode TUIs; Reports `runs/muse_eval/*.md`; Watchdog `~/.local/bin/stwatch.sh`.

---

## ➡️ WHERE TO CONTINUE (nächste Schritte, Priorisiert)

> ⚠️ Ein `runs/plot_layer_muse_v3/` (26.08. 11:57, self-judged 1.8 FAIL)
> wurde NICHT von der Haupt-Session erzeugt — Provenienz unklar (vermutlich
> tmux-TUI/Watchdog). Nicht committed; vor Verwendung Prompt-Stand prüfen.

**Priorität A — Plot-Layer P5 nicht durch Löschen, sondern durch Kontext**
Option (b): `prompt_a` um `load_bearing_event` erweitern — jeder Plot definiert den geteilten Peak mit einer *anderen* `caused_by`/`why_in_plot`. Dann 3. Lauf:
```
PORTS=8222,8223,8224 MODEL=muse-spark-1.2-contributor-free \
python3 distill/plot_layer.py --meta runs/meta_layer_v2b/meta.json \
  --events runs/events_build10_full/events.json --out runs/plot_layer_muse_v3 \
  --ports 8222,8223,8224 --model muse-spark-1.2-contributor-free
MUSE_PORTS=8222,8223,8224 MUSE_MODEL=muse-spark-1.2-contributor-free \
  python3 tools/plot_cover.py runs/plot_layer_muse_v3/plots.json \
    runs/plot_layer_muse_v3/plots_covered.json
python3 tools/pipeline_gate.py --plots runs/plot_layer_muse_v3/plots_covered.json
```

**Priorität B — Exposé Jacket-Copy-Truncation** (`distill/expose_layer.py` / Schema `maxLength` oder Stop-String). Handshake-Step 2.

**Priorität C — Entity Brown/Jones-Differenzierung** (Prompt + erneut).

**Priorität D — Multi-Judge-Panel** über Plot-Samples v1–v8 (Drift-Messung — *noch offen*).

---

## 📂 SCHNELL-REFERENZ

Shims starten:
```
for p in 8222 8223 8224; do PORT=$p setsid nohup python3 tools/zen_shim.py > runs/shim_$p.log 2>&1 < /dev/null & disown; done
```
Shim testen (gibt pures JSON zurück):
```
curl -sS -X POST http://127.0.0.1:8222/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"muse-spark-1.2-contributor-free","messages":[{"role":"user","content":"nur ein JSON: {\"x\":1}"}],"response_format":{"type":"json_schema","json_schema":{"name":"k","schema":{"type":"object","properties":{"x":{"type":"integer"}}}}}}'
```

