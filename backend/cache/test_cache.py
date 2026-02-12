"""
Test script for CacheService.
Run this in Django shell: python manage.py shell < cache/test_cache.py
Or copy-paste into Django shell.
"""

from cache.services import CacheService
from django.core.cache import cache
import json


def test_redis_connection():
    """Test if Redis is connected"""
    print("=" * 50)
    print("Testing Redis Connection")
    print("=" * 50)
    try:
        # Test basic cache operations
        test_key = "test:connection"
        test_value = "test_value"
        cache.set(test_key, test_value, timeout=10)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            print("✓ Redis connection: SUCCESS")
            cache.delete(test_key)
            return True
        else:
            print("✗ Redis connection: FAILED - Value mismatch")
            return False
    except Exception as e:
        print(f"✗ Redis connection: FAILED - {e}")
        return False


def test_cache_service_price():
    """Test price caching functionality"""
    print("\n" + "=" * 50)
    print("Testing Price Cache")
    print("=" * 50)
    
    service = CacheService()
    test_symbol = "EURUSD"
    test_data = {
        "symbol": test_symbol,
        "price": "1.0850",
        "bid": "1.0849",
        "ask": "1.0851",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    
    try:
        # Test SET
        print(f"Setting price for {test_symbol}...")
        service.set_price(test_symbol, test_data)
        print("✓ SET operation: SUCCESS")
        
        # Test GET
        print(f"Getting price for {test_symbol}...")
        retrieved = service.get_price(test_symbol)
        
        if retrieved is None:
            print("✗ GET operation: FAILED - No data retrieved")
            return False
        
        if retrieved == test_data:
            print("✓ GET operation: SUCCESS - Data matches")
        else:
            print("✗ GET operation: FAILED - Data mismatch")
            print(f"  Expected: {test_data}")
            print(f"  Got: {retrieved}")
            return False
        
        # Test TTL (check if key exists after setting)
        print("Checking TTL...")
        key = f"forex:price:{test_symbol}"
        ttl = cache.ttl(key)
        if ttl is not None and ttl > 0:
            print(f"✓ TTL: SUCCESS - Key expires in {ttl} seconds")
        else:
            print("⚠ TTL: WARNING - Could not retrieve TTL")
        
        return True
        
    except Exception as e:
        print(f"✗ Price cache test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_service_pairs():
    """Test active pairs caching functionality"""
    print("\n" + "=" * 50)
    print("Testing Active Pairs Cache")
    print("=" * 50)
    
    service = CacheService()
    test_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    
    try:
        # Test SET
        print("Setting active pairs...")
        service.set_active_pairs(test_pairs)
        print("✓ SET operation: SUCCESS")
        
        # Test GET
        print("Getting active pairs...")
        retrieved = service.get_active_pairs()
        
        if retrieved is None:
            print("✗ GET operation: FAILED - No data retrieved")
            return False
        
        if retrieved == test_pairs:
            print("✓ GET operation: SUCCESS - Data matches")
        else:
            print("✗ GET operation: FAILED - Data mismatch")
            print(f"  Expected: {test_pairs}")
            print(f"  Got: {retrieved}")
            return False
        
        # Test TTL
        print("Checking TTL...")
        key = "forex:pairs:active"
        ttl = cache.ttl(key)
        if ttl is not None and ttl > 0:
            print(f"✓ TTL: SUCCESS - Key expires in {ttl} seconds")
        else:
            print("⚠ TTL: WARNING - Could not retrieve TTL")
        
        return True
        
    except Exception as e:
        print(f"✗ Pairs cache test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_miss():
    """Test cache miss scenario"""
    print("\n" + "=" * 50)
    print("Testing Cache Miss")
    print("=" * 50)
    
    service = CacheService()
    non_existent_symbol = "NONEXISTENT"
    
    try:
        result = service.get_price(non_existent_symbol)
        if result is None:
            print("✓ Cache miss: SUCCESS - Returns None as expected")
            return True
        else:
            print(f"✗ Cache miss: FAILED - Expected None, got {result}")
            return False
    except Exception as e:
        print(f"✗ Cache miss test: FAILED - {e}")
        return False


def test_cache_expiry():
    """Test that cache expires correctly"""
    print("\n" + "=" * 50)
    print("Testing Cache Expiry (Price TTL)")
    print("=" * 50)
    
    service = CacheService()
    test_symbol = "TESTTTL"
    test_data = {"symbol": test_symbol, "price": "1.0000"}
    
    try:
        # Set with short TTL
        service.set_price(test_symbol, test_data)
        print(f"Set price for {test_symbol}")
        
        # Check immediately
        result = service.get_price(test_symbol)
        if result is not None:
            print("✓ Cache exists immediately after setting")
        else:
            print("✗ Cache not found immediately after setting")
            return False
        
        # Check TTL
        key = f"forex:price:{test_symbol}"
        ttl = cache.ttl(key)
        print(f"TTL: {ttl} seconds (expected: {CacheService.PRICE_TTL})")
        
        if ttl <= CacheService.PRICE_TTL:
            print("✓ TTL: SUCCESS - Correct expiration time")
        else:
            print("⚠ TTL: WARNING - TTL seems incorrect")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache expiry test: FAILED - {e}")
        return False


def run_all_tests():
    """Run all cache tests"""
    print("\n" + "=" * 50)
    print("CACHE SERVICE TEST SUITE")
    print("=" * 50)
    
    results = []
    
    # Test 1: Redis Connection
    results.append(("Redis Connection", test_redis_connection()))
    
    # Test 2: Price Cache
    results.append(("Price Cache", test_cache_service_price()))
    
    # Test 3: Pairs Cache
    results.append(("Active Pairs Cache", test_cache_service_pairs()))
    
    # Test 4: Cache Miss
    results.append(("Cache Miss", test_cache_miss()))
    
    # Test 5: Cache Expiry
    results.append(("Cache Expiry", test_cache_expiry()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    # This allows running directly, but Django shell is preferred
    import os
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()
    
    run_all_tests()
