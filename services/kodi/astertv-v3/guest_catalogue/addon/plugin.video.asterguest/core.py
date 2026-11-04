"""Pure validation and Jellyfin response shaping for the Guest adapter."""

from __future__ import annotations

import re
import urllib.parse


ITEM_ID = re.compile(r"^[0-9a-fA-F]{32}$")
KINDS = {"Movie", "Series", "Season", "Episode"}
HLS_RESOURCE = re.compile(r"^(?:main\.m3u8|hls1/main/[0-9]+\.ts)$")
HLS_QUERY_FIELDS = {
    "MediaSourceId", "PlaySessionId", "VideoStreamIndex", "AudioStreamIndex",
    "VideoCodec", "AudioCodec", "MaxWidth", "VideoBitrate", "AudioBitrate",
    "TranscodingMaxAudioChannels", "SegmentContainer", "MinSegments",
    "BreakOnNonKeyFrames", "TranscodingProtocol", "runtimeTicks",
    "actualSegmentLengthTicks",
}
FIELDS = {
    "Id", "Name", "Type", "Overview", "ProductionYear", "IndexNumber",
    "ParentIndexNumber", "SeriesName", "RunTimeTicks", "ImageTags",
    "ParentId", "SeriesId", "SeasonId",
}


class GuestCatalogueError(ValueError):
    pass


def item_id(value):
    if not isinstance(value, str) or not ITEM_ID.fullmatch(value):
        raise GuestCatalogueError("invalid-item-id")
    return value.lower()


def shape_item(value):
    if not isinstance(value, dict) or value.get("Type") not in KINDS:
        raise GuestCatalogueError("unsupported-item")
    result = {key: value[key] for key in FIELDS if key in value}
    result["Id"] = item_id(result.get("Id"))
    for relation in ("ParentId", "SeriesId", "SeasonId"):
        if relation in result:
            result[relation] = item_id(result[relation])
    if not isinstance(result.get("Name"), str) or not result["Name"].strip():
        raise GuestCatalogueError("item-name-required")
    result["Name"] = result["Name"].strip()[:240]
    if isinstance(result.get("Overview"), str):
        result["Overview"] = result["Overview"].strip()[:4000]
    return result


def shape_items(value, allowed_types):
    if not isinstance(value, dict) or not isinstance(value.get("Items"), list):
        raise GuestCatalogueError("items-schema")
    allowed = set(allowed_types)
    rows = [shape_item(row) for row in value["Items"]]
    if any(row["Type"] not in allowed for row in rows):
        raise GuestCatalogueError("unexpected-item-type")
    return rows[:500]


def api_path(route, *, user_id, parent_id=None, item=None):
    user = item_id(user_id)
    if route == "libraries":
        return "/Users/" + user + "/Views"
    if route == "items":
        parent = item_id(parent_id)
        query = urllib.parse.urlencode({
            "ParentId": parent, "Recursive": "true", "SortBy": "SortName",
            "SortOrder": "Ascending", "Fields": "Overview,PrimaryImageAspectRatio",
            "IncludeItemTypes": item,
        })
        return "/Users/" + user + "/Items?" + query
    if route == "item":
        return "/Users/" + user + "/Items/" + item_id(item)
    raise GuestCatalogueError("unsupported-api-route")


def proxy_target(kind, identifier):
    identifier = item_id(identifier)
    if kind == "art":
        return "/Items/" + identifier + "/Images/Primary?maxWidth=640&quality=85"
    raise GuestCatalogueError("unsupported-proxy-route")


def validate_hls_route(resource, raw_query):
    if not HLS_RESOURCE.fullmatch(resource):
        raise GuestCatalogueError("hls-resource-denied")
    pairs = urllib.parse.parse_qsl(raw_query, keep_blank_values=False)
    if not pairs or any(key not in HLS_QUERY_FIELDS for key, _value in pairs):
        raise GuestCatalogueError("hls-query-denied")
    return resource + "?" + urllib.parse.urlencode(pairs)
