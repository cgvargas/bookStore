from functools import wraps
from django.core.cache import caches
from django.conf import settings
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class GoogleBooksCache:
    def __init__(self):
        self.cache = caches['google_books']
        self.timeout = settings.GOOGLE_BOOKS_CACHE_TIMEOUT
        self.prefix = settings.GOOGLE_BOOKS_CACHE_KEY_PREFIX

    def generate_key(self, *args, **kwargs):
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return f"{self.prefix}{hashlib.md5(key_data.encode()).hexdigest()}"

    def get(self, key):
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.error(f"Erro ao recuperar cache: {str(e)}")
            return None

    def set(self, key, value):
        try:
            self.cache.set(key, value, self.timeout)
            return True
        except Exception as e:
            logger.error(f"Erro ao definir cache: {str(e)}")
            return False


cache_instance = GoogleBooksCache()


def cache_google_books_api(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        cache_key = cache_instance.generate_key(*args, **kwargs)
        result = cache_instance.get(cache_key)

        if result is None:
            result = func(self, *args, **kwargs)
            cache_instance.set(cache_key, result)

        return result

    return wrapper