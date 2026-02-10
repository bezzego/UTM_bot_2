from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def build_utm_url(base_url: str, utm_source: str, utm_medium: str, utm_campaign: str, utm_content: str = None) -> str:
    """
    Формирует ссылку с добавленными UTM-параметрами.
    Если в базовой ссылке уже есть параметры, добавляет новые через '&'.
    """
    separator = '&' if '?' in base_url else '?'
    # Избежать двойного разделителя, если ссылка уже заканчивается на '?' или '&'
    if base_url.endswith('?') or base_url.endswith('&'):
        separator = ''
    
    # Формируем базовые UTM-параметры
    utm_params = f"utm_source={utm_source}&utm_medium={utm_medium}&utm_campaign={utm_campaign}"
    
    # Добавляем utm_content, если он передан
    if utm_content:
        utm_params += f"&utm_content={utm_content}"
    
    return f"{base_url}{separator}{utm_params}"


def build_utm_url_advanced(base_url: str, utm_params: dict) -> str:
    """
    Расширенная версия для формирования ссылки с UTM-параметрами.
    Принимает словарь с UTM-параметрами.
    """
    parsed = urlparse(base_url)
    query_params = dict(parse_qsl(parsed.query))
    
    # Добавляем или обновляем UTM-параметры
    for key, value in utm_params.items():
        if value:  # Добавляем только если значение не пустое
            query_params[key] = value
    
    new_query = urlencode(query_params, doseq=True)
    
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))


def extract_utm_params(url: str) -> dict:
    """
    Извлекает UTM-параметры из ссылки.
    """
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query))
    
    utm_params = {}
    for key in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']:
        if key in query_params:
            utm_params[key] = query_params[key]
    
    return utm_params


def remove_utm_params(url: str) -> str:
    """
    Удаляет все UTM-параметры из ссылки.
    """
    parsed = urlparse(url)
    query_params = dict(parse_qsl(parsed.query))
    
    # Удаляем UTM-параметры
    utm_keys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
    for key in utm_keys:
        query_params.pop(key, None)
    
    new_query = urlencode(query_params, doseq=True)
    
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))


def is_utm_url(url: str) -> bool:
    """
    Проверяет, содержит ли ссылка UTM-параметры.
    """
    utm_params = extract_utm_params(url)
    return len(utm_params) > 0


def validate_utm_params(utm_source: str = None, utm_medium: str = None, utm_campaign: str = None) -> bool:
    """
    Проверяет обязательные UTM-параметры на наличие значений.
    """
    return all([utm_source, utm_medium, utm_campaign])