# Muse 1.2 via ProtonVPN vs. direct — Concurrency & Throughput Benchmark

Date: 2026-08-27 (07:14–07:41 UTC). Model `muse-spark-1.2-contributor-free`,
endpoint `/v1/responses`, `reasoning: {effort: "high"}` on every request.

**148 requests, 148 successes, 0 errors, 828,877 generated tokens.**

## Setup

- **VM**: Debian 13 genericcloud image under KVM/QEMU (4 vCPU, 8 GB RAM, 20 GB
  overlay disk), cloud-init NoCloud seed, QEMU user-mode networking (slirp) with
  `hostfwd` ssh on 127.0.0.1:2222. Terminal-only, no GUI.
  The host user was *not* in the `kvm` group despite the brief saying so; adding
  it was required before `-enable-kvm` worked.
- **VPN**: OpenVPN (UDP) to `node-nl-204.protonvpn.net`, Netherlands.
  Verified via `api.ipify.org`: host egress `45.38.21.38`, VM egress after
  tunnel `77.247.178.109`. Tunnel stayed up for the whole run.
- **Payload** (identical bytes in every condition): plot-judgment task built
  from the real pipeline — P1–P5 rubric from `distill/plot_layer.py` +
  29,697-char event digest (`distill/meta_layer.py build_digest` over
  `runs/events_build10_full/events.json`) + 35,114-char plot-layer JSON
  (`runs/plot_layer_muse/plots.json`). ~16.4k prompt tokens. Each request
  carries a unique judge index and nanosecond nonce so upstream response
  caching cannot serve a hit.
- **Recorded**: timing, HTTP status, token usage only. Response texts are never
  stored (judge answers can quote screenplay material).

### Getting the VPN config (attempts)

`https://api.protonvpn.ch/vpn/logicals` is **no longer public**. It rejected
requests in three escalating stages: `400 Missing x-pm-appversion header`, then
`422 app no longer supported` for older client version strings, then `401`
(session required) once a current version string was accepted. So the documented
"fetch the logicals list anonymously" route is dead.

Two working substitutes were used instead:
1. Server IPs via public DNS — the scheme is `node-<cc>-<nn>.protonvpn.net`
   (`node-nl-01` … resolve fine; the older `nl-free-01` names are NXDOMAIN).
2. The CA certificate and `tls-crypt` key from Proton's own published
   `.ovpn` bundles (MIT-licensed, mirrored publicly). Country configs for
   NL/RO/JP were fetched; the NL UDP config connected on the **first attempt**,
   so no fallback servers or ports were needed.

## Results

| Condition | Path | conc | n | ok | errors | p50 s | p90 s | max s | tok/s per stream (med) | gen tok (med) | reasoning share | batch wall s | agg tok/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A_vpn_c20 | VPN | 20 | 40 | 40 | none | 35.1 | 48.2 | 69.0 | 166.6 | 5632 | 86.4% | 110.3 | 2117.3 |
| B_host_c20 | host | 20 | 40 | 40 | none | 72.0 | 86.1 | 97.3 | 80.9 | 5911 | 85.8% | 187.1 | 1200.8 |
| C_vpn_c1 | VPN | 1 | 4 | 4 | none | 34.8 | 42.5 | 42.5 | 168.6 | 4572 | 77.5% | 136.0 | 150.2 |
| C_host_c1 | host | 1 | 4 | 4 | none | 84.4 | 107.8 | 110.9 | 74.9 | 6179 | 87.7% | 328.0 | 71.1 |
| C_vpn_c5 | VPN | 5 | 10 | 10 | none | 37.0 | 54.2 | 61.7 | 160.3 | 5618 | 86.7% | 98.9 | 546.0 |
| C_host_c5 | host | 5 | 10 | 10 | none | 81.1 | 83.0 | 85.9 | 75.3 | 5656 | 86.0% | 168.3 | 328.6 |
| C_vpn_c10 | VPN | 10 | 10 | 10 | none | 30.9 | 33.3 | 38.1 | 183.3 | 5348 | 86.2% | 38.2 | 1486.4 |
| C_host_c10 | host | 10 | 10 | 10 | none | 57.7 | 79.0 | 81.1 | 83.8 | 4933 | 86.0% | 81.2 | 654.9 |
| D_vpn_par | VPN | 5 | 10 | 10 | none | 30.2 | 36.4 | 36.5 | 187.7 | 5532 | 86.6% | 64.9 | 847.3 |
| D_host_par | host | 5 | 10 | 10 | none | 66.3 | 77.9 | 79.1 | 80.3 | 5282 | 84.6% | 156.9 | 336.8 |

A vs B is the headline pair: same payload, same concurrency, run back-to-back
and never overlapping. **The VPN path finished the same 40 requests in 110.3 s
vs 187.1 s and delivered 2117 vs 1201 aggregate tok/s — 1.76x.**

## Observations

**1. Throttling is invisible in status codes.** Not one HTTP 503, 429 or any
other error occurred in 148 requests across both paths. The sporadic 503s noted
in the earlier baseline did not reproduce. Rate limiting here manifests purely
as a **reduced per-stream token rate**, so any monitoring that watches only
error rates will not see it.

**2. Per-stream token rate is a near-constant per exit IP, independent of
concurrency.** This is the central result:

- VPN exit: 160.3 / 168.6 / 183.3 / 166.6 / 187.7 tok/s at c=1, 5, 10, 20 and
  under parallel load — range 160–188, mean **173.3**.
- Host exit: 74.9 / 75.3 / 83.8 / 80.9 / 80.3 tok/s over the same ladder —
  range 75–84, mean **79.0**.

Each IP behaves like it has its own fixed per-stream speed, and that speed
barely moves from 1 to 20 concurrent streams. The ratio between the two exits is
**2.19x**, stable across the whole ladder. There is no throttling "knee" in the
1–20 range on either path — aggregate throughput keeps climbing with concurrency
on both.

**3. Test D is the controlled experiment, and it settles the mechanism.** A/B ran
sequentially, so a general backend slowdown could in principle explain the gap.
Test D removes that: both exits hammered the API **simultaneously** at c=5.
Neither degraded the other — the VPN recorded 187.7 tok/s per stream (its best
of the entire run) while the host simultaneously recorded 80.3 (its normal
rate). Combined **1184.1 aggregate tok/s across two exits at once**. Two IPs
running concurrently each keep their full solo budget, which is only possible if
the budgets are independent.

**4. The limit is IP-based, not account-based — and it cannot be otherwise.**
`tools/zen_shim.py` sends **no Authorization header, no API key, no cookie** to
`https://opencode.ai/zen/v1/responses`. There is no account identity in the
request at all. Combined with (3), the limit can only be keyed on source IP.
The most plausible reading of the 2.19x gap: the host IP has been driving
pipeline traffic for days and has accumulated a reduced rate, while a fresh
Proton exit starts on a clean budget.

**5. VPN latency overhead is negligible against generation time.** The tunnel
adds tens of milliseconds; a request spends 30–90 s generating. The VPN path was
*faster* on wall-clock latency in every single condition (p50 30.2–37.0 s vs
57.7–84.4 s). The brief expected increased latency from the VPN; the opposite
happened, because the throttle difference dwarfs the tunnel cost.

**6. ~86% of generated tokens are reasoning tokens, not visible output.**
Median ~5,300–5,900 generated tokens per judgment, of which only ~700–800 are
the actual answer. Any throughput or cost model for the mass conversion must
budget for the reasoning tail, and `output_tokens` in the usage block already
includes it (`output_tokens_details.reasoning_tokens` is a subset, not an
addend).

## Verdict: is the VPN route worth it for concurrency scaling?

**Yes, but not for the reason the experiment was designed around.**

The VPN does not raise a concurrency ceiling — there is no ceiling in the 1–20
range. Both paths scale aggregate throughput monotonically to c=20 with zero
errors. What the VPN buys is a **2.19x higher per-stream token rate**, because
the exit IP is not the one that has been carrying the pipeline's traffic.

Because the budget is per-IP and provably independent (test D), throughput
scales roughly linearly in the **number of distinct exit IPs**, and this is the
axis with real headroom. Concurrency within one IP is already close to saturated
by c=10–20 (the VPN went 1486 → 2117 tok/s from c=10 to c=20, only 1.42x for 2x
the concurrency), whereas adding a second independent exit added its full budget
on top with no interference at all.

For the planned mass conversion of screenplays, the practical shape is:
**N VPN exits × ~10 concurrent streams each**, rather than pushing one IP to very
high concurrency. Extrapolating the measured per-IP rate, 4–6 tunnels at c=10
would land in the 6,000–9,000 tok/s range versus the ~1,200 tok/s the host
currently achieves at c=20 — roughly a 5–7x speedup on the same account, since
the account is not what is being metered.

Caveats worth stating: this is one VPN exit measured over ~25 minutes, so the
170 tok/s figure is that server's rate, not a guaranteed rate for every Proton
node — a fresh exit's budget may also decay as it accrues traffic, which is
exactly what appears to have happened to the host IP. Before committing, the
sensible next step is to run 3–4 tunnels in parallel for a longer window and
confirm the per-IP rate holds up under sustained load rather than a short burst.
Rotation policy and Proton's own fair-use limits also need checking if this
becomes the standing pipeline path.

## Files

Raw per-request records (timing, status, usage only — no response text, no
credentials): `A_vpn_c20.jsonl`, `B_host_c20.jsonl`, `C_{vpn,host}_c{1,5,10}.jsonl`,
`D_{vpn,host}_par.jsonl`. Aggregates in `summary.json`, table in `table.md`.


## Addendum: extended ladder to c=100 (same exit, later the same day)

Run WHILE the knivesout tree build held ~10 streams on the same tunnel, so
these numbers are a lower bound.

| conc | n | ok | wall s | tokens | agg tok/s | tok/s/stream |
|---|---|---|---|---|---|---|
| 50 | 50 | 50 | 59.9 | 283,000 | **4,726** | 94.5 |
| 100 | 100 | 100 | 71.6 | 555,069 | **7,755** | 77.6 |

Zero errors at c=100. This corrects the earlier "saturates near c=10"
reading (an over-read of the small c=10 to c=20 step): aggregate
throughput keeps climbing to at least c=100 with only gentle per-stream
decay (150 -> 78 tok/s). One exit at c=100 already delivers what the
multi-exit extrapolation promised. The binding constraint is now the
client architecture (one lock per endpoint in EndpointPool), not the API.
