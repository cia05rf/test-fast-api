import aiohttp
import asyncio
import nest_asyncio

# Apply nest_asyncio
nest_asyncio.apply()

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()  # or response.json() depending on your API response

async def main():
    urls = ["https://test-fast-api.azurewebsites.net/"] * 50

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, url in enumerate(urls):
            print("GET", i)
            task = asyncio.create_task(fetch(session, url))
            tasks.append(task)
            await asyncio.sleep(1)  # Wait for 1 second before scheduling the next task
        
        responses = await asyncio.gather(*tasks)
        for response in responses:
            print(response)

# Run the main function in an asyncio event loop
asyncio.run(main())
