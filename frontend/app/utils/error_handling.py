import streamlit as st
from typing import Optional, Dict, Any, Callable
import asyncio
from functools import wraps
import logging
from datetime import datetime

class ErrorTracker:
    """Track and report errors."""
    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.max_errors = 100

    def add_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'message': str(error),
            'context': context or {}
        }
        self.errors.append(error_data)
        if len(self.errors) > self.max_errors:
            self.errors.pop(0)
        logging.error(f"Error: {error_data}")

    def get_errors(self) -> List[Dict[str, Any]]:
        return self.errors

    def clear_errors(self) -> None:
        self.errors.clear()

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry failed operations."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator

def handle_api_error(error: Exception) -> str:
    """Handle API errors and return user-friendly messages."""
    error_messages = {
        'ConnectionError': 'Unable to connect to the server. Please check your internet connection.',
        'TimeoutError': 'Request timed out. Please try again.',
        'HTTPError': 'Server error occurred. Please try again later.',
        'ValidationError': 'Invalid input data. Please check your search criteria.',
        'NotFoundError': 'No results found for your search criteria.',
    }
    error_type = type(error).__name__
    return error_messages.get(error_type, 'An unexpected error occurred. Please try again.')

def graceful_degradation(func: Callable):
    """Decorator to implement graceful degradation."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            st.error(handle_api_error(e))
            return None
    return wrapper

class ErrorBoundary:
    """Context manager for error handling."""
    def __init__(self, error_handler: Optional[Callable] = None):
        self.error_handler = error_handler or handle_api_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            st.error(self.error_handler(exc_val))
            return True
        return False

def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log error with context."""
    logging.error(f"Error: {str(error)}", extra={
        'context': context or {},
        'timestamp': datetime.now().isoformat()
    })

def show_error_message(error: Exception, error_type: str = "error") -> None:
    """Show styled error message."""
    message = handle_api_error(error)
    st.markdown(f"""
        <div style="
            padding: 10px;
            border-radius: 5px;
            background-color: rgba(255, 107, 107, 0.1);
            color: #FF6B6B;
            margin: 10px 0;
        ">
            {message}
        </div>
    """, unsafe_allow_html=True) 