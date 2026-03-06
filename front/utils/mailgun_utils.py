import base64
import os
import time
import traceback

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

PEM_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'mailgun-webhooks.pem')
MAX_TIMESTAMP_AGE_SECONDS = 300  # 5 minutes


def validate_token(token: str, timestamp: int, signature: str) -> bool:
    # Reject stale requests (replay attack prevention)
    current_time = time.time()
    if abs(current_time - timestamp) > MAX_TIMESTAMP_AGE_SECONDS:
        print(f"Rejecting request with timestamp {timestamp} (too old), "
              f"current time is {current_time}")
        return False

    with open(PEM_PATH, 'rb') as f:
        cert = x509.load_pem_x509_certificate(f.read())
    public_key = cert.public_key()

    message = f"{timestamp}{token}".encode()
    sig_bytes = base64.b64decode(signature)

    try:
        public_key.verify(sig_bytes, message, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        print(f"Signature verification failed for token {token} with timestamp {timestamp}")
        print(traceback.format_exc())
        return False
