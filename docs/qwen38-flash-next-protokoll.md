# Protokoll: Qwen3.8-Flash-Next lokal auf A100 mit vLLM

Stand: 26.08.2026, ~13:35. Ziel: `Qwen/Qwen3.8-Flash-Next` (FP8) auf 2–4×
A100 unter vLLM mit Batching servieren, damit den Plot-Layer neu generieren
und judgen. Dieses Protokoll hält fest, was dabei über Modell, Ökosystem
und diese Maschine gelernt wurde — inklusive jeder Startup-Hürde und ihres
Fixes, damit niemand diese Kette erneut ablaufen muss.

## 1. Das Modell

| | |
|---|---|
| Architektur | `Qwen4ExpForConditionalGeneration`, model_type `qwen4_exp` (multimodal Wrapper, `language_model_only: true`) |
| Größe | 180B total = 125B Transformer (6B aktiv) + **51B n-Gramm-Embeddings** + 4B MTP |
| MoE | 512 Experten, 10 routed + 1 shared aktiv, intermediate **640** (klein!) |
| Attention | Hybrid: Gated DeltaNet (48 V-/16 QK-Heads, linear) + „Qwen Sparse Attention" (QSA: 24 Q-/2 KV-Heads, Indexer mit budget 2048, compress 4) im 3:1-Muster über 48 Layer |
| Extras | Hyper-Connections (hc_count 4), PLE (per-layer embeddings), MTP-Layer, Kontext 262k |
| Checkpoints | BF16 (~360 GB) und FP8 e4m3 (~180 GB, 131 Shards) — wir nutzen FP8 |

**Der entscheidende Unterschied zu GLM-5.3-Flash:** die QSA-Attention ist
auf **FlashAttention-varlen + Triton** gebaut, nicht auf Hopper-only
FlashMLA/DSA-Kernel. Deshalb ist dieses Modell auf Ampere (SM80) machbar,
GLM-5.3 nicht.

## 2. Ökosystem-Status (26.08.2026)

- vLLM-Support existiert **nur** als am selben Tag geöffneter PR
  [vllm-project/vllm#53896](https://github.com/vllm-project/vllm/pull/53896)
  (`peakcrosser7/vllm@release/qwen38next`); dazu separat PR #53899
  („PLE-Offload": n-Gramm-Embeddings ins RAM — für 2-GPU-Deployments nötig,
  nicht in unserem Branch).
- Kein Support in vLLM 0.27.1/0.28.0/main, kein llama.cpp-Support; die
  unsloth-GGUF-Repos existieren mit Quant-Tabellen im README (IQ1_S 72 GB …
  Q4_K_XL 111 GB), Dateien waren zum Zeitpunkt der Prüfung vorhanden.
- Install-Weg der Wahl: `VLLM_USE_PRECOMPILED=1 uv pip install -e <clone>` —
  das Precompiled-Wheel enthält sogar den neuen fused-GDN-CUDA-Kernel; kein
  Source-Build nötig.

## 3. Die Startup-Hürden, in Reihenfolge (alle behoben)

Der PR ist tagesfrisch und trägt Merge-Skew: sein Modellcode ruft APIs, die
main am selben Tag umbenannt hat. Jede Hürde kam eine Stufe weiter:

| # | Symptom | Ursache | Fix |
|---|---|---|---|
| 1 | `torch._C._cuda_init(): driver too old (12040)` | Treiber 550 (CUDA 12.4) vs. Wheel torch+cu130 | `LD_LIBRARY_PATH=/home/deployer/models/cuda-compat` — Forward-Compat `libcuda.so` 590.48.01 (A100 = Datacenter, forward compat erlaubt) |
| 2 | `AutoWeightsLoader.__init__() … 'skip_prefixes'` (dann `'skip_substrs'`) | main hat beide Skip-Argumente entfernt | Beide Felder in `AutoWeightsLoader` restauriert (`_can_skip` um prefix/substr erweitert) — ein Fix für alle 6 Callsites |
| 3 | `MLAAttentionSpec … 'compress_ratio'` | main-Rename | `compress_ratio` → `tokens_per_state` (Feld auf `AttentionSpec`, gleiche Semantik) in `qsa_cache.py` |
| 4 | Triton: `fp8e4nv not supported … ('fp8e4b15','fp8e5')` in `fused_moe_kernel` | MoE-intermediate 640/TP4=160 teilt die 128er-Quantblöcke nicht → Code **erzwingt** Triton-Block-FP8-MoE; Triton kann E4M3 erst ab SM89 | `--enable-expert-parallel`: Experten bleiben ganz (512/EP), kein Block-Refine → Oracle wählt **MARLIN** (w8a16 weight-only, läuft auf SM80) |
| 5 | `KV cache layout LBNHC cannot express mixed page sizes` | Hybridmodell: Linear-Attn-State-Pages ≠ QSA-Pages | `VLLM_KV_CACHE_LAYOUT=BLHNC` (steht wörtlich in der Fehlermeldung) |
| 6 | `MLAAttentionSpec has no 'storage_block_size'` | main-Rename | → Property `num_states` (= block_size // tokens_per_state) |
| 7 | `QSA raw cache must be [blocks, block_size, 1, width]; got (256, 1, 4, 140)` | mains Allocator liefert Views als `[B, H, N, C]`, PR-Code erwartet `[B, rows, 1, C]` — Head- und State-Dim vertauscht | `_canonical_view()`: `permute(0, 2, 1, 3)` beim Bind; sicher, weil alle QSA-Triton-Kernel stride-basiert indizieren (`stride(0), stride(1), stride(3)`) |
| 8 | Nach erfolgreichem CUDA-Graph-Capture: `FileNotFoundError: 'ninja'` beim JIT-Build des Sampling-Moduls | FlashInfer-JIT braucht ninja, fehlte im venv | `uv pip install ninja` |

Alle Patches liegen im lokalen Checkout
`/home/deployer/models/vllm-qwen38next-src` (venv:
`/home/deployer/models/vllm-q38-venv`); Serve-Skript mit allen Flags und
Begründungen: `tools/serve_qwen38fn.sh`.

## 4. Deployment-Fakten

- **TP4 auf GPUs 4–7** (Ornith-Instanz 8111 dafür gestoppt; 8110 läuft als
  Fallback weiter). Gewichte: **44,5 GiB pro GPU**, Ladezeit ~49 s aus dem
  Page-Cache. Port 8130, Kontext 64k.
- **2× A100 geht mit diesem Branch nicht**: 180 GB / 2 = 90 GB > 80 GB.
  Es ginge erst mit PLE-Offload (PR #53899): −51 GB n-Gramm-Embeddings ins
  RAM → ~65 GB/GPU. Der Weg ist bekannt, aber ein zweiter Branch-Merge.
- FP8 auf Ampere = **Marlin weight-only** (Dequant zu BF16 im Kernel):
  volle Qualität der FP8-Gewichte, aber keine FP8-Compute-Beschleunigung —
  Compute läuft in BF16. vLLM warnt entsprechend.
- MTP/Speculative Decoding noch nicht aktiviert (erst Basis stabilisieren).

## 5. Übertragbare Lektionen

1. **Kernel-Gates zuerst prüfen, dann Gewichte laden.** Die Reihenfolge
   config.json → Arch-Registry → Kernel-Capability-Checks (`grep
   supports_compute_capability`) kostet Minuten und entscheidet alles.
   So fiel GLM-5.3 in Minuten durch (SM90-only), Qwen3.8 bestand.
2. **Tagesfrische Modell-PRs tragen Merge-Skew.** Der PR-Code ruft APIs von
   gestern; main hat sie heute umbenannt. Muster: Fehlermeldung → Rename in
   main suchen (`grep` im Ziel-Backend, das dieselbe Semantik nutzt — hier
   verriet `sparse_swa.py` den Namen `tokens_per_state`) → minimal patchen.
3. **Bei MoE-Quantisierung entscheidet Teilbarkeit über den Kernel-Pfad.**
   Kleines intermediate (640) + TP-Sharding + 128er-Blöcke = erzwungener
   Triton-Pfad. **EP statt TP für Experten** löst das strukturell und ist
   auf Ampere ohnehin der einzige Weg zum Marlin-Backend.
4. **Fehlermeldungen instrumentieren statt Allocator lesen**: die um die
   Ist-Shape erweiterte ValueError (`got (256, 1, 4, 140)`) hat die
   Permutations-Diagnose in einem Lauf geliefert.
5. **Stride-basierte Triton-Kernel vertragen permutierte Views** — Layout-
   Konflikte zwischen Engine und Modellcode lassen sich am Bind-Punkt mit
   einer `permute`-View lösen, ohne Kernel anzufassen.
6. **`pgrep -f` matcht den eigenen Monitor** (drittes Mal im Projekt):
   Warteschleifen, deren Pattern im eigenen Kommandotext vorkommt, laufen
   ewig. PID-basiert prüfen oder Pattern wählen, das nur den Zielprozess
   trifft.
7. Die Forward-Compat-Libs in `/home/deployer/models/cuda-compat` (590.48)
   überbrücken Treiber 550 → CUDA-13-Wheels für **alle** Projekte auf
   dieser Maschine — das war schon einmal jemandes Problem und die Lösung
   lag ungenutzt daneben.

## 6. Gemessener Throughput (4× A100, TP4+EP, Marlin w8a16, 64k ctx)

| Lastprofil | Ergebnis |
|---|---|
| Single-Stream (512 tok) | **54 tok/s** |
| 8 parallele Streams | 396 tok/s aggregiert (49,5/Stream) |
| 32 parallele Streams | **1305 tok/s aggregiert** (40,8/Stream) |

Einordnung: Single-Stream schneller als Ornith-397B lokal (44 tok/s) und
2× so schnell wie GLM-5.3 über Zen (27 tok/s); unter Batch-32 liefert der
eine Endpoint das ~48-fache eines Zen-Streams. Continuous Batching ersetzt
das Viele-Endpoints-Muster vollständig — ein Server, viele Streams.

Zwei Betriebsdetails:
- Das Modell ist ein **Reasoner** (denkt in `<think>…</think>` im Content).
  Für Freitext braucht es einen Reasoning-Parser oder Nachbearbeitung —
  aber mit `response_format: json_schema` (unser `EndpointPool`-Standard)
  erzwingt Guided Decoding pures JSON ab Token 1; kein Think-Block, kein
  Parser nötig. Sanity-verifiziert.
- `EndpointPool` hält **einen Lock pro Endpoint** — gegen einen einzelnen
  vLLM-Server denselben Port mehrfach listen (`--ports 8130,8130,8130,8130`),
  sonst verschenkt man das Batching.

## 7. Plot-Layer-Ergebnis (gleiches Panel wie im GLM-Report)

Lauf: `runs/plot_layer_qwen38fn` (gleicher Prompt/Code wie v8/Muse; die
komplette Generierung inkl. Ketten und Self-Judge in **wenigen Minuten**
statt ~12 min bei Muse). Judging: 3× GLM-5.3-Panel, identische Rubric.

| Plot-Layer (Composer) | GLM-5.3-Panel | Schwächste Dim |
|---|---|---|
| plot_layer_muse (GLM-5.3) | **3.33** FAIL | P1 2.33 |
| plot_layer_v8 (Ornith, online) | 2.73 FAIL | P1/P5 2.00 |
| **plot_layer_qwen38fn (Qwen3.8)** | **2.07** FAIL | **P5 1.00** |

Selbst-Judge (Qwen über Qwen): 2.0 — deckungsgleich mit dem Panel, anders
als Orniths +1.9-Selbstinflation.

Der Fehlermodus ist eindeutig und bei allen drei Judges identisch: Qwen
baut zwei fast identische Ganzfilm-Nacherzählungen („Awakening" und
„Identity Crisis", 15 geteilte Events, 18 bzw. 21 Events über die volle
Spanne) statt disziplinierter Ein-Perspektiven-Stränge → P5=1, P2=2; die
Ketten sind zudem kausal schwach (P1=2).

**Fazit:** Qwen3.8-Flash-Next ist auf dieser Maschine der mit Abstand
schnellste große Composer (54 tok/s, 1300+ aggregiert), aber für die
Plot-Aufgabe in Rohform der schwächste der drei. Sinnvolle Rollen: hoher
Durchsatz für parallele Draft-/Panel-/Verify-Stufen, Judge-Zweitmeinung,
Massen-Generierung mit strengem Scaffold — nicht der Ein-Schuss-Composer
für die Perspektivstruktur.

## 8. Offen

- 2-GPU-Deployment: erst nach Merge von PLE-Offload (PR #53899) sinnvoll.
- MTP/Speculative Decoding ungetestet (potenziell weiterer Speedup).
- Qwen als Judge-Panel-Mitglied und als Draft-Stufe vor einem stärkeren
  Refiner ist unerprobt — angesichts des Durchsatzes der nächste
  interessante Versuch.
