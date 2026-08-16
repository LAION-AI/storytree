"""distill — an author/judge loop that reconstructs the hidden narrative
architecture of a finished screenplay and stores every artifact, critique,
revision and hindsight trace as fine-tuning data.

Reuses `narrativeforge` (schemas, craft sheet, plot embedding, backends, JSON
Patch) and `reconstruct.scriptforge` (screenplay parser, envelopes). It forks
neither.

See distill/WHITEPAPER.md.
"""

__all__ = ["promptlib", "rubric", "store", "loop", "nodes", "estimate"]
__version__ = "0.1.0"
