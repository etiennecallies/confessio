from home.models.stat_models import SearchHit
from home.utils.web_utils import get_user_user_agent_and_ip


def new_search_hit(request, nb_websites):
    user, user_agent, ip_address_hash = get_user_user_agent_and_ip(request)

    search_hit = SearchHit(
        query=request.get_full_path()[255:],
        nb_websites=nb_websites,
        user=user,
        user_agent=user_agent,
        ip_address_hash=ip_address_hash,
    )
    search_hit.save()
