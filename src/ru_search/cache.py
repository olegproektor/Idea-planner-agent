"""
Caching layer for the ru_search module.

This module implements a TTL-based caching system for search results,
using in-memory dictionary storage with thread-safe operations.
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib


class SearchCache:
    """
    TTL-based caching system for search results.
    
    This class provides a thread-safe in-memory cache for storing and retrieving
    search results with automatic expiration based on time-to-live (TTL).
    """
    
    def __init__(self, ttl: int = 21600):
        """
        Initialize the SearchCache with a specified TTL.
        
        Args:
            ttl: Time-to-live in seconds (default: 21600 = 6 hours)
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def _make_key(self, source: str, query: str) -> str:
        """
        Create a cache key from source and query using MD5 hashing.
        
        Args:
            source: Data source name
            query: Search query string
            
        Returns:
            Cache key in format "source:query_hash"
        """
        # Create MD5 hash of the query
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        return f"{source}:{query_hash}"
    
    def get(self, source: str, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached results for a specific source and query.
        
        Args:
            source: Data source name
            query: Search query string
            
        Returns:
            Cached data if available and not expired, None otherwise
        """
        key = self._make_key(source, query)
        
        with self._lock:
            cached_item = self._cache.get(key)
            if cached_item is None:
                return None
            
            # Check if the cached item has expired
            cache_time = cached_item.get('timestamp')
            if cache_time is None:
                return None
                
            # Calculate expiration time
            expiration_time = cache_time + self.ttl
            current_time = time.time()
            
            # Remove expired item and return None
            if current_time > expiration_time:
                del self._cache[key]
                return None
            
            # Return cached data
            return cached_item.get('data')
    
    def set(self, source: str, query: str, data: Dict[str, Any]) -> None:
        """
        Cache search results for a specific source and query.
        
        Args:
            source: Data source name
            query: Search query string
            data: Data to cache
        """
        key = self._make_key(source, query)
        
        cache_item = {
            'timestamp': time.time(),
            'data': data,
            'source': source,
            'query_hash': key.split(':')[1]  # Store the hash part
        }
        
        with self._lock:
            self._cache[key] = cache_item
    
    def clear(self) -> None:
        """
        Clear all cache entries.
        """
        with self._lock:
            self._cache.clear()
    
    def _cleanup_expired(self) -> None:
        """
        Remove all expired cache entries.
        
        This method is called internally to clean up expired items.
        """
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for key, cached_item in self._cache.items():
                cache_time = cached_item.get('timestamp')
                if cache_time is not None:
                    expiration_time = cache_time + self.ttl
                    if current_time > expiration_time:
                        expired_keys.append(key)
            
            # Remove expired items
            for key in expired_keys:
                del self._cache[key]