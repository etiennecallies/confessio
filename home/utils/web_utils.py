import os

from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.urls import reverse

from home.utils.hash_utils import hash_string_to_hex


def get_client_ip(request) -> str:
    """
    https://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django/4581997#4581997
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_user_agent_and_ip(request) -> tuple[User | None, str | None, str | None]:
    user = request.user if request.user.is_authenticated else None
    user_agent = request.META.get('HTTP_USER_AGENT', None)
    ip_hash_salt = os.environ.get('IP_HASH_SALT')
    ip_address_hash = hash_string_to_hex(ip_hash_salt + get_client_ip(request))

    return user, user_agent, ip_address_hash


def redirect_with_url_params(url_name: str, query_params: dict, **kwargs):
    url = reverse(url_name, kwargs=kwargs)
    if query_params:
        url += '?' + '&'.join(f'{key}={value}' for key, value in query_params.items())
    return redirect(url)
