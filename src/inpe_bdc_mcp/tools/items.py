"""Ferramentas MCP para acesso a itens e assets STAC."""

from __future__ import annotations

from typing import Any

from ..client import BDCClient
from ..models.item import AssetInfo, DownloadInfo, ItemDetail


def get_item(collection_id: str, item_id: str) -> dict[str, Any]:
    """Retorna detalhes completos de um item STAC."""
    client = BDCClient.get_instance()
    data = client.get_item(collection_id, item_id)
    detail = client._item_to_detail(data)
    return detail.model_dump()


def list_item_assets(collection_id: str, item_id: str) -> dict[str, Any]:
    """Lista todos os assets de um item com metadados completos."""
    client = BDCClient.get_instance()
    data = client.get_item(collection_id, item_id)
    detail = client._item_to_detail(data)
    return {k: v.model_dump() for k, v in detail.assets.items()}


def get_asset_download_info(
    collection_id: str, item_id: str, asset_key: str
) -> dict[str, Any]:
    """Gera informações e snippets de download para um asset específico."""
    client = BDCClient.get_instance()
    data = client.get_item(collection_id, item_id)
    assets = data.get("assets", {})

    if asset_key not in assets:
        available = list(assets.keys())
        return {
            "error": f"Asset '{asset_key}' não encontrado.",
            "available_assets": available,
            "suggestion": f"Use um dos assets disponíveis: {', '.join(available)}",
        }

    asset = assets[asset_key]
    url = asset.get("href", "")
    mime = asset.get("type", "")
    requires_auth = not data.get("properties", {}).get("bdc:public", True)
    auth_header = None
    curl_auth = ""
    wget_auth = ""
    py_auth = ""
    r_auth = ""

    if client.auth.is_authenticated():
        auth_header = "x-api-key: <BDC_API_KEY>"
        curl_auth = ' -H "x-api-key: $BDC_API_KEY"'
        wget_auth = ' --header="x-api-key: $BDC_API_KEY"'
        py_auth = '\n    headers = {"x-api-key": os.getenv("BDC_API_KEY", "")}'
        r_auth = '\n# Adicione header de autenticação se necessário'

    info = DownloadInfo(
        url=url,
        mime_type=mime,
        curl_command=f'curl -L{curl_auth} -o "{asset_key}.tif" "{url}"',
        wget_command=f'wget{wget_auth} -O "{asset_key}.tif" "{url}"',
        python_rasterio_snippet=f'''import rasterio
import os
{py_auth if py_auth else ""}
# Acesso direto via rasterio (COG — streaming sem download completo):
env = rasterio.Env(GDAL_HTTP_HEADERFILE="/dev/null")
with env:
    with rasterio.open("{url}") as src:
        print(f"CRS: {{src.crs}}")
        print(f"Shape: {{src.shape}}")
        print(f"Bounds: {{src.bounds}}")
        # Ler janela específica:
        # window = rasterio.windows.from_bounds(*bbox, src.transform)
        # data = src.read(1, window=window)''',
        python_download_snippet=f'''import httpx
import os

url = "{url}"
headers = {{"x-api-key": os.getenv("BDC_API_KEY", "")}}

with httpx.stream("GET", url, headers=headers, follow_redirects=True) as r:
    r.raise_for_status()
    with open("{asset_key}.tif", "wb") as f:
        for chunk in r.iter_bytes(chunk_size=8192):
            f.write(chunk)
print("Download concluído: {asset_key}.tif")''',
        r_terra_snippet=f'''library(terra)
{r_auth}
r <- rast("{url}")
print(r)
plot(r)''',
        requires_auth=requires_auth,
        auth_header=auth_header,
    )
    return info.model_dump()


def get_thumbnail_url(collection_id: str, item_id: str) -> dict[str, Any]:
    """Retorna URL do thumbnail de um item para visualização rápida."""
    client = BDCClient.get_instance()
    data = client.get_item(collection_id, item_id)
    assets = data.get("assets", {})

    for key in ("thumbnail", "THUMBNAIL"):
        if key in assets:
            return {"url": assets[key].get("href", ""), "key": key}

    return {"url": None, "message": "Nenhum thumbnail disponível para este item."}


def get_quicklook_bands(collection_id: str) -> dict[str, Any]:
    """Retorna as bandas usadas para quicklook/thumbnail nessa coleção."""
    client = BDCClient.get_instance()
    data = client.get_collection(collection_id)
    props = data.get("properties", {})
    bands = props.get("bdc:bands_quicklook", [])

    return {
        "collection_id": collection_id,
        "quicklook_bands": bands,
        "note": "Estas bandas são usadas pelo BDC para gerar visualizações RGB rápidas.",
    }


def get_stac_item_as_geojson(collection_id: str, item_id: str) -> dict[str, Any]:
    """Retorna item como GeoJSON Feature puro."""
    client = BDCClient.get_instance()
    data = client.get_item(collection_id, item_id)

    return {
        "type": "Feature",
        "id": data.get("id"),
        "geometry": data.get("geometry"),
        "properties": data.get("properties", {}),
        "bbox": data.get("bbox"),
    }
