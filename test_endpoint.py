import aiohttp
import asyncio
import nest_asyncio
from datetime import datetime
import random
import string


def generate_random_id(length=8):
    # Generate a random string of upper and lower case characters, and digits
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


LOAD = "50%"
N = 50
PLATFORM = "fastapi"
URL = "https://test-fast-api.azurewebsites.net/product-conversation"
# URL = "https://prod-productgpt-as-01.azurewebsites.net/product-conversation"
# URL = "https://adb-5427387077664746.6.azuredatabricks.net/serving-endpoints/product_gpt_ep_dev/invocations"

# Apply nest_asyncio
nest_asyncio.apply()

loads = {
    "50%": 2,  # Wait for 2 second before scheduling the next task
    "100%": 1,
    "150%": 0.75,
}

headers = {
    "Authorization": "Bearer dapi0972ce0717a8f667adf76ac1033d06e0-2"
}


async def fetch(url, d):
    # Increase total timeout to 120 seconds
    timeout = aiohttp.ClientTimeout(total=120)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=d, headers=headers) as response:
                # or response.json() depending on your API response
                return await response.text(), response.status
    except TimeoutError:
        return {}, 504


def gen_data(platform: str = "fastapi", n: int = N):
    if platform == "databricks":
        return [{
            "inputs": {
                "message": ["i have a headache"],
                "conversationId": [generate_random_id()],
                "messageId": [generate_random_id()],
                "timestamp": [str(datetime.now())],
                "metadata": [None]
            }
        } for _ in range(n)]
    else:
        return [{
            "conversationId": generate_random_id(),
            "messageId": generate_random_id(),
            "message": "i have a headache"
        } for _ in range(n)]


summary = {}


async def main():
    urls = [URL] * N
    data = gen_data(PLATFORM, N)
    tasks = []
    for i, (url, d) in enumerate(zip(urls, data)):
        print("POST", i)
        task = asyncio.create_task(fetch(url, d))
        tasks.append(task)
        await asyncio.sleep(
            loads[LOAD]
        )

    responses = await asyncio.gather(*tasks)
    for response, status in responses:
        print(response, status)
        summary[status] = summary.get(status, 0) + 1
    print(summary)

# Run the main function in an asyncio event loop
asyncio.run(main())
