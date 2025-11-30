from typing import Type

from .base import PaginationStrategy


class StrategyRegistry:
    """Registry for pagination strategies."""

    _strategies: dict[str, Type[PaginationStrategy]] = {}

    @classmethod
    def register(cls, name: str, strategy_cls: Type[PaginationStrategy]) -> None:
        """Register a new strategy."""
        cls._strategies[name] = strategy_cls

    @classmethod
    def get(cls, name: str) -> Type[PaginationStrategy]:
        """Get a strategy by name."""
        if name not in cls._strategies:
            raise ValueError(f"Strategy '{name}' not found in registry.")
        return cls._strategies[name]

    @classmethod
    def list_strategies(cls) -> list[str]:
        """List all registered strategies."""
        return list(cls._strategies.keys())
