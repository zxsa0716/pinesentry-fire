"""STAC search and download helpers for Tanager / EMIT / Sentinel-2."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pystac_client import Client

TANAGER_STAC = "https://www.planet.com/data/stac/browser/tanager-core-imagery/catalog.json"
S2_STAC = "https://earth-search.aws.element84.com/v1"


@dataclass
class SceneInfo:
    id: str
    sensor: str
    datetime: str
    bbox: tuple
    href: str | None = None


def search_tanager(bbox: tuple, datetime_range: str | None = None) -> list[SceneInfo]:
    """Search the Tanager Open Data Catalog (static STAC)."""
    c = Client.open(TANAGER_STAC)
    items = c.search(bbox=bbox, datetime=datetime_range, max_items=20).item_collection()
    return [
        SceneInfo(
            id=it.id,
            sensor="tanager",
            datetime=str(it.datetime),
            bbox=tuple(it.bbox),
            href=it.assets.get("radiance", it.assets.get("default")).href if it.assets else None,
        )
        for it in items
    ]


def search_s2(bbox: tuple, datetime_range: str, cloud_max: int = 20) -> list[SceneInfo]:
    """Search Sentinel-2 L2A on AWS Open Data."""
    c = Client.open(S2_STAC)
    items = c.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=datetime_range,
        query={"eo:cloud_cover": {"lt": cloud_max}},
    ).item_collection()
    return [
        SceneInfo(id=it.id, sensor="s2", datetime=str(it.datetime), bbox=tuple(it.bbox))
        for it in items
    ]


def search_emit(bbox: tuple, datetime_range: tuple) -> list:
    """Search EMIT L2A SR via NASA EarthData."""
    import earthaccess
    earthaccess.login(persist=True)
    return earthaccess.search_data(
        short_name="EMITL2ARFL", bounding_box=bbox, temporal=datetime_range
    )
