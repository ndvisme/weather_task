from rq import Queue
from app.core.config import redis_conn

queue = Queue(connection=redis_conn)
