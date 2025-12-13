from tasks import processing_document
result = processing_document.delay("windows-test-123")
print(f"Sent: {result.id}")


# import redis

# r = redis.Redis(host='127.0.0.1', port=6379, db=0)
# try:
#     print(r.ping())  # Should print True
#     r.set('test-key', 'hello')
#     print(r.get('test-key'))  # Should print b'hello'
# except Exception as e:
#     print(f"Error: {e}")
    
# import os
# from dotenv import load_dotenv

# load_dotenv()
# print(f"Broker: {os.getenv('CELERY_BROKER_URL')}")