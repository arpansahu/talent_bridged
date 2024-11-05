import redis
from django.conf import settings

# Initialize the Redis client using REDIS_CLOUD_URL
redis_client = redis.StrictRedis.from_url(settings.REDIS_CLOUD_URL)