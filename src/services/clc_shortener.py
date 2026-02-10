import aiohttp
import logging

async def shorten_url(long_url: str, api_key: str) -> str:
    """
    Отправляет длинную ссылку в API сервиса clc.li для сокращения.
    Тело запроса содержит ключ 'url'.
    Возвращает короткую ссылку из полей 'short', 'shorturl', 'data.short' или 'url.shorturl'.
    Логирует ошибки HTTP и ошибки, указанные в поле 'error' ответа.
    Возвращает None в случае ошибки.
    """
    api_endpoint = "https://clc.li/api/url/add"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {"url": long_url}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api_endpoint, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("error", 0) != 0:
                        logging.error(f"CLC API logical error: {result}")
                        return None
                    short_url = None
                    if "short" in result:
                        short_url = result["short"]
                    elif "shorturl" in result:
                        short_url = result["shorturl"]
                    elif "data" in result and "short" in result["data"]:
                        short_url = result["data"]["short"]
                    elif "url" in result and "shorturl" in result["url"]:
                        short_url = result["url"]["shorturl"]
                    return short_url
                else:
                    err_text = await response.text()
                    logging.error(f"CLC API HTTP error {response.status}: {err_text}")
                    return None
    except Exception as e:
        logging.exception("Exception during shorten_url call")
        return None