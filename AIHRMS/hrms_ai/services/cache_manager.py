"""
Cache Manager - Intelligent cache selection and management
"""
import logging
import yaml
import time
from typing import Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import os

logger = logging.getLogger(__name__)

class CacheInterface(ABC):
    """Abstract cache interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass

class MemoryCache(CacheInterface):
    """High-performance in-memory cache (Caffeine-style)"""
    
    def __init__(self, max_size: int = 10000, expire_after_write: int = 3600, expire_after_access: int = 1800):
        self.max_size = max_size
        self.expire_after_write = expire_after_write
        self.expire_after_access = expire_after_access
        self.cache = {}
        self.access_times = {}
        self.write_times = {}
        self.hit_count = 0
        self.miss_count = 0
    
    async def get(self, key: str) -> Optional[Any]:
        current_time = time.time()
        
        if key not in self.cache:
            self.miss_count += 1
            return None
        
        # Check expiration
        write_time = self.write_times.get(key, 0)
        access_time = self.access_times.get(key, 0)
        
        if (current_time - write_time > self.expire_after_write or 
            current_time - access_time > self.expire_after_access):
            await self.delete(key)
            self.miss_count += 1
            return None
        
        # Update access time
        self.access_times[key] = current_time
        self.hit_count += 1
        return self.cache[key]
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        current_time = time.time()
        
        # Evict if at max size
        if len(self.cache) >= self.max_size and key not in self.cache:
            await self._evict_lru()
        
        self.cache[key] = value
        self.write_times[key] = current_time
        self.access_times[key] = current_time
        return True
    
    async def delete(self, key: str) -> bool:
        if key in self.cache:
            del self.cache[key]
            self.write_times.pop(key, None)
            self.access_times.pop(key, None)
            return True
        return False
    
    async def clear(self) -> bool:
        self.cache.clear()
        self.access_times.clear()
        self.write_times.clear()
        return True
    
    async def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        await self.delete(lru_key)
    
    def get_stats(self) -> Dict[str, Any]:
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "type": "memory",
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "status": "active"
        }

class RedisCache(CacheInterface):
    """Redis-based cache"""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, 
                 password: str = None, connection_timeout: int = 5, **kwargs):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.connection_timeout = connection_timeout
        self.redis_client = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            import redis.asyncio as redis
            
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_connect_timeout=self.connection_timeout,
                socket_timeout=self.connection_timeout,
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.connected = False
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.connected:
            return None
        
        try:
            import json
            from datetime import datetime
            
            value = await self.redis_client.get(key)
            if not value:
                return None
            
            # Parse JSON with datetime support
            def json_deserializer(dct):
                if not isinstance(dct, dict):
                    return dct
                for key, val in dct.items():
                    if isinstance(val, str) and ('T' in val or val.endswith('Z')):
                        try:
                            dct[key] = datetime.fromisoformat(val.replace('Z', '+00:00'))
                        except:
                            pass
                return dct
            
            return json.loads(value, object_hook=json_deserializer)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        if not self.connected:
            return False
        
        try:
            import json
            from datetime import datetime, date
            
            # Custom JSON encoder for datetime objects
            def json_serializer(obj):
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            serialized_value = json.dumps(value, default=json_serializer)
            await self.redis_client.set(key, serialized_value, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if not self.connected:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        if not self.connected:
            return False
        
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.connected:
            return {"type": "redis", "status": "disconnected"}
        
        try:
            return {
                "type": "redis",
                "status": "connected",
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "memory_usage": "available",
                "connected_clients": "active"
            }
        except:
            return {"type": "redis", "status": "error"}

class CacheManager:
    """Intelligent cache manager with automatic fallback"""
    
    def __init__(self):
        self.cache: Optional[CacheInterface] = None
        self.config = self._load_config()
        self.cache_type = None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load cache configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "../config/cache_config.yml")
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.warning(f"Could not load cache config: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "cache": {
                "strategy": "auto",
                "redis": {"host": "localhost", "port": 6379, "db": 0},
                "memory": {"max_size": 10000, "expire_after_write": 3600, "expire_after_access": 1800},
                "compression": {"ttl": 7200, "max_entries": 50000}
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize cache at startup"""
        strategy = self.config["cache"]["strategy"]
        
        if strategy == "redis":
            return await self._init_redis_only()
        elif strategy == "memory":
            return await self._init_memory_only()
        else:  # auto
            return await self._init_auto()
    
    async def _init_redis_only(self) -> bool:
        """Initialize Redis cache only"""
        try:
            redis_config = self.config["cache"]["redis"]
            redis_cache = RedisCache(**redis_config)
            
            if await redis_cache.connect():
                self.cache = redis_cache
                self.cache_type = "redis"
                logger.info("Cache initialized: Redis")
                return True
            
            raise Exception("Redis connection failed")
        except Exception as e:
            logger.error(f"Redis-only initialization failed: {e}")
            raise
    
    async def _init_memory_only(self) -> bool:
        """Initialize memory cache only"""
        try:
            memory_config = self.config["cache"]["memory"]
            self.cache = MemoryCache(**memory_config)
            self.cache_type = "memory"
            logger.info("Cache initialized: Memory")
            return True
        except Exception as e:
            logger.error(f"Memory cache initialization failed: {e}")
            raise
    
    async def _init_auto(self) -> bool:
        """Auto-select cache with Redis fallback to memory - Never fails"""
        try:
            # Try Redis first
            redis_config = self.config["cache"]["redis"]
            redis_cache = RedisCache(**redis_config)
            
            if await redis_cache.connect():
                self.cache = redis_cache
                self.cache_type = "redis"
                logger.info("Cache initialized: Redis (auto-selected)")
                return True
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}")
        
        try:
            # Fallback to memory - this should never fail
            logger.info("Redis unavailable, falling back to memory cache")
            memory_config = self.config["cache"]["memory"]
            self.cache = MemoryCache(**memory_config)
            self.cache_type = "memory"
            logger.info("Cache initialized: Memory (fallback)")
            return True
        except Exception as e:
            logger.error(f"Memory cache fallback failed: {e}")
            # Last resort - basic memory cache with defaults
            self.cache = MemoryCache()
            self.cache_type = "memory_basic"
            logger.warning("Using basic memory cache with default settings")
            return True
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache:
            return None
        return await self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if not self.cache:
            return False
        
        # Use default TTL from config if not specified
        if ttl is None:
            ttl = self.config["cache"]["compression"]["ttl"]
        
        return await self.cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.cache:
            return False
        return await self.cache.delete(key)
    
    async def clear(self) -> bool:
        """Clear all cache"""
        if not self.cache:
            return False
        return await self.cache.clear()
    
    async def sadd(self, key: str, value: str) -> bool:
        """Add value to Redis set (Redis only)"""
        if not self.cache or self.cache_type != "redis":
            return False
        try:
            rc = getattr(self.cache, "redis_client", None)
            if rc:
                await rc.sadd(key, value)
                return True
        except Exception as e:
            logger.error(f"Redis sadd error: {e}")
        return False
    
    async def incr(self, key: str) -> int:
        """Increment counter (Redis only)"""
        if not self.cache or self.cache_type != "redis":
            return 0
        try:
            rc = getattr(self.cache, "redis_client", None)
            if rc:
                return await rc.incr(key)
        except Exception as e:
            logger.error(f"Redis incr error: {e}")
        return 0
    
    async def exists_pattern(self, pattern: str) -> bool:
        """Check if any keys matching pattern exist (Redis only)"""
        if not self.cache or self.cache_type != "redis":
            return False
        try:
            rc = getattr(self.cache, "redis_client", None)
            if rc:
                keys = await rc.keys(pattern)
                return len(keys) > 0
        except Exception as e:
            logger.error(f"Redis exists_pattern error: {e}")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache:
            return {"status": "not_initialized"}
        
        stats = self.cache.get_stats()
        stats["selected_type"] = self.cache_type
        stats["strategy"] = self.config["cache"]["strategy"]
        return stats
    
    def is_available(self) -> bool:
        """Check if cache is available"""
        return self.cache is not None

# Global cache manager instance
cache_manager = CacheManager()