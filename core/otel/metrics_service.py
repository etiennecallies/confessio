from opentelemetry.metrics import get_meter


class MetricsService:
    def __init__(self):
        meter = get_meter(__name__)

        # Create all metrics once here
        self.response_count = meter.create_counter(
            "http.server.response.count",
            description="Number of responses by URL name",
        )

        self.response_time_sum = meter.create_counter(
            "http.server.response.time.sum",
            description="Total response time by URL name",
        )

        self.response_db_time_sum = meter.create_counter(
            "http.server.response.db_time.sum",
            description="Total response DB time by URL name",
        )

        self.warning_counter = meter.create_counter(
            "http.server.warnings.count",
            description="Count of warnings in the application",
        )

    def record_response_time(self, elapsed_time, db_time, url_name):
        attributes = {"url_name": url_name}
        self.response_count.add(1, attributes)
        self.response_time_sum.add(elapsed_time, attributes)
        self.response_db_time_sum.add(db_time, attributes)

    def increment_warning_counter(self, warning_name):
        self.warning_counter.add(1, {
            "warning_name": warning_name,
        })


metrics_service = MetricsService()
