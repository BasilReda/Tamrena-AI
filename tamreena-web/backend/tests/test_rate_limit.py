import time

from app.rate_limit import RateLimiter


def test_allows_requests_under_the_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.check("user-1") is True
    assert limiter.check("user-1") is True
    assert limiter.check("user-1") is True


def test_rejects_requests_over_the_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    assert limiter.check("user-1") is True
    assert limiter.check("user-1") is True
    assert limiter.check("user-1") is False


def test_limit_is_tracked_independently_per_key():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.check("user-1") is True
    assert limiter.check("user-2") is True  # different key, unaffected by user-1's usage


def test_old_requests_fall_out_of_the_window():
    limiter = RateLimiter(max_requests=1, window_seconds=0.05)
    assert limiter.check("user-1") is True
    assert limiter.check("user-1") is False
    time.sleep(0.06)
    assert limiter.check("user-1") is True
