# Quick Cache Service Testing Guide

## Method 1: Django Management Command (Recommended)

Run the comprehensive test suite:
```bash
cd backend
python manage.py test_cache
```

## Method 2: Django Shell

Open Django shell and run tests:
```bash
cd backend
python manage.py shell
```

Then in the shell:
```python
# Import the test function
from cache.test_cache import run_all_tests

# Run all tests
run_all_tests()
```

## Method 3: Quick Manual Test in Django Shell

```python
from cache.services import CacheService
from django.core.cache import cache

# Create service instance
service = CacheService()

# Test 1: Check Redis connection
cache.set("test", "value", timeout=10)
print("Redis connected:", cache.get("test") == "value")
cache.delete("test")

# Test 2: Test price caching
test_price = {
    "symbol": "EURUSD",
    "price": "1.0850",
    "bid": "1.0849",
    "ask": "1.0851",
    "timestamp": "2024-01-01T12:00:00Z"
}

service.set_price("EURUSD", test_price)
retrieved = service.get_price("EURUSD")
print("Price cache works:", retrieved == test_price)

# Test 3: Test pairs caching
test_pairs = ["EURUSD", "GBPUSD", "USDJPY"]
service.set_active_pairs(test_pairs)
retrieved_pairs = service.get_active_pairs()
print("Pairs cache works:", retrieved_pairs == test_pairs)

# Test 4: Check TTL
from django.core.cache import cache
ttl = cache.ttl("forex:price:EURUSD")
print(f"Price TTL: {ttl} seconds (expected: {CacheService.PRICE_TTL})")
```

## Method 4: Check Redis Directly

If you have redis-cli installed:
```bash
redis-cli

# In redis-cli:
KEYS forex:*
GET forex:price:EURUSD
TTL forex:price:EURUSD
```

## Troubleshooting

### Redis Connection Issues
- Check if Redis is running: `redis-cli ping` (should return "PONG")
- Verify REDIS_URL in your .env file
- Check if django-redis is installed: `pip list | grep django-redis`

### Cache Not Working
- Check Django logs for warnings
- Verify CACHES setting in settings.py
- Test basic cache: `from django.core.cache import cache; cache.set("test", "ok"); print(cache.get("test"))`
