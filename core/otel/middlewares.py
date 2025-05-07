import time


class RequestStartTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.start_time = time.time()
        return self.get_response(request)


class ResponseTimeMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        from core.otel.metrics_service import metrics_service
        self.metrics_service = metrics_service

    def __call__(self, request):
        response = self.get_response(request)
        start_time = getattr(request, "start_time", None)

        if start_time and request.resolver_match:
            elapsed_time = time.time() - start_time
            url_name = request.resolver_match.url_name or "unknown"

            # Avoid too many metrics
            if url_name in [
                'around_place_view',
                'in_area_view',
                'around_me_view',
            ]:
                url_name = 'search_view'
            elif url_name not in [
                'index',
                'autocomplete',
                'diocese_view',
                'website_view',
                'api_churches',
            ]:
                url_name = 'other'

            self.metrics_service.record_response_time(elapsed_time, url_name)

        return response
