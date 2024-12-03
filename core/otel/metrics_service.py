from opentelemetry.metrics import get_meter


class MetricsService:
    def __init__(self):
        meter = get_meter(__name__)

        # Create all metrics once here
        self.response_time_histogram = meter.create_histogram(
            "http.server.response.time",
            description="Response time by URL name",
        )

        self.warning_counter = meter.create_counter(
            "http.server.warnings.count",
            description="Count of warnings in the application",
        )

    def record_response_time(self, elapsed_time, url_name):
        self.response_time_histogram.record(elapsed_time, {
            "url_name": url_name,
        })

    def increment_warning_counter(self, warning_name):
        self.warning_counter.add(1, {
            "warning_name": warning_name,
        })


metrics_service = MetricsService()
