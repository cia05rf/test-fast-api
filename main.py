import os
import requests
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from httpx import AsyncClient, Timeout
import logging
import random
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace import config_integration
from opencensus.ext.azure.log_exporter import AzureLogHandler
import string

def generate_random_id(length=8):
    # Generate a random string of upper and lower case characters, and digits
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

app = FastAPI()

class ProductData(BaseModel):
    """
    ### Used for applying API input schema validation
    """
    message: str
    conversationId: str
    messageId: str
    metadata: dict = None # Optional

class FeedbackData(BaseModel):
    """
    ### Used for applying API input schema validation
    """
    messageId: str
    conversationId: str
    feedback: str

# App Insights Configuration
# In this step connect APPINSIGHTS_INSTRUMENTATIONKEY with AzureLogHandler which collects the Logs in it.

APPINSIGHTS_INSTRUMENTATIONKEY = os.environ.get("APPINSIGHTS_INSTRUMENTATIONKEY")
config_integration.trace_integrations(['logging'])
logger = logging.getLogger(__name__)
handler = AzureLogHandler(connection_string=f'InstrumentationKey={APPINSIGHTS_INSTRUMENTATIONKEY}')
logger.addHandler(handler)
logger.setLevel("INFO")


# In this step AzureExporter will export the Logs or Traces to App Insights in Azure Portal.
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    tracer = Tracer(exporter=AzureExporter(connection_string=f'InstrumentationKey={APPINSIGHTS_INSTRUMENTATIONKEY}'),sampler=ProbabilitySampler(1.0))
    with tracer.span("main") as span:
        span.span_kind = SpanKind.SERVER
        # Assigning the request id to the span id
        span.span_id = request.headers.get("x-request-id")
        logger.info(span.span_id, "**request received in middleware**")
        response = await call_next(request)
    return response

@app.get("/")
def index():
    return {"hello": "world"}

@app.get("/welcome")
def welcome_page():
    return "Welcome to productGPT"


@app.get("/hello")
async def hello():
    logger.info("Processing request for /hello")
    await asyncio.sleep(5)
    logger.info("Request processed")
    return {"message": "hello world"}
      

@app.post("/product-conversation")
async def read_products(data: ProductData, request: Request):
    """
    ### Takes user input from frontend(Chatbot) and pass it to productgpt API and returns the response
    - Args: Json Object such as :
        ```
        {
        
            "message": "Any string message. For e.g: Make my teeth shine please",
            "conversationId": "Hash value. For e.g: 2234567890123456789f3f66",
            "messageId": "Hash value. For e.g: 2234567890123456789f3f66",
            "metadata": {"foo": "bar"}
        }
        ```
    - Returns:
        Json object such as :
        ```
        {
            
                "conversationId": "Hash value. For e.g: 2234567890123456789f3f66",
                "messageId": "Hash value. For e.g: 2234567890123456789f3f66",
                "timestamp": "2023-10-06T13:11:47.877745",
                "message": "String message",
                "products": [{}]
            
        }
        ```
    """
    req_id = generate_random_id()
    # Declaring Variables
    product_api_target_type = os.environ.get('product_api_target_type')
    null_value_error = os.environ.get('null_value_error')
    mock_url = os.environ.get('mock_url')
    dev_url = os.environ.get('dev_url')
    live_url = os.environ.get('live_url')
    try:
        logger.info(f"{req_id} - **Data Received from UI**")
        access_token = os.environ.get('access_token')
        message = data.message.strip()
        conversationId = data.conversationId.strip()
        messageId = data.messageId.strip()
        metadata = data.metadata
        timestamp = str(datetime.now())
        # Remove special characters from message
        # message = re.sub(r'[^a-zA-Z0-9\s]', '', message)
    except Exception as e:
        logger.error(f"{req_id} - Exception: creating variables - {e}")
        return {"Error": os.environ.get('invalid_json_message'), "StatusCode": "400"}

    if (message is None) or (message == ""):
        logger.error(f"{req_id} - Exception: message null value error")
        return {"Error": null_value_error, "StatusCode": "400"}
    if (conversationId is None) or (conversationId == ""):
        logger.error(f"{req_id} - Exception: conversationId null value error")
        return {"Error": null_value_error, "StatusCode": "400"}
    if (messageId is None) or (messageId == ""):
        logger.error(f"{req_id} - Exception: messageId null value error")
        return {"Error": null_value_error, "StatusCode": "400"}
    if (metadata is None) or (metadata == ""):
        metadata = None

    if product_api_target_type == "mock":
        url = mock_url
    elif product_api_target_type == "dev":
        url = dev_url
    else:
        url = live_url

    # Headers for internal request
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(access_token)
    }

    try:
        # Framing Data for internal call
        data = {
            "inputs": {
                "message": [message],
                "conversationId": [conversationId],
                "messageId": [messageId],
                "timestamp": [timestamp],
                "metadata": [metadata]
            }
        }
        raw_data = json.dumps(data, indent=4)
        #return {"data": raw_data, "url" : url, "headers": headers}
        logger.info(f"{req_id} - **Data sent to Conversation-Api**")
        # Doing internal request asynchronously
        timeout = Timeout(120, connect=130)  # 120 seconds read timeout, 130 seconds connect timeout
        async with AsyncClient(timeout=timeout) as client:
            response = await client.post(url, data=raw_data, headers=headers)
            logger.info(f"{req_id} - Response from Conversation-Api: {response}")
            json_data = response.json()
        resp = json_data['predictions'][0]
    except Exception as e:
        logger.error(f"{req_id} - Exception: {e}")
        raise HTTPException(status_code=500, detail="Error whilst contacting completion service")

    return {"received": timestamp} | resp