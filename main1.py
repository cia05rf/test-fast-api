from fastapi import FastAPI
import asyncio
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("final.env")

# Azure Application Insights Instrumentation Key
APPINSIGHTS_INSTRUMENTATIONKEY = os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")

app = FastAPI()

# Configure Azure logging
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(connection_string=f'InstrumentationKey={APPINSIGHTS_INSTRUMENTATIONKEY}'))

# Configure Azure tracing
tracer = Tracer(
    exporter=AzureExporter(connection_string=f'InstrumentationKey={APPINSIGHTS_INSTRUMENTATIONKEY}'),
    sampler=ProbabilitySampler(1.0),
)

@app.get("/hello")
async def hello():
    logger.info("Processing request for /hello")

    with tracer.span(name="hello_sleep"):
        await asyncio.sleep(5)

    logger.info("Request processed")
    return {"message": "hello world"}
