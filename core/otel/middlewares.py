import time

from opentelemetry.metrics import get_meter


class RequestStartTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.start_time = time.time()
        return self.get_response(request)


class ResponseTimeMetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        meter = get_meter(__name__)
        # Histogram to record response times
        self.response_time_histogram = meter.create_histogram(
            "http.server.response.time",
            description="Response time by URL name",
        )

    def __call__(self, request):
        response = self.get_response(request)
        start_time = getattr(request, "start_time", None)

        if start_time and request.resolver_match:
            elapsed_time = time.time() - start_time
            url_name = request.resolver_match.url_name or "unknown"

            # Avoid too many metrics
            if url_name not in [
                'index',
                'autocomplete',
                'diocese_view',
            ]:
                url_name = 'other'

            # Record the response time in the histogram
            self.response_time_histogram.record(elapsed_time, {
                "url_name": url_name,
            })

        return response
