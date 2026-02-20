from cachetools import TTLCache
from typing import Any, Optional
import fnmatch


class CacheService:
    """
    In-memory caching service using cachetools.TTLCache.
    
    TTL = 24 hours (86400 seconds)
    Max size = 1000 items
    
    Strategy: 
    - Cache GET endpoint results with parametrized keys (e.g., 'producto_list_cat_1_act_True')
    - On any write operation (POST/PUT/PATCH/DELETE), invalidate affected cache keys
    - Always return .copy() of cached values to prevent mutations
    
    Thread-safety: Not needed for single-worker FastAPI deployments
    """
    
    TTL_SECONDS = 86400  # 24 hours
    MAX_SIZE = 1000
    
    def __init__(self):
        """Initialize TTLCache with 24-hour TTL and max 1000 items."""
        self.cache = TTLCache(maxsize=self.MAX_SIZE, ttl=self.TTL_SECONDS)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache by key.
        
        Args:
            key: Cache key (e.g., 'producto_list_cat_1_act_True')
        
        Returns:
            Cached value or None if not found / expired
        """
        return self.cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with TTL of 24 hours.
        
        Args:
            key: Cache key (e.g., 'producto_list_cat_1_act_True')
            value: Value to cache (must be serializable, e.g., Pydantic schemas)
        """
        self.cache[key] = value
    
    def invalidate(self, pattern: str) -> None:
        """
        Invalidate cache keys matching a pattern using fnmatch.
        
        Args:
            pattern: Pattern to match keys against (e.g., 'oferta_*', 'producto_list_*')
        
        Note:
            Uses fnmatch for pattern matching. O(n) where n is number of cached items.
            OK for maxsize=1000, consider Redis if cache grows much larger.
        
        Examples:
            invalidate('producto_*')  # Removes producto_list_*, producto_1, producto_2, etc.
            invalidate('oferta_list_*')  # Removes oferta_list_act_None, oferta_list_act_True, etc.
        """
        keys_to_delete = [k for k in self.cache.keys() if fnmatch.fnmatch(str(k), pattern)]
        for k in keys_to_delete:
            self.cache.pop(k, None)
    
    def clear_all(self) -> None:
        """
        Clear entire cache. Called after any write operation when clearing everything.
        
        Guarantees: O(1) operation using dict.clear()
        """
        self.cache.clear()
    
    def get_stats(self) -> dict:
        """
        Get cache statistics for debugging.
        
        Returns:
            Dict with cache size and keys
        """
        return {
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "keys": list(self.cache.keys())
        }
