import datetime
import logging
import re
from typing import Optional
from urllib.parse import urlparse


logger = logging.getLogger(__name__)


ACTION_PATTERN = re.compile(r"/actions/([^/]+)")


def extract_action_slug(url: str) -> str:
    """
    Extract slug portion of a GorBilet URL for utm_content.
    """
    try:
        parsed = urlparse(url)
        match = ACTION_PATTERN.search(parsed.path)
        if match:
            return match.group(1)

        segments = [segment for segment in parsed.path.split("/") if segment]
        if segments:
            return segments[-1]
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error extracting action slug from %s: %s", url, exc)

    return "event"


def build_utm_content_with_date(base_slug: str, date_str: Optional[str] = None) -> str:
    """
    Combine slug with date (if provided) to form utm_content.
    """
    if not date_str:
        return base_slug

    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d-%m")
    except ValueError:
        formatted_date = date_str.replace("-", "")

    return f"{base_slug}-{formatted_date}"
