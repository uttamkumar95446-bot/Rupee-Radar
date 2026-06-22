"""Rate limiter for LLM API calls.

Respects Groq free-tier limits for llama-3.3-70b-versatile:
  - Max 30 requests per minute
  - Max 100K tokens per day

Provides token estimation before each call and enforces
both the request rate and daily token budget.

Thread-safe via threading.Lock. Auto-resets daily.
"""

import logging
import threading
import time
from collections import deque
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

# ── Rate Limits ──
MAX_REQUESTS_PER_MINUTE = 30
MAX_TOKENS_PER_DAY = 100_000
SAFETY_BUFFER_REQUESTS = 2  # Reserve 2 requests/min buffer
SAFETY_BUFFER_TOKENS = 5_000  # Reserve 5K token buffer
EFFECTIVE_MAX_REQUESTS = MAX_REQUESTS_PER_MINUTE - SAFETY_BUFFER_REQUESTS
EFFECTIVE_MAX_TOKENS = MAX_TOKENS_PER_DAY - SAFETY_BUFFER_TOKENS

# ── Token Estimation Heuristics ──
# Rough: 1 token ≈ 4 characters for English text
CHARS_PER_TOKEN = 4.0

# Average output tokens to expect per response type
ESTIMATED_OUTPUT_TOKENS = {
    "categorize": 200,  # JSON array of categories for a batch
    "insights": 300,    # JSON with 3-5 insights
}


def estimate_tokens(messages: list[dict]) -> int:
    """Estimate the number of tokens for a list of messages.

    Uses a simple character-count heuristic:
      - 1 token ≈ 4 characters for English text
      - Adds estimated output tokens

    Args:
        messages: List of message dicts with 'role' and 'content' keys.

    Returns:
        Estimated total token count (input + estimated output).
    """
    if not messages:
        return 0

    total_chars = 0
    for msg in messages:
        content = msg.get("content", "")
        total_chars += len(str(content))

    # Role overhead (~4 tokens per message for metadata)
    overhead_tokens = len(messages) * 4

    input_tokens = int(total_chars / CHARS_PER_TOKEN) + overhead_tokens

    # Determine context from message content to estimate output tokens
    last_content = str(messages[-1].get("content", "")) if messages else ""
    if "Categorize these transactions" in last_content:
        output_tokens = ESTIMATED_OUTPUT_TOKENS["categorize"]
    elif "Generate" in last_content and "insights" in last_content:
        output_tokens = ESTIMATED_OUTPUT_TOKENS["insights"]
    else:
        output_tokens = 200  # conservative default

    return input_tokens + output_tokens


class LLMRateLimiter:
    """Tracks and enforces LLM API rate limits.

    Thread-safe via threading.Lock. Auto-resets daily counters
    when the calendar date changes.

    Singleton pattern — use module-level instance via get_limiter().
    """

    def __init__(self):
        self._lock = threading.Lock()

        self._request_timestamps: deque[float] = deque()
        self._tokens_used_today: int = 0
        self._total_requests_made: int = 0
        self._budget_exhausted: bool = False
        self._last_warning_pct: float = 0.0

        # Date tracking for auto-reset
        self._current_date: date = date.today()

    # ── Public API ──

    def check_budget(self, estimated_tokens: int) -> bool:
        """Check whether the daily token budget allows this request.

        Thread-safe. Auto-resets if the date has changed since last check.

        Args:
            estimated_tokens: Estimated tokens for the upcoming request.

        Returns:
            True if the budget allows the request, False if exhausted.
        """
        with self._lock:
            self._auto_reset_if_new_day()

            if self._budget_exhausted:
                return False

            projected = self._tokens_used_today + estimated_tokens
            if projected > EFFECTIVE_MAX_TOKENS:
                logger.warning(
                    f"Daily token budget exhausted: "
                    f"{self._tokens_used_today:,}/{EFFECTIVE_MAX_TOKENS:,} used, "
                    f"requested ~{estimated_tokens:,}. "
                    f"Falling back to rule-based processing."
                )
                self._budget_exhausted = True
                return False

            return True

    def wait_if_needed(self) -> None:
        """Block until the request rate limit allows a new request.

        In async contexts, this uses asyncio.sleep for non-blocking waits.
        In sync contexts, it falls back to time.sleep.

        Enforces max EFFECTIVE_MAX_REQUESTS per rolling 60-second window.
        If at the limit, waits until the oldest timestamp expires + buffer.
        """
        with self._lock:
            self._auto_reset_if_new_day()
            now = time.time()

            # Prune timestamps older than 60 seconds
            while self._request_timestamps and now - self._request_timestamps[0] > 60:
                self._request_timestamps.popleft()

            if len(self._request_timestamps) >= EFFECTIVE_MAX_REQUESTS:
                oldest = self._request_timestamps[0]
                wait_time = 60.0 - (now - oldest) + 0.5  # +0.5s buffer
            else:
                wait_time = 0.0

        # Perform the wait outside the lock so other threads can proceed
        if wait_time > 0:
            logger.info(
                f"Rate limit reached ({len(self._request_timestamps)} requests "
                f"in last minute). Waiting {wait_time:.1f}s..."
            )
            self._sleep(wait_time)

        with self._lock:
            self._request_timestamps.append(time.time())

    def record_usage(self, tokens_used: int) -> None:
        """Record token usage after a successful API call.

        Thread-safe. Issues warnings at 50%, 75%, and 90% thresholds.

        Args:
            tokens_used: Actual tokens used (from API response if available),
                         or estimated tokens if actual is not available.
        """
        with self._lock:
            self._auto_reset_if_new_day()
            self._tokens_used_today += tokens_used
            self._total_requests_made += 1

            # Log warnings at thresholds
            usage_pct = (self._tokens_used_today / EFFECTIVE_MAX_TOKENS) * 100
            if usage_pct >= 90 and self._last_warning_pct < 90:
                logger.warning(
                    f"Daily token budget critically low: {usage_pct:.0f}% used "
                    f"({self._tokens_used_today:,}/{EFFECTIVE_MAX_TOKENS:,})."
                )
                self._last_warning_pct = 90
            elif usage_pct >= 75 and self._last_warning_pct < 75:
                logger.warning(
                    f"Daily token budget at {usage_pct:.0f}% "
                    f"({self._tokens_used_today:,}/{EFFECTIVE_MAX_TOKENS:,}). "
                    f"~{self.tokens_remaining:,} tokens remaining."
                )
                self._last_warning_pct = 75
            elif usage_pct >= 50 and self._last_warning_pct < 50:
                logger.info(
                    f"Daily token budget at {usage_pct:.0f}% "
                    f"({self._tokens_used_today:,}/{EFFECTIVE_MAX_TOKENS:,})."
                )
                self._last_warning_pct = 50

    # ── Properties ──

    @property
    def tokens_remaining(self) -> int:
        """Tokens remaining in the daily budget."""
        with self._lock:
            self._auto_reset_if_new_day()
            return max(0, EFFECTIVE_MAX_TOKENS - self._tokens_used_today)

    @property
    def requests_in_window(self) -> int:
        """Number of requests in the current 60-second window."""
        with self._lock:
            now = time.time()
            while self._request_timestamps and now - self._request_timestamps[0] > 60:
                self._request_timestamps.popleft()
            return len(self._request_timestamps)

    @property
    def budget_exhausted(self) -> bool:
        """Whether the daily budget has been exhausted."""
        with self._lock:
            self._auto_reset_if_new_day()
            return self._budget_exhausted

    # ── Internal ──

    def _auto_reset_if_new_day(self) -> None:
        """Reset daily counters if the calendar date has changed.

        Called automatically before any budget/rate check.
        """
        today = date.today()
        if today > self._current_date:
            old_date = self._current_date
            old_tokens = self._tokens_used_today
            self._tokens_used_today = 0
            self._total_requests_made = 0
            self._budget_exhausted = False
            self._last_warning_pct = 0.0
            self._current_date = today
            self._request_timestamps.clear()
            logger.info(
                f"Daily token budget auto-reset: {old_date} → {today} "
                f"({old_tokens:,} tokens used previously)."
            )

    @staticmethod
    def _sleep(seconds: float) -> None:
        """Sleep for the given duration.

        Uses time.sleep since all LLM callers (categorize_transactions
        and generate_insights) use synchronous Groq/OpenAI clients.
        """
        time.sleep(seconds)

    def reset_daily(self) -> None:
        """Force-reset all daily counters (for testing or manual reset)."""
        with self._lock:
            old_tokens = self._tokens_used_today
            self._tokens_used_today = 0
            self._total_requests_made = 0
            self._budget_exhausted = False
            self._last_warning_pct = 0.0
            self._current_date = date.today()
            self._request_timestamps.clear()
            logger.info(
                f"Daily token budget manually reset "
                f"({old_tokens:,} tokens used previously)."
            )

    def __repr__(self) -> str:
        return (
            f"LLMRateLimiter(requests={self.requests_in_window}/{EFFECTIVE_MAX_REQUESTS}/min, "
            f"tokens={self._tokens_used_today:,}/{EFFECTIVE_MAX_TOKENS:,}/day, "
            f"exhausted={self._budget_exhausted})"
        )


# ── Module-level singleton ──
_limiter: Optional[LLMRateLimiter] = None


def get_limiter() -> LLMRateLimiter:
    """Get or create the shared rate limiter instance."""
    global _limiter
    if _limiter is None:
        _limiter = LLMRateLimiter()
        logger.info(
            f"Rate limiter initialized: {EFFECTIVE_MAX_REQUESTS} req/min, "
            f"{EFFECTIVE_MAX_TOKENS:,} tokens/day"
        )
    return _limiter
