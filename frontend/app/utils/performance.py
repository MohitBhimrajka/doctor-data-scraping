import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import time
from functools import wraps
import asyncio
from collections import deque
import threading

class Cache:
    """Simple in-memory cache with TTL."""
    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            data = self.cache[key]
            if time.time() - data['timestamp'] < self.ttl:
                return data['value']
            del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self.cache[key] = {
            'value': value,
            'timestamp': time.time()
        }

    def clear(self) -> None:
        self.cache.clear()

class RequestQueue:
    """Queue for managing API requests."""
    def __init__(self, max_concurrent: int = 3):
        self.queue = deque()
        self.running = False
        self.max_concurrent = max_concurrent
        self.lock = threading.Lock()

    async def add_request(self, coro: Callable) -> Any:
        with self.lock:
            self.queue.append(coro)
            if not self.running:
                self.running = True
                asyncio.create_task(self._process_queue())
        return await self._wait_for_result(coro)

    async def _process_queue(self) -> None:
        while self.queue:
            tasks = []
            for _ in range(min(self.max_concurrent, len(self.queue))):
                if self.queue:
                    coro = self.queue.popleft()
                    tasks.append(asyncio.create_task(coro))
            if tasks:
                await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)  # Prevent CPU spinning
        self.running = False

    async def _wait_for_result(self, coro: Callable) -> Any:
        return await coro

def debounce(wait_time: float = 0.5):
    """Decorator to debounce function calls."""
    def decorator(fn):
        timer = None
        def debounced(*args, **kwargs):
            nonlocal timer
            if timer is not None:
                timer.cancel()
            timer = asyncio.create_task(asyncio.sleep(wait_time))
            return fn(*args, **kwargs)
        return debounced
    return decorator

class VirtualScroll:
    """Virtual scrolling for large datasets."""
    def __init__(self, items: List[Any], page_size: int = 10):
        self.items = items
        self.page_size = page_size
        self.current_page = 0

    def get_page(self, page: int) -> List[Any]:
        start = page * self.page_size
        end = start + self.page_size
        return self.items[start:end]

    def get_total_pages(self) -> int:
        return (len(self.items) + self.page_size - 1) // self.page_size

def optimize_chart_data(data: Dict[str, Any], max_points: int = 100) -> Dict[str, Any]:
    """Optimize chart data by reducing points."""
    if len(data.get('x', [])) > max_points:
        step = len(data['x']) // max_points
        return {
            'x': data['x'][::step],
            'y': data['y'][::step]
        }
    return data

def memoize(func: Callable) -> Callable:
    """Decorator to memoize function results."""
    cache = {}
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper 