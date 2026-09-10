"""FinOps and Operational Guardrail Manager for LLM / Amazon Bedrock.

Enforces:
1. $100/month hard cost ceiling and kill switch.
2. Token/input limits (input character truncation, max output token capping).
3. Usage limits (daily request cap) and rate limiting (per-minute burst control).
4. Circuit breaker for 429 Throttling / ServiceQuotaExceeded errors (cooldown backoff).
5. Request deduplication / caching to eliminate redundant billable calls.
"""

import time
import hashlib
import logging
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMGuardrailError(Exception):
    """Base exception for LLM guardrail violations."""
    pass


class LLMBudgetExceededError(LLMGuardrailError):
    """Raised when monthly budget ceiling is reached."""
    pass


class LLMRateLimitExceededError(LLMGuardrailError):
    """Raised when per-minute request rate is exceeded."""
    pass


class LLMDailyLimitExceededError(LLMGuardrailError):
    """Raised when daily total request limit is exceeded."""
    pass


class LLMCircuitBreakerActiveError(LLMGuardrailError):
    """Raised when LLM calls are temporarily paused due to upstream throttling."""
    pass


class FinOpsGuardrailManager:
    """Manages financial budgets, rate limits, circuit breakers, and caches for LLM calls."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(FinOpsGuardrailManager, cls).__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        """Initialize in-memory trackers."""
        self._state_lock = threading.Lock()
        now = datetime.now(timezone.utc)
        self._current_month = now.strftime("%Y-%m")
        self._current_day = now.strftime("%Y-%m-%d")

        # Monthly metrics ($100 budget cap)
        self.monthly_estimated_cost_usd: float = 0.0
        self.monthly_input_tokens: int = 0
        self.monthly_output_tokens: int = 0
        self.monthly_requests: int = 0

        # Daily metrics
        self.daily_requests: int = 0

        # Rate limiting: sliding window of timestamps (epoch seconds)
        self._request_timestamps = []

        # Circuit breaker
        self._circuit_breaker_until: float = 0.0
        self._circuit_breaker_reason: str = ""

        # In-memory response cache: hash -> (response_text, expiry_epoch)
        self._cache: Dict[str, Tuple[str, float]] = {}

    def _check_and_roll_dates(self):
        """Roll over counters when month or day changes."""
        now = datetime.now(timezone.utc)
        month_str = now.strftime("%Y-%m")
        day_str = now.strftime("%Y-%m-%d")

        if month_str != self._current_month:
            logger.info(f"New billing month detected ({month_str}). Resetting monthly Bedrock counters.")
            self._current_month = month_str
            self.monthly_estimated_cost_usd = 0.0
            self.monthly_input_tokens = 0
            self.monthly_output_tokens = 0
            self.monthly_requests = 0

        if day_str != self._current_day:
            logger.info(f"New day detected ({day_str}). Resetting daily Bedrock request counter.")
            self._current_day = day_str
            self.daily_requests = 0

    def check_and_acquire(self) -> None:
        """Pre-flight check before any Bedrock LLM invocation.

        Raises:
            LLMCircuitBreakerActiveError: If in circuit breaker cooldown.
            LLMBudgetExceededError: If monthly spend has reached or breached budget.
            LLMDailyLimitExceededError: If daily call volume limit is exceeded.
            LLMRateLimitExceededError: If requests per minute exceeds burst threshold.
        """
        settings = get_settings()
        now_ts = time.time()

        with self._state_lock:
            self._check_and_roll_dates()

            # 1. Circuit Breaker Check
            if now_ts < self._circuit_breaker_until:
                remaining = int(self._circuit_breaker_until - now_ts)
                msg = (
                    f"Bedrock circuit breaker active for next {remaining}s due to upstream error: "
                    f"'{self._circuit_breaker_reason}'. Falling back to deterministic knowledge base."
                )
                logger.warning(msg)
                raise LLMCircuitBreakerActiveError(msg)

            # 2. Hard Cost Budget Ceiling Check ($100 / month)
            if self.monthly_estimated_cost_usd >= settings.llm_monthly_budget_usd:
                msg = (
                    f"Monthly LLM budget of ${settings.llm_monthly_budget_usd:.2f} reached "
                    f"(Current spent: ${self.monthly_estimated_cost_usd:.2f}). "
                    f"Invocations halted to prevent financial impact."
                )
                logger.error(msg)
                raise LLMBudgetExceededError(msg)

            # 3. Daily Usage Limit Check
            if self.daily_requests >= settings.llm_daily_request_limit:
                msg = (
                    f"Daily LLM request limit ({settings.llm_daily_request_limit} reqs/day) reached "
                    f"(Today: {self.daily_requests})."
                )
                logger.warning(msg)
                raise LLMDailyLimitExceededError(msg)

            # 4. Per-Minute Rate Limiting (Sliding Window)
            one_minute_ago = now_ts - 60.0
            self._request_timestamps = [ts for ts in self._request_timestamps if ts > one_minute_ago]
            if len(self._request_timestamps) >= settings.llm_rate_limit_per_minute:
                msg = (
                    f"LLM rate limit ({settings.llm_rate_limit_per_minute} req/min) exceeded. "
                    f"Throttling request to avoid quota exhaustion."
                )
                logger.warning(msg)
                raise LLMRateLimitExceededError(msg)

            # Acquire permit
            self._request_timestamps.append(now_ts)
            self.daily_requests += 1
            self.monthly_requests += 1

    def record_usage(self, input_tokens: int, output_tokens: int) -> float:
        """Record token consumption and update estimated monthly spend.

        Returns:
            Estimated incremental cost for this invocation in USD.
        """
        settings = get_settings()
        cost_in = (input_tokens / 1000.0) * settings.llm_cost_per_1k_input_tokens
        cost_out = (output_tokens / 1000.0) * settings.llm_cost_per_1k_output_tokens
        call_cost = cost_in + cost_out

        with self._state_lock:
            self.monthly_input_tokens += input_tokens
            self.monthly_output_tokens += output_tokens
            self.monthly_estimated_cost_usd += call_cost

            logger.info(
                f"LLM Usage Recorded: +{input_tokens} in / +{output_tokens} out tokens. "
                f"Call cost: ${call_cost:.5f}. Total Month: ${self.monthly_estimated_cost_usd:.4f} / ${settings.llm_monthly_budget_usd:.2f}"
            )

        return call_cost

    def trip_circuit_breaker(self, reason: str) -> None:
        """Trip circuit breaker to pause requests when AWS throttles or breaches quotas."""
        settings = get_settings()
        cooldown = settings.llm_circuit_breaker_cooldown_seconds
        with self._state_lock:
            self._circuit_breaker_until = time.time() + cooldown
            self._circuit_breaker_reason = reason
            logger.warning(f"Circuit breaker tripped for {cooldown}s: {reason}")

    def truncate_input(self, text: str) -> str:
        """Enforce maximum input character limit to prevent large prompt cost spikes."""
        settings = get_settings()
        max_chars = settings.llm_max_input_chars
        if len(text) > max_chars:
            logger.warning(f"Input truncated from {len(text)} to {max_chars} chars to enforce input guardrail.")
            return text[:max_chars] + "\n\n[Context truncated by Guardrail]"
        return text

    def clamp_max_tokens(self, requested_tokens: int) -> int:
        """Enforce maximum output token ceiling."""
        settings = get_settings()
        return min(requested_tokens, settings.llm_max_output_tokens)

    def compute_cache_key(self, model_id: str, system_prompt: str, user_message: str) -> str:
        """Compute deterministic cache key for prompt deduplication."""
        hasher = hashlib.sha256()
        hasher.update(model_id.encode('utf-8'))
        hasher.update(b"::")
        hasher.update(system_prompt.strip().encode('utf-8'))
        hasher.update(b"::")
        hasher.update(user_message.strip().encode('utf-8'))
        return hasher.hexdigest()

    def get_cached_response(self, cache_key: str) -> Optional[str]:
        """Check if response is already cached."""
        now = time.time()
        with self._state_lock:
            item = self._cache.get(cache_key)
            if item:
                text, expiry = item
                if now < expiry:
                    return text
                else:
                    del self._cache[cache_key]
        return None

    def set_cached_response(self, cache_key: str, response: str, ttl: int = 3600) -> None:
        """Store response in cache to avoid repeating identical LLM calls."""
        now = time.time()
        with self._state_lock:
            # Simple purge of expired items if cache grows large
            if len(self._cache) > 2000:
                self._cache = {k: v for k, v in self._cache.items() if v[1] > now}
            self._cache[cache_key] = (response, now + ttl)

    def get_status(self) -> Dict[str, Any]:
        """Return current status of guardrails for monitoring / admin dashboard."""
        settings = get_settings()
        now = time.time()
        with self._state_lock:
            cb_active = now < self._circuit_breaker_until
            remaining_cb = int(self._circuit_breaker_until - now) if cb_active else 0
            return {
                "billing_month": self._current_month,
                "monthly_budget_usd": settings.llm_monthly_budget_usd,
                "monthly_spent_usd": round(self.monthly_estimated_cost_usd, 4),
                "budget_used_percent": round((self.monthly_estimated_cost_usd / max(settings.llm_monthly_budget_usd, 1.0)) * 100, 2),
                "monthly_requests": self.monthly_requests,
                "monthly_input_tokens": self.monthly_input_tokens,
                "monthly_output_tokens": self.monthly_output_tokens,
                "daily_requests": self.daily_requests,
                "daily_request_limit": settings.llm_daily_request_limit,
                "rate_limit_per_minute": settings.llm_rate_limit_per_minute,
                "circuit_breaker_active": cb_active,
                "circuit_breaker_cooldown_remaining_seconds": remaining_cb,
                "circuit_breaker_reason": self._circuit_breaker_reason if cb_active else None
            }


# Singleton instance
guardrails = FinOpsGuardrailManager()
