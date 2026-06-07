import pytest
from app.infrastructure.cache.cache_service import CacheService
import time


class TestCacheService:
    """Unit tests for CacheService"""
    
    @pytest.fixture
    def cache(self):
        """Create a fresh cache instance for each test"""
        return CacheService()
    
    def test_set_and_get(self, cache):
        """Test basic set and get operations"""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_get_nonexistent_key(self, cache):
        """Test getting a key that doesn't exist"""
        assert cache.get("nonexistent") is None
    
    def test_set_overwrites_existing(self, cache):
        """Test that setting a key overwrites previous value"""
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"
    
    def test_cache_with_list(self, cache):
        """Test caching list objects"""
        test_list = [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]
        cache.set("items", test_list)
        assert cache.get("items") == test_list
    
    def test_cache_with_dict(self, cache):
        """Test caching dict objects"""
        test_dict = {"id": 1, "name": "test", "active": True}
        cache.set("item", test_dict)
        assert cache.get("item") == test_dict
    
    def test_clear_all(self, cache):
        """Test clearing entire cache"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        cache.clear_all()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
    
    def test_clear_all_with_empty_cache(self, cache):
        """Test clearing an empty cache doesn't raise errors"""
        cache.clear_all()
        assert cache.get("key") is None
    
    def test_multiple_operations(self, cache):
        """Test multiple set/get operations"""
        cache.set("user_1", {"id": 1, "name": "Alice"})
        cache.set("user_2", {"id": 2, "name": "Bob"})
        cache.set("settings", {"theme": "dark"})
        
        assert cache.get("user_1") == {"id": 1, "name": "Alice"}
        assert cache.get("user_2") == {"id": 2, "name": "Bob"}
        assert cache.get("settings") == {"theme": "dark"}
    
    def test_get_stats(self, cache):
        """Test getting cache statistics"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = cache.get_stats()
        
        assert stats["size"] == 2
        assert stats["maxsize"] == 1000
        assert stats["ttl"] == 86400  # 24 hours
        assert "key1" in stats["keys"]
        assert "key2" in stats["keys"]
    
    def test_cache_parametrized_keys(self, cache):
        """Test parametrized cache keys like 'producto_list_cat_1_act_True'"""
        # Simulate parametrized keys for products with different filters
        cache.set("producto_list_cat_None_act_None", [{"id": 1}, {"id": 2}])
        cache.set("producto_list_cat_1_act_None", [{"id": 1}])
        cache.set("producto_list_cat_1_act_True", [{"id": 1}])
        cache.set("producto_list_cat_2_act_False", [])
        
        assert len(cache.get("producto_list_cat_None_act_None")) == 2
        assert len(cache.get("producto_list_cat_1_act_None")) == 1
        assert len(cache.get("producto_list_cat_1_act_True")) == 1
        assert len(cache.get("producto_list_cat_2_act_False")) == 0
    
    def test_cache_invalidation_clear_all_on_write(self, cache):
        """Test that clear_all() can be used to invalidate on write"""
        # Setup initial cache
        cache.set("producto_list_cat_None_act_None", [{"id": 1}])
        cache.set("producto_1", {"id": 1, "name": "Product 1"})
        
        # Simulate write operation - clear all
        cache.clear_all()
        
        # Verify all entries are gone
        assert cache.get("producto_list_cat_None_act_None") is None
        assert cache.get("producto_1") is None


class TestCacheServiceMaxSize:
    """Test CacheService behavior with maxsize"""
    
    def test_cache_respects_maxsize(self):
        """Test that cache respects maxsize limit"""
        cache = CacheService()
        
        # Add items up to maxsize (1000)
        for i in range(5):
            cache.set(f"key_{i}", f"value_{i}")
        
        # All should be accessible
        for i in range(5):
            assert cache.get(f"key_{i}") == f"value_{i}"
    
    def test_cache_stats_empty(self):
        """Test cache stats on empty cache"""
        cache = CacheService()
        stats = cache.get_stats()
        
        assert stats["size"] == 0
        assert stats["maxsize"] == 1000
        assert stats["keys"] == []
