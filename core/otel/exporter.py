from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

metric_exporter = OTLPMetricExporter(endpoint="http://localhost:4317")
metric_reader = PeriodicExportingMetricReader(metric_exporter)
meter_provider = MeterProvider(metric_readers=[metric_reader])

# Set the global meter provider
set_meter_provider(meter_provider)
