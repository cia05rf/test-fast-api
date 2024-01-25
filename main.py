import os
import requests
import json
import re
from fastapi import FastAPI, Request
from pydantic import BaseModel
from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime
import logging
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
from opencensus.trace.span import SpanKind
from opencensus.trace import config_integration
from opencensus.ext.azure.log_exporter import AzureLogHandler

app = FastAPI()

class ProductData(BaseModel):
    """
    ### Used for applying API input schema validation
    """
    message: str
    conversationId: str
    messageId: str

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
        logger.info("**request received in middleware**")
        response = await call_next(request)
    return response


@app.get("/welcome")
def welcome_page():
   
    return "Welcome to productGPT"
      

@app.post("/product-conversation")
async def read_products(data: ProductData, request: Request):
    """
    ### Takes user input from frontend(Chatbot) and pass it to productgpt API and returns the response
    - Args: Json Object such as :
        ```
        {
        
            "message": "Any string message. For e.g: Make my teeth shine please",
            "conversationId": "Hash value. For e.g: 2234567890123456789f3f66",
            "messageId": "Hash value. For e.g: 2234567890123456789f3f66"
            
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
                "products": [
                        {}
                ]
            
        }
        ```
    """

    # Declaring Variables
    product_api_target_type = os.environ.get('product_api_target_type')
    null_value_error = os.environ.get('null_value_error')
    mock_url = os.environ.get('mock_url')
    live_url = os.environ.get('live_url')
    try:
        logger.info("**Data Received from UI**")
        access_token = os.environ.get('access_token')
        message = data.message.strip()
        conversationId = data.conversationId.strip()
        messageId = data.messageId.strip()
        timestamp = str(datetime.now())
        # Remove special characters from message
        # message = re.sub(r'[^a-zA-Z0-9\s]', '', message)
    except Exception as e:
        logger.info(f"Exception: {e}")
        return {"Error": os.environ.get('invalid_json_message'), "StatusCode": "400"}

    if (message is None) or (message == ""):
        return {"Error": null_value_error, "StatusCode": "400"}
    if (conversationId is None) or (conversationId == ""):
        return {"Error": null_value_error, "StatusCode": "400"}
    if (messageId is None) or (messageId == ""):
        return {"Error": null_value_error, "StatusCode": "400"}

    if product_api_target_type == "mock":
        url = mock_url
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
                "timestamp": [timestamp]
            }
        }
        raw_data = json.dumps(data, indent=4)
        logger.info("**Data sent to Conversation-Api**")
        #return {"data": raw_data, "url" : url, "headers": headers}
        #Doing internal request
        x = requests.post(url, data=raw_data, headers=headers, verify=True)
        json_data = x.json()
        logger.info(f"Response from Conversation-Api: {x}")
      
    except Exception as e:
        logger.info(f"Exception: {e}")
        return {"Error": os.environ.get('internal_server_err_message'), "StatusCode": "500"}

    return json_data['predictions'][0]