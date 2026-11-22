"""Public NVIDIA catalog used by the preview. No account data is sent."""

import json
from urllib.error import URLError
from urllib.request import Request

from .model_registry import MODELS
from .nvidia import open_without_redirects

CATALOG_URL = "https://integrate.api.nvidia.com/v1/models"
MAX_CATALOG_BYTES = 1024 * 1024


def available_models(opener=open_without_redirects):
    """Return only listed models whose request contract the daemon supports."""
    request = Request(CATALOG_URL, headers={"Accept": "application/json"})
    try:
        with opener(request, timeout=8) as response:
            payload = response.read(MAX_CATALOG_BYTES + 1)
        if len(payload) > MAX_CATALOG_BYTES:
            raise ValueError("catalog size")
        records = json.loads(payload)["data"]
        if not isinstance(records, list) or any(
            not isinstance(row, dict) or not isinstance(row.get("id"), str)
            for row in records
        ):
            raise ValueError("catalog format")
    except (OSError, URLError, ValueError, KeyError, TypeError) as error:
        raise ValueError("NVIDIA indisponível. Tente atualizar a lista de modelos.") from error

    ids = {row["id"] for row in records}
    return tuple(model_id for model_id in MODELS if model_id in ids)
