from .base import AwaitingAgent, Backend, BackendError, Usage, extract_json

__all__ = ["Backend", "BackendError", "AwaitingAgent", "Usage", "extract_json",
           "make_backend"]


def make_backend(name: str, **kwargs):
    if name == "hyprlab":
        from .hyprlab import HyprlabBackend
        return HyprlabBackend(**kwargs)
    if name == "agent":
        from .agent import AgentBackend
        return AgentBackend(**kwargs)
    raise ValueError(f"unknown backend {name!r} (expected 'hyprlab' or 'agent')")
