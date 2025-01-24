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
