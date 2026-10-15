import hashlib
import json
from uuid import uuid4

class DomainError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status
        super().__init__(message)

def uid():
    return uuid4().hex

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def require(condition, message, status=400):
    if not condition:
        raise DomainError(message, status)
