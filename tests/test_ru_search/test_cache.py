"""
Comprehensive tests for cache functionality.

This module tests the SearchCache class including:
- Cache hit/miss behavior
- TTL expiration
- Thread safety
- Key generation
- Cache clearing
"""

import pytest
import time
import threading
from src.ru_search.cache import SearchCache


class TestSearchCache:
    """Test suite for SearchCache class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.cache = SearchCache(ttl=2)  # Short TTL for testing
        
    def test_cache_initialization(self):
        """Test cache initialization."""
        assert self.cache.ttl == 2
        assert isinstance(self.cache._cache, dict)
        assert len(self.cache._cache) == 0

    def test_make_key(self):
        """Test cache key generation."""
        key1 = self.cache._make_key("wildberries", "телефон")
        key2 = self.cache._make_key("wildberries", "телефон")
        key3 = self.cache._make_key("ozon", "телефон")
        key4 = self.cache._make_key("wildberries", "смартфон")
        
        # Same source and query should produce same key
        assert key1 == key2
        
        # Different source should produce different key
        assert key1 != key3
        
        # Different query should produce different key
        assert key1 != key4
        
        # Key format should be "source:hash"
        assert ":" in key1
        assert len(key1.split(":")) == 2

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        test_data = {"products": [{"id": 1, "name": "test"}], "timestamp": time.time()}
        
        # Set data
        self.cache.set("wildberries", "телефон", test_data)
        
        # Get data
        cached_data = self.cache.get("wildberries", "телефон")
        
        assert cached_data == test_data
        assert len(self.cache._cache) == 1

    def test_cache_miss(self):
        """Test cache miss behavior."""
        # Try to get non-existent data
        cached_data = self.cache.get("wildberries", "телефон")
        
        assert cached_data is None

    def test_cache_expiration(self):
        """Test TTL-based cache expiration."""
        test_data = {"products": [{"id": 1, "name": "test"}], "timestamp": time.time()}
        
        # Set data
        self.cache.set("wildberries", "телефон", test_data)
        
        # Should be available immediately
        cached_data = self.cache.get("wildberries", "телефон")
        assert cached_data == test_data
        
        # Wait for expiration (TTL is 2 seconds)
        time.sleep(3)
        
        # Should be expired and return None
        cached_data = self.cache.get("wildberries", "телефон")
        assert cached_data is None
        
        # Cache should be empty after expiration
        assert len(self.cache._cache) == 0

    def test_cache_multiple_entries(self):
        """Test multiple cache entries."""
        test_data1 = {"products": [{"id": 1, "name": "test1"}]}
        test_data2 = {"products": [{"id": 2, "name": "test2"}]}
        test_data3 = {"products": [{"id": 3, "name": "test3"}]}
        
        # Set multiple entries
        self.cache.set("wildberries", "телефон", test_data1)
        self.cache.set("ozon", "телефон", test_data2)
        self.cache.set("wildberries", "смартфон", test_data3)
        
        # Verify all entries are stored
        assert len(self.cache._cache) == 3
        
        # Verify each entry can be retrieved
        assert self.cache.get("wildberries", "телефон") == test_data1
        assert self.cache.get("ozon", "телефон") == test_data2
        assert self.cache.get("wildberries", "смартфон") == test_data3

    def test_cache_overwrite(self):
        """Test cache entry overwriting."""
        test_data1 = {"products": [{"id": 1, "name": "test1"}]}
        test_data2 = {"products": [{"id": 2, "name": "test2"}]}
        
        # Set initial data
        self.cache.set("wildberries", "телефон", test_data1)
        assert self.cache.get("wildberries", "телефон") == test_data1
        
        # Overwrite with new data
        self.cache.set("wildberries", "телефон", test_data2)
        assert self.cache.get("wildberries", "телефон") == test_data2
        
        # Should still have only one entry
        assert len(self.cache._cache) == 1

    def test_cache_clear(self):
        """Test cache clearing."""
        test_data1 = {"products": [{"id": 1, "name": "test1"}]}
        test_data2 = {"products": [{"id": 2, "name": "test2"}]}
        
        # Set multiple entries
        self.cache.set("wildberries", "телефон", test_data1)
        self.cache.set("ozon", "телефон", test_data2)
        assert len(self.cache._cache) == 2
        
        # Clear cache
        self.cache.clear()
        
        # Cache should be empty
        assert len(self.cache._cache) == 0
        assert self.cache.get("wildberries", "телефон") is None
        assert self.cache.get("ozon", "телефон") is None

    def test_cache_cleanup_expired(self):
        """Test automatic cleanup of expired entries."""
        # Set multiple entries with different timestamps
        old_data = {"products": [{"id": 1, "name": "old"}], "timestamp": time.time() - 10}
        new_data = {"products": [{"id": 2, "name": "new"}], "timestamp": time.time()}
        
        # Manually set old entry (bypassing normal set method)
        old_key = self.cache._make_key("wildberries", "old_query")
        self.cache._cache[old_key] = {
            'timestamp': time.time() - 10,  # 10 seconds old
            'data': old_data,
            'source': 'wildberries',
            'query_hash': old_key.split(':')[1]
        }
        
        # Set new entry normally
        self.cache.set("wildberries", "new_query", new_data)
        
        assert len(self.cache._cache) == 2
        
        # Run cleanup
        self.cache._cleanup_expired()
        
        # Should only have the new entry
        assert len(self.cache._cache) == 1
        assert self.cache.get("wildberries", "new_query") == new_data
        assert self.cache.get("wildberries", "old_query") is None

    def test_thread_safety(self):
        """Test thread safety of cache operations."""
        def cache_operations(cache, operation_type):
            if operation_type == "set":
                for i in range(10):
                    cache.set(f"source{i}", f"query{i}", {"data": i})
            elif operation_type == "get":
                for i in range(10):
                    cache.get(f"source{i}", f"query{i}")
            elif operation_type == "mixed":
                for i in range(5):
                    cache.set(f"source{i}", f"query{i}", {"data": i})
                    cache.get(f"source{i}", f"query{i}")
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=cache_operations, args=(self.cache, "mixed"))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache integrity
        # Should have some entries (exact count may vary due to race conditions)
        assert len(self.cache._cache) > 0
        
        # Verify we can still read and write
        self.cache.set("test", "test", {"final": "test"})
        assert self.cache.get("test", "test") == {"final": "test"}

    def test_cache_with_different_ttl(self):
        """Test cache with different TTL values."""
        # Test with very short TTL
        short_cache = SearchCache(ttl=1)
        test_data = {"products": [{"id": 1, "name": "test"}]}
        
        short_cache.set("wildberries", "телефон", test_data)
        assert short_cache.get("wildberries", "телефон") == test_data
        
        time.sleep(2)
        assert short_cache.get("wildberries", "телефон") is None
        
        # Test with longer TTL
        long_cache = SearchCache(ttl=10)
        long_cache.set("wildberries", "телефон", test_data)
        assert long_cache.get("wildberries", "телефон") == test_data
        
        time.sleep(2)
        # Should still be available
        assert long_cache.get("wildberries", "телефон") == test_data

    def test_cache_key_collision_prevention(self):
        """Test that cache keys prevent collisions."""
        # Different queries should have different keys even if they hash similarly
        key1 = self.cache._make_key("wildberries", "телефон")
        key2 = self.cache._make_key("wildberries", "телефон ")  # With space
        key3 = self.cache._make_key("wildberries", "Телефон")  # Different case
        
        # These should be different keys
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
        
        # Set data for each
        self.cache.set("wildberries", "телефон", {"data": "original"})
        self.cache.set("wildberries", "телефон ", {"data": "with_space"})
        self.cache.set("wildberries", "Телефон", {"data": "uppercase"})
        
        # Should be able to retrieve each separately
        assert self.cache.get("wildberries", "телефон") == {"data": "original"}
        assert self.cache.get("wildberries", "телефон ") == {"data": "with_space"}
        assert self.cache.get("wildberries", "Телефон") == {"data": "uppercase"}

    def test_cache_metadata_storage(self):
        """Test that cache stores metadata correctly."""
        test_data = {"products": [{"id": 1, "name": "test"}]}
        
        # Set data
        self.cache.set("wildberries", "телефон", test_data)
        
        # Check internal cache structure
        key = self.cache._make_key("wildberries", "телефон")
        cached_item = self.cache._cache[key]
        
        assert 'timestamp' in cached_item
        assert 'data' in cached_item
        assert 'source' in cached_item
        assert 'query_hash' in cached_item
        assert cached_item['source'] == "wildberries"
        assert cached_item['data'] == test_data
        assert cached_item['query_hash'] == key.split(':')[1]

    def test_cache_with_complex_data(self):
        """Test cache with complex data structures."""
        complex_data = {
            "products": [
                {
                    "id": 1,
                    "name": "test",
                    "metadata": {
                        "brand": "test",
                        "rating": 4.5,
                        "reviews": 100,
                        "nested": {
                            "deep": {
                                "value": "test"
                            }
                        }
                    }
                }
            ],
            "summary": {
                "total": 1,
                "average_price": 1000.0,
                "brands": ["test"]
            }
        }
        
        # Set complex data
        self.cache.set("wildberries", "телефон", complex_data)
        
        # Retrieve and verify
        cached_data = self.cache.get("wildberries", "телефон")
        assert cached_data == complex_data
        assert cached_data["products"][0]["metadata"]["nested"]["deep"]["value"] == "test"

    def test_cache_edge_cases(self):
        """Test cache edge cases."""
        # Empty query
        self.cache.set("wildberries", "", {"empty_query": True})
        assert self.cache.get("wildberries", "") == {"empty_query": True}
        
        # Very long query
        long_query = "a" * 1000
        self.cache.set("wildberries", long_query, {"long_query": True})
        assert self.cache.get("wildberries", long_query) == {"long_query": True}
        
        # Special characters in query
        special_query = "телефон!@#$%^&*()_+-=[]{}|;':\",./<>?"
        self.cache.set("wildberries", special_query, {"special": True})
        assert self.cache.get("wildberries", special_query) == {"special": True}
        
        # Unicode characters
        unicode_query = "телефон📱смартфон💻"
        self.cache.set("wildberries", unicode_query, {"unicode": True})
        assert self.cache.get("wildberries", unicode_query) == {"unicode": True}

    def test_cache_performance(self):
        """Test cache performance with many entries."""
        import time
        
        start_time = time.time()
        
        # Add many entries
        for i in range(100):
            self.cache.set(f"source{i}", f"query{i}", {"data": i})
        
        set_time = time.time() - start_time
        
        # Retrieve all entries
        start_time = time.time()
        for i in range(100):
            self.cache.get(f"source{i}", f"query{i}")
        
        get_time = time.time() - start_time
        
        # Should be fast (less than 1 second for 100 operations)
        assert set_time < 1.0
        assert get_time < 1.0
        assert len(self.cache._cache) == 100