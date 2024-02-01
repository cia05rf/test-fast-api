import aiohttp
import asyncio
import nest_asyncio
from datetime import datetime

# Apply nest_asyncio
nest_asyncio.apply()

data = {
    "conversationId": "test",
    "messageId": "test",
    "message": "i have a headache"
}

async def fetch(session, url):
    st_time = str(datetime.now())
    async with session.post(url, json=data) as response:
        return st_time, await response.text(), response.status  # or response.json() depending on your API response

summary = {}
async def main():
    urls = ["https://test-fast-api.azurewebsites.net/product-conversation"] * 5
    # urls = ["https://prod-productgpt-as-01.azurewebsites.net/product-conversation"] * 1

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, url in enumerate(urls):
            print("POST", i)
            task = asyncio.create_task(fetch(session, url))
            tasks.append(task)
            await asyncio.sleep(2)  # Wait for 2 second before scheduling the next task
        
        responses = await asyncio.gather(*tasks)
        for st_time, response, status in responses:
            print(st_time, response, status)
            summary[status] = summary.get(status, 0) + 1
        print(summary)

# Run the main function in an asyncio event loop
asyncio.run(main())
