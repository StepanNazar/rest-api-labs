import asyncio
import threading
from typing import Any, Coroutine


class AsyncBridge:
    """Bridges synchronous code to an asynchronous event loop running in a background thread."""

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        """Run the event loop in the background thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run a coroutine in the background event loop and return the result.

        Args:
            coro: The coroutine to execute.

        Returns:
            The result of the coroutine.
        """
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()


bridge = AsyncBridge()
