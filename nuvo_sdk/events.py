"""Event subscription system for NuVo client."""

import asyncio
from typing import Callable, List
from .models import StateChangeEvent


class EventManager:
    """Manages event subscriptions and distribution."""

    def __init__(self):
        self._subscribers: List[Callable[[StateChangeEvent], None]] = []

    def subscribe(self, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Subscribe to state change events.

        Args:
            callback: Function to call with StateChangeEvent
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[StateChangeEvent], None]) -> None:
        """
        Unsubscribe from state change events.

        Args:
            callback: Function to remove
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def notify(self, event: StateChangeEvent) -> None:
        """
        Notify all subscribers of an event.

        Args:
            event: StateChangeEvent to distribute
        """
        for callback in self._subscribers:
            try:
                # Handle both sync and async callbacks
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                # Don't let subscriber errors break the event system
                print(f"Error in event subscriber: {e}")

    def clear(self) -> None:
        """Remove all subscribers."""
        self._subscribers.clear()
