# Handshake 2 — Session-Übergabe

Stand: 26.08.2026 · Repo: **github.com/LAION-AI/storytree** (public, transferiert von christophschuhmann/storytree, alte URL redirectet) · Live: https://projects.laion.ai/storytree/webapp/storytree-explorer.html

## Aktueller bester Stand (alles PASS, gepusht)
- Root v3 `runs/story_root_v3/` (5.0, RT1–10, inkl. identification_value mit ev-Zitaten) · Exposé `runs/expose_v1/` (5.0) · Meta `runs/meta_layer_v2b/` · Entities `runs/entity_trial_v2/profiles.json` · Events `runs/events_build10_full/events.json` (**ev-033 reinstated**) · Plots `runs/plot_layer_v8/plots_covered.json` (**47/47 Events, 224/224 Szenen**)
- Explorer: `webapp/storytree-explorer.html` + Daten via `python3 tools/build_explorer_data.py` (liest story_root_v3 + plots_covered)
- Gate: `python3 tools/pipeline_gate.py [--plots ...]` — 18 Assertions, Exit 1 bei Verstoß. Runner: `tools/run_storytree.sh`

## OFFEN: Muse-Spark-Pipeline (der Grund für diesen Handshake)
Ziel: ganze Pipeline mit Muse statt Ornith in `runs/*_muse/`. 
- Zen-API (ohne Key!): POST `https://opencode.ai/zen/v1/responses` `{"model":"muse-spark-1.2-contributor-free","input":"..."}` → Antwort `output[]`, Text steckt in items type==message → content[].text
- Shim existiert: `tools/zen_shim.py` (Port 8222, OpenAI→Zen). **BUG**: Muse ignoriert JSON-Schema (kein Grammar-Layer wie llama.cpp) → `chunk fail: 'facts'`. 
- **FIX TO DO**: im Shim Prompt-Zusatz „Respond with ONLY raw JSON" + tolerantes Parsing (```-Fences strippen, erstes `{`..letztes `}` extrahieren). Dann: `python3 distill/root_layer.py --out runs/story_root_muse --ports 8222 --model muse-spark-1.2-contributor-free`, danach plot_layer (+plot_cover) und expose_layer gleiche Flags.
- Free-Model-Budgets: muse-spark-1.2-free ctx=1.05M out=131k (bester), nemotron-3-ultra 1M/128k, deepseek-v4-flash-free 200k/128k.

## Infrastruktur
- tmux-Session **storytree**: 7 Panes opencode TUIs (muse-spark free), Aufgaben je Layer; Reports in `runs/muse_eval/*.md` (root 8.7, meta pass, entities 6.4 — Brown/Jones blur, plots 5/10 — Overlap, expose fand Jacket-Copy-Truncation-Bug). Watchdog `~/.local/bin/stwatch.sh` auto-retryt Stream-Errors + erlaubt Permissions, Log `runs/tmux_watchdog.log`.
- opencode 1.17.17 installiert, Config `~/.config/opencode/opencode.json` (Provider ornith→localhost:8110).

## Gotchas
- Heredocs: nur kleine, quoted (`<<'EOF'`); große Dateien mehrfach anhängen oder editor nutzen; JS nach jedem Patch `node --check`.
- Push: origin = LAION-AI/storytree; `tools/publish.sh` umgestellt. Token HAT KEINE `workflow`-Scope → `.github/` bleibt gitignored. Pages = branch deploy von main/root.
- Vor public-push: kein Leak (`tools/check_no_leak.py`). `.env` nie committen.

## Nächste Schritte nach Reset
1. Zen-Shim-Fix (oben) → Muse-Root-Lauf zu Ende → Plots+Cover+Gate → Exposé → Vergleich Ornith vs Muse
2. Reparieren: expose_v1 jacket_copy truncation („…save one he"), Entity Brown/Jones-Differenzierung
3. Multi-Judge-Panel über plot samples v1–v8 (Drift-Messung steht noch aus)
