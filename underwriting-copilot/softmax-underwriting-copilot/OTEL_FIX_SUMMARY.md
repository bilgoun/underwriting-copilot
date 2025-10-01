# OpenTelemetry Import Fix - Applied 2025-09-30

## Problem
The simulation script was failing with:
```
ModuleNotFoundError: No module named 'opentelemetry.sdk.extension'
ImportError: cannot import name 'set_logger_provider' from 'opentelemetry.sdk._logs'
```

## Root Cause
OpenTelemetry Python SDK reorganized its modules:
1. **Logs exporter** moved from public to private module: `opentelemetry.exporter.otlp.proto.http._log_exporter`
2. **set_logger_provider** moved from SDK to API: `opentelemetry._logs` (not `opentelemetry.sdk._logs`)
3. **PrometheusMetricReader** moved: `opentelemetry.exporter.prometheus` (not `opentelemetry.sdk.extension.prometheus`)

## Solution Applied

### Changes to `app/observability.py`:

1. **Robust logs exporter import** (lines 14-26):
```python
# Robust OTLP logs exporter import (works across OTel versions)
try:
    # OTLP/HTTP logs exporter (OTel >= ~1.15, current location)
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    HAS_LOG_EXPORTER = True
except Exception:
    try:
        # Fallback: OTLP/gRPC logs exporter
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        HAS_LOG_EXPORTER = True
    except Exception:
        OTLPLogExporter = None  # type: ignore
        HAS_LOG_EXPORTER = False
```

2. **Fixed set_logger_provider import** (lines 59-63):
```python
# set_logger_provider must come from the API package (not sdk)
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggingHandler, LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.prometheus import PrometheusMetricReader
```

3. **Improved logger provider initialization** (lines 174-190):
```python
# Create LoggerProvider even if we can't export logs, so LoggingHandler works locally
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

if HAS_LOG_EXPORTER:
    log_exporter = OTLPLogExporter(
        endpoint=f"{endpoint}/v1/logs",  # for HTTP; with gRPC, env var is enough
        headers=headers,
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
else:
    logger.debug("otlp_log_exporter_unavailable", component=component)

# Attach Python logging -> OTel pipeline
logging_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
root_logger = logging.getLogger()
root_logger.addHandler(logging_handler)
```

## Benefits

1. **Version resilient**: Works with both HTTP and gRPC exporters
2. **Graceful degradation**: System works even if logs export is unavailable
3. **Future-proof**: Uses current OTel Python SDK structure (1.37+)
4. **Better error handling**: Catches import errors and continues

## Verification

```bash
# Test imports
python3 - <<'PY'
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
print("✅ All imports successful")
PY

# Test observability module
python3 -c "from app.observability import init_observability; print('✅ Module loads')"

# Run simulation
python scripts/run_simulations.py
```

## Status
✅ **FIXED** - Simulation script now runs successfully
✅ **TESTED** - All imports verified
✅ **PRODUCTION READY** - Works with OpenTelemetry Python SDK 1.37+

## References
- [OpenTelemetry Python Docs](https://opentelemetry-python.readthedocs.io/)
- [OTLP Exporter Configuration](https://opentelemetry.io/docs/specs/otel/protocol/exporter/)
- [Logs API Migration](https://github.com/open-telemetry/opentelemetry-python/blob/main/CHANGELOG.md)
