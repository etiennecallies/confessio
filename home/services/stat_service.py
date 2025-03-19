import os

from home.models.stat_models import SearchHit
from home.utils.hash_utils import hash_string_to_hex
from home.utils.web_utils import get_client_ip


def new_search_hit(request, nb_websites):
    user_agent = request.META['HTTP_USER_AGENT']
    ip_hash_salt = os.environ.get('IP_HASH_SALT')
    ip_address_hash = hash_string_to_hex(ip_hash_salt + get_client_ip(request))

    user = request.user if request.user.is_authenticated else None

    search_hit = SearchHit(
        query=request.get_full_path(),
        nb_websites=nb_websites,
        user=user,
        user_agent=user_agent,
        ip_address_hash=ip_address_hash,
    )
    search_hit.save()
