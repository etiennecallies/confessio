import os

import httpx


def verify_token(token: str) -> bool:
    cloudflare_turnstile_secret_key = os.environ.get('CLOUDFLARE_TURNSTILE_SECRET_KEY', '')

    url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
    payload = {
        'secret': cloudflare_turnstile_secret_key,
        'response': token,
    }

    with httpx.Client() as client:
        response = client.post(url, json=payload)
        outcome = response.json()

    if outcome.get('success'):
        return True

    print(f"Cloudflare Turnstile verification failed: {outcome}")
    return False
