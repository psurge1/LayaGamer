"""Shared agent result types."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    action: str
    metadata: dict
