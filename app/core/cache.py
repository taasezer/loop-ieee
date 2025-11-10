"""
LOOP Lojistik Platformu - Gelişmiş Cache Yöneticisi
Redis tabanlı çok katmanlı cache stratejileri
"""

import json
import pickle
from typing import Any, Optional, Dict, List, Union, Callable, Awaitable
from datetime import timedelta, datetime
from functools import wraps
import hashlib
from dataclasses import dataclass
from loguru import logger

from core.database import get_cached_data, set_cached_data, delete_cached_data
from core.config import settings


@dataclass
class CacheConfig:
    """Cache konfigürasyonu"""
    ttl: int = 300  # 5 dakika
    key_prefix: str = ""
    version: str = "1"
    compress: bool = False
    tags: List[str] = None


class CacheManager:
    """Gelişmiş cache yöneticisi"""
    
    def __init__(self):
        self.configs = {
            'default': CacheConfig(ttl=settings.CACHE_TTL_SECONDS),
            'weather': CacheConfig(ttl=settings.WEATHER_CACHE_TTL, key_prefix="weather:"),
            'currency': CacheConfig(ttl=settings.CURRENCY_CACHE_TTL, key_prefix="currency:"),
            'location': CacheConfig(ttl=300, key_prefix="location:"),
            'analytics': CacheConfig(ttl=1800, key_prefix="analytics:"),  # 30 dakika
            'ml_model': CacheConfig(ttl=3600, key_prefix="ml:", compress=True),  # 1 saat
            'session': CacheConfig(ttl=1800, key_prefix="session:"),  # 30 dakika
            'api_response': CacheConfig(ttl=60, key_prefix="api:", version="2")  # 1 dakika
        }
    
    def get_config(self, cache_type: str = 'default') -> CacheConfig:
        """Cache konfigürasyonu al"""
        return self.configs.get(cache_type, self.configs['default'])
    
    def generate_cache_key(self, key: str, config: CacheConfig, *args, **kwargs) -> str:
        """Cache anahtarı oluştur"""
        # Anahtar prefix'ini ekle
        cache_key = f"{config.key_prefix}{key}"
        
        # Versiyon bilgisini ekle
        if config.version:
            cache_key = f"v{config.version}:{cache_key}"
        
        # Eğer argümanlar varsa, hash oluştur
        if args or kwargs:
            hash_input = f"{args}{sorted(kwargs.items()) if kwargs else ''}"
            hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            cache_key = f"{cache_key}:{hash_suffix}"
        
        return cache_key
    
    async def get(self, key: str, cache_type: str = 'default') -> Optional[Any]:
        """Cache'den veri al"""
        try:
            config = self.get_config(cache_type)
            cache_key = self.generate_cache_key(key, config)
            
            # Redis'ten veri al
            data = await get_cached_data(cache_key)
            
            if data:
                # Sıkıştırılmış veriyi aç
                if config.compress:
                    data = pickle.loads(data)
                else:
                    data = json.loads(data)
                
                logger.debug(f"Cache hit: {cache_key}")
                return data
            
            logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get hatası: {e}")
            return None
    
    async def set(self, key: str, value: Any, cache_type: str = 'default', custom_ttl: Optional[int] = None) -> bool:
        """Cache'e veri kaydet"""
        try:
            config = self.get_config(cache_type)
            cache_key = self.generate_cache_key(key, config)
            ttl = custom_ttl or config.ttl
            
            # Veriyi hazırla
            if config.compress:
                data = pickle.dumps(value)
            else:
                data = json.dumps(value, default=str)
            
            # Redis'e kaydet
            success = await set_cached_data(cache_key, data, ttl)
            
            if success:
                logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
                
                # Tag'lere göre indeksle
                if config.tags:
                    await self._add_to_tags(cache_key, config.tags)
            
            return success
            
        except Exception as e:
            logger.error(f"Cache set hatası: {e}")
            return False
    
    async def delete(self, key: str, cache_type: str = 'default') -> bool:
        """Cache'den veri sil"""
        try:
            config = self.get_config(cache_type)
            cache_key = self.generate_cache_key(key, config)
            
            success = await delete_cached_data(cache_key)
            
            if success:
                logger.debug(f"Cache delete: {cache_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Cache delete hatası: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Pattern'e göre cache'leri sil"""
        try:
            redis_client = await self._get_redis()
            keys = await redis_client.keys(pattern)
            
            if keys:
                deleted_count = await redis_client.delete(*keys)
                logger.info(f"Pattern silme: {pattern} ({deleted_count} key)")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Pattern silme hatası: {e}")
            return 0
    
    async def invalidate_tags(self, tags: List[str]) -> int:
        """Tag'lere göre cache'leri invalidate et"""
        try:
            redis_client = await self._get_redis()
            deleted_count = 0
            
            for tag in tags:
                tag_key = f"tag:{tag}"
                keys = await redis_client.smembers(tag_key)
                
                if keys:
                    deleted_count += await redis_client.delete(*keys)
                    await redis_client.delete(tag_key)
            
            logger.info(f"Tag invalidation: {tags} ({deleted_count} key)")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Tag invalidation hatası: {e}")
            return 0
    
    async def _add_to_tags(self, cache_key: str, tags: List[str]):
        """Cache'i tag'lere ekle"""
        try:
            redis_client = await self._get_redis()
            
            for tag in tags:
                tag_key = f"tag:{tag}"
                await redis_client.sadd(tag_key, cache_key)
                
        except Exception as e:
            logger.error(f"Tag ekleme hatası: {e}")
    
    async def _get_redis(self):
        """Redis client al"""
        return await get_redis()


# Global cache manager instance
cache_manager = CacheManager()


# Decorator fonksiyonları
def cache_result(cache_type: str = 'default', ttl: Optional[int] = None, tags: Optional[List[str]] = None):
    """Fonksiyon sonucunu cache'le"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Cache anahtarı oluştur
            cache_key = f"{func.__module__}.{func.__name__}"
            
            # Cache'den dene
            cached_result = await cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                return cached_result
            
            # Fonksiyonu çalıştır
            result = await func(*args, **kwargs)
            
            # Sonucu cache'e kaydet
            if result is not None:
                await cache_manager.set(cache_key, result, cache_type, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(*cache_types: str, pattern: Optional[str] = None, tags: Optional[List[str]] = None):
    """Fonksiyon çağrıldığında cache'leri invalidate et"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Önce fonksiyonu çalıştır
            result = await func(*args, **kwargs)
            
            # Sonra cache'leri temizle
            for cache_type in cache_types:
                if pattern:
                    await cache_manager.delete_pattern(pattern)
                if tags:
                    await cache_manager.invalidate_tags(tags)
            
            return result
        
        return wrapper
    return decorator


# Cache stratejileri
class CacheStrategies:
    """Cache stratejileri"""
    
    @staticmethod
    async def cache_aside(key: str, fetch_func: Callable[[], Awaitable[Any]], cache_type: str = 'default') -> Any:
        """Cache-aside (lazy loading) stratejisi"""
        # Önce cache'den dene
        cached_data = await cache_manager.get(key, cache_type)
        if cached_data is not None:
            return cached_data
        
        # Cache yoksa veritabanından çek
        data = await fetch_func()
        
        # Cache'e kaydet
        if data is not None:
            await cache_manager.set(key, data, cache_type)
        
        return data
    
    @staticmethod
    async def write_through(key: str, data: Any, save_func: Callable[[Any], Awaitable[bool]], cache_type: str = 'default') -> bool:
        """Write-through stratejisi"""
        # Önce veritabanına kaydet
        db_success = await save_func(data)
        
        # Sonra cache'e kaydet
        if db_success:
            await cache_manager.set(key, data, cache_type)
        
        return db_success
    
    @staticmethod
    async def write_behind(key: str, data: Any, save_func: Callable[[Any], Awaitable[bool]], cache_type: str = 'default', delay: int = 5) -> bool:
        """Write-behind (write-back) stratejisi"""
        # Hemen cache'e kaydet
        cache_success = await cache_manager.set(key, data, cache_type)
        
        # Veritabanına asenkron kaydet
        async def delayed_save():
            await asyncio.sleep(delay)
            await save_func(data)
        
        # Arka planda çalıştır
        asyncio.create_task(delayed_save())
        
        return cache_success
    
    @staticmethod
    async def refresh_ahead(key: str, fetch_func: Callable[[], Awaitable[Any]], cache_type: str = 'default', refresh_threshold: float = 0.8) -> Any:
        """Refresh-ahead stratejisi"""
        cached_data = await cache_manager.get(key, cache_type)
        
        if cached_data is not None:
            # TTL kontrolü
            redis_client = await cache_manager._get_redis()
            ttl = await redis_client.ttl(key)
            config = cache_manager.get_config(cache_type)
            
            if ttl > 0 and ttl < (config.ttl * refresh_threshold):
                # Arka planda yenile
                async def refresh():
                    new_data = await fetch_func()
                    if new_data is not None:
                        await cache_manager.set(key, new_data, cache_type)
                
                asyncio.create_task(refresh())
        
        else:
            # Cache yoksa hemen çek
            cached_data = await fetch_func()
            if cached_data is not None:
                await cache_manager.set(key, cached_data, cache_type)
        
        return cached_data


# Cache metrics ve monitoring
class CacheMetrics:
    """Cache metrikleri"""
    
    def __init__(self):
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0
    
    def record_hit(self):
        """Hit kaydet"""
        self.hit_count += 1
    
    def record_miss(self):
        """Miss kaydet"""
        self.miss_count += 1
    
    def record_error(self):
        """Error kaydet"""
        self.error_count += 1
    
    def get_hit_rate(self) -> float:
        """Hit rate hesapla"""
        total = self.hit_count + self.miss_count
        return (self.hit_count / total) * 100 if total > 0 else 0
    
    def get_metrics(self) -> Dict:
        """Metrikleri al"""
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'error_count': self.error_count,
            'hit_rate': self.get_hit_rate(),
            'total_requests': self.hit_count + self.miss_count
        }


# Global metrics instance
cache_metrics = CacheMetrics()


# Örnek kullanım fonksiyonları
async def get_or_set_courier_location(courier_id: str) -> Optional[Dict]:
    """Kurye konumunu cache'den al veya ayarla"""
    cache_key = f"courier:{courier_id}:location"
    
    return await CacheStrategies.cache_aside(
        cache_key,
        lambda: fetch_courier_location_from_db(courier_id),
        cache_type='location'
    )


async def fetch_courier_location_from_db(courier_id: str) -> Optional[Dict]:
    """Veritabanından kurye konumunu al"""
    # Bu fonksiyon veritabanı sorgusu yapacak
    # Şimdilik mock data döndürüyoruz
    return {
        'courier_id': courier_id,
        'latitude': 41.0082,
        'longitude': 28.9784,
        'timestamp': datetime.now().isoformat()
    }


async def update_courier_performance(courier_id: str, performance_data: Dict) -> bool:
    """Kurye performansını güncelle (write-through)"""
    cache_key = f"courier:{courier_id}:performance"
    
    return await CacheStrategies.write_through(
        cache_key,
        performance_data,
        lambda data: save_courier_performance_to_db(courier_id, data),
        cache_type='analytics'
    )


async def save_courier_performance_to_db(courier_id: str, data: Dict) -> bool:
    """Kurye performansını veritabanına kaydet"""
    # Bu fonksiyon veritabanına kaydedecek
    return True