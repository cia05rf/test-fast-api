from fastapi import FastAPI
import asyncio
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
import logging

# Azure Application Insights Instrumentation Key
instrumentation_key = 'f293c1fb-3646-4323-adda-ee10b87c9850'

app = FastAPI()

# Configure Azure logging
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=f'InstrumentationKey={instrumentation_key}'))

# Configure Azure tracing
tracer = Tracer(
    exporter=AzureExporter(connection_string=f'InstrumentationKey={instrumentation_key}'),
    sampler=ProbabilitySampler(1.0),
)

@app.get("/hello")
async def hello():
    logger.info("Processing request for /hello")

    with tracer.span(name="hello_sleep"):
        await asyncio.sleep(5)

    logger.info("Request processed")
    return {"message": "hello world"}
