from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.constants import SHOP_LATITUDE, SHOP_LONGITUDE
from app.services.errors import ServiceError
from app.utils.distance import haversine_distance_km


@dataclass(frozen=True)
class Coordinate:
    latitude: Decimal
    longitude: Decimal


@dataclass(frozen=True)
class GeocodeResult:
    latitude: Decimal
    longitude: Decimal
    formatted_address: str
    place_id: str | None
    provider: str
    status: str
    geocoded_at: datetime


@dataclass(frozen=True)
class RouteMatrix:
    distance_km: list[list[float]]
    duration_minutes: list[list[int]]
    provider: str


GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
OPENROUTESERVICE_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
OPENROUTESERVICE_MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"
FALLBACK_SPEED_KMPH = 25.0
MIN_OPENROUTESERVICE_CONFIDENCE = 0.6
OPENROUTESERVICE_GEOCODE_CANDIDATE_LIMIT = 5


async def geocode_address(address: str) -> GeocodeResult:
    settings = get_settings()
    provider = _maps_provider(settings)
    if provider == "openrouteservice":
        return await _geocode_address_openrouteservice(address, settings)
    if provider == "google":
        return await _geocode_address_google(address, settings)
    raise ServiceError(
        "unsupported_maps_provider",
        status_code=422,
        context={"maps_provider": provider},
    )


async def build_route_matrix(coordinates: list[Coordinate]) -> RouteMatrix:
    settings = get_settings()
    if len(coordinates) > 13:
        raise ServiceError("route_matrix_too_large", status_code=422)

    provider = _maps_provider(settings)
    if provider == "openrouteservice":
        if not getattr(settings, "openrouteservice_api_key", None):
            return _fallback_route_matrix(coordinates)
        return await _build_route_matrix_openrouteservice(coordinates, settings)
    if provider == "google":
        if not getattr(settings, "google_maps_api_key", None):
            return _fallback_route_matrix(coordinates)
        return await _build_route_matrix_google(coordinates, settings)
    raise ServiceError(
        "unsupported_maps_provider",
        status_code=422,
        context={"maps_provider": provider},
    )


async def _geocode_address_openrouteservice(address: str, settings: Any) -> GeocodeResult:
    api_key = getattr(settings, "openrouteservice_api_key", None)
    if not api_key:
        raise ServiceError("maps_api_key_required", status_code=503)

    params = {
        "text": address,
        "boundary.country": "VN",
        "focus.point.lat": getattr(settings, "shop_latitude", SHOP_LATITUDE),
        "focus.point.lon": getattr(settings, "shop_longitude", SHOP_LONGITUDE),
        "size": OPENROUTESERVICE_GEOCODE_CANDIDATE_LIMIT,
        "lang": "vi",
    }
    headers = {"Authorization": api_key, "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(
            timeout=settings.maps_request_timeout_seconds
        ) as client:
            response = await client.get(
                OPENROUTESERVICE_GEOCODE_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ServiceError("geocoding_timeout", status_code=504) from exc
    except httpx.HTTPError as exc:
        raise ServiceError("geocoding_provider_error", status_code=502) from exc

    payload = response.json()
    features = payload.get("features") or []
    if not features:
        raise ServiceError("geocoding_no_results", status_code=422)

    result = _best_openrouteservice_geocode_result(features, settings)
    geometry = result.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []
    if len(coordinates) < 2:
        raise ServiceError("geocoding_missing_coordinates", status_code=422)

    properties = result.get("properties") or {}

    return GeocodeResult(
        latitude=_decimal_coordinate(coordinates[1]),
        longitude=_decimal_coordinate(coordinates[0]),
        formatted_address=properties.get("label") or properties.get("name") or address,
        place_id=properties.get("id") or properties.get("gid"),
        provider="openrouteservice",
        status="OK",
        geocoded_at=datetime.now(timezone.utc),
    )


async def _geocode_address_google(address: str, settings: Any) -> GeocodeResult:
    if not settings.google_maps_api_key:
        raise ServiceError("maps_api_key_required", status_code=503)

    params = {
        "address": address,
        "key": settings.google_maps_api_key,
        "region": "vn",
        "language": "vi",
    }
    try:
        async with httpx.AsyncClient(
            timeout=settings.maps_request_timeout_seconds
        ) as client:
            response = await client.get(GOOGLE_GEOCODE_URL, params=params)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ServiceError("geocoding_timeout", status_code=504) from exc
    except httpx.HTTPError as exc:
        raise ServiceError("geocoding_provider_error", status_code=502) from exc

    payload = response.json()
    status = payload.get("status")
    if status != "OK":
        raise ServiceError(
            "geocoding_failed",
            status_code=422,
            context={"provider_status": status or "unknown"},
        )

    results = payload.get("results") or []
    if not results:
        raise ServiceError("geocoding_no_results", status_code=422)

    result = _best_google_geocode_result(results)
    geometry = result.get("geometry") or {}
    location = geometry.get("location") or {}
    if "lat" not in location or "lng" not in location:
        raise ServiceError("geocoding_missing_coordinates", status_code=422)

    if geometry.get("location_type") == "APPROXIMATE" and len(results) > 1:
        raise ServiceError("geocoding_ambiguous_address", status_code=422)

    return GeocodeResult(
        latitude=_decimal_coordinate(location["lat"]),
        longitude=_decimal_coordinate(location["lng"]),
        formatted_address=result.get("formatted_address") or address,
        place_id=result.get("place_id"),
        provider="google",
        status=status,
        geocoded_at=datetime.now(timezone.utc),
    )


async def _build_route_matrix_openrouteservice(
    coordinates: list[Coordinate],
    settings: Any,
) -> RouteMatrix:
    locations = [
        [float(coordinate.longitude), float(coordinate.latitude)]
        for coordinate in coordinates
    ]
    body = {
        "locations": locations,
        "metrics": ["distance", "duration"],
        "units": "m",
    }
    headers = {
        "Authorization": settings.openrouteservice_api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    try:
        async with httpx.AsyncClient(
            timeout=settings.maps_request_timeout_seconds
        ) as client:
            response = await client.post(
                OPENROUTESERVICE_MATRIX_URL,
                json=body,
                headers=headers,
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ServiceError("route_matrix_timeout", status_code=504) from exc
    except httpx.HTTPError as exc:
        raise ServiceError("route_matrix_provider_error", status_code=502) from exc

    payload = response.json()
    distances = payload.get("distances")
    durations = payload.get("durations")
    if distances is None or durations is None:
        raise ServiceError("route_matrix_failed", status_code=422)

    distance_matrix: list[list[float]] = []
    duration_matrix: list[list[int]] = []
    for distance_row, duration_row in zip(distances, durations, strict=False):
        parsed_distance_row: list[float] = []
        parsed_duration_row: list[int] = []
        for distance, duration in zip(distance_row, duration_row, strict=False):
            if distance is None or duration is None:
                raise ServiceError("route_matrix_element_failed", status_code=422)
            parsed_distance_row.append(round(distance / 1000, 3))
            parsed_duration_row.append(max(round(duration / 60), 0))
        distance_matrix.append(parsed_distance_row)
        duration_matrix.append(parsed_duration_row)

    _validate_square_matrix(distance_matrix, len(coordinates))
    _validate_square_matrix(duration_matrix, len(coordinates))
    return RouteMatrix(
        distance_km=distance_matrix,
        duration_minutes=duration_matrix,
        provider="openrouteservice",
    )


async def _build_route_matrix_google(
    coordinates: list[Coordinate],
    settings: Any,
) -> RouteMatrix:
    locations = "|".join(
        f"{coordinate.latitude},{coordinate.longitude}" for coordinate in coordinates
    )
    params = {
        "origins": locations,
        "destinations": locations,
        "key": settings.google_maps_api_key,
        "mode": "driving",
        "units": "metric",
        "language": "vi",
    }
    try:
        async with httpx.AsyncClient(
            timeout=settings.maps_request_timeout_seconds
        ) as client:
            response = await client.get(GOOGLE_DISTANCE_MATRIX_URL, params=params)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ServiceError("route_matrix_timeout", status_code=504) from exc
    except httpx.HTTPError as exc:
        raise ServiceError("route_matrix_provider_error", status_code=502) from exc

    payload = response.json()
    if payload.get("status") != "OK":
        raise ServiceError(
            "route_matrix_failed",
            status_code=422,
            context={"provider_status": payload.get("status") or "unknown"},
        )

    distance_matrix: list[list[float]] = []
    duration_matrix: list[list[int]] = []
    for row in payload.get("rows") or []:
        distance_row: list[float] = []
        duration_row: list[int] = []
        for element in row.get("elements") or []:
            if element.get("status") != "OK":
                raise ServiceError(
                    "route_matrix_element_failed",
                    status_code=422,
                    context={"provider_status": element.get("status") or "unknown"},
                )
            distance_row.append(round(element["distance"]["value"] / 1000, 3))
            duration_row.append(max(round(element["duration"]["value"] / 60), 0))
        distance_matrix.append(distance_row)
        duration_matrix.append(duration_row)

    _validate_square_matrix(distance_matrix, len(coordinates))
    _validate_square_matrix(duration_matrix, len(coordinates))
    return RouteMatrix(
        distance_km=distance_matrix,
        duration_minutes=duration_matrix,
        provider="google",
    )


def _best_google_geocode_result(results: list[dict[str, Any]]) -> dict[str, Any]:
    for result in results:
        if not result.get("partial_match"):
            return result
    raise ServiceError("geocoding_ambiguous_address", status_code=422)


def _best_openrouteservice_geocode_result(
    features: list[dict[str, Any]],
    settings: Any,
) -> dict[str, Any]:
    shop_latitude = float(getattr(settings, "shop_latitude", SHOP_LATITUDE))
    shop_longitude = float(getattr(settings, "shop_longitude", SHOP_LONGITUDE))
    candidates: list[tuple[float, dict[str, Any]]] = []
    low_confidence_values: list[float] = []

    for feature in features:
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        if len(coordinates) < 2:
            continue

        properties = feature.get("properties") or {}
        confidence = _optional_float(properties.get("confidence"))
        if confidence is not None and confidence < MIN_OPENROUTESERVICE_CONFIDENCE:
            low_confidence_values.append(confidence)
            continue

        try:
            distance = haversine_distance_km(
                shop_latitude,
                shop_longitude,
                float(coordinates[1]),
                float(coordinates[0]),
            )
        except (TypeError, ValueError):
            continue

        candidates.append((distance, feature))

    if candidates:
        return min(candidates, key=lambda candidate: candidate[0])[1]

    if low_confidence_values:
        raise ServiceError(
            "geocoding_low_confidence",
            status_code=422,
            context={"provider_confidence": max(low_confidence_values)},
        )

    raise ServiceError("geocoding_missing_coordinates", status_code=422)


def _decimal_coordinate(value: float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0000001"))


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fallback_route_matrix(coordinates: list[Coordinate]) -> RouteMatrix:
    distance_matrix: list[list[float]] = []
    duration_matrix: list[list[int]] = []
    for origin in coordinates:
        distance_row: list[float] = []
        duration_row: list[int] = []
        for destination in coordinates:
            distance = haversine_distance_km(
                float(origin.latitude),
                float(origin.longitude),
                float(destination.latitude),
                float(destination.longitude),
            )
            distance_row.append(round(distance, 3))
            duration_row.append(max(round(distance / FALLBACK_SPEED_KMPH * 60), 0))
        distance_matrix.append(distance_row)
        duration_matrix.append(duration_row)
    return RouteMatrix(
        distance_km=distance_matrix,
        duration_minutes=duration_matrix,
        provider="haversine_fallback",
    )


def _validate_square_matrix(matrix: list[list[Any]], expected_size: int) -> None:
    if len(matrix) != expected_size or any(len(row) != expected_size for row in matrix):
        raise ServiceError("route_matrix_invalid_shape", status_code=502)


def _maps_provider(settings: Any) -> str:
    return str(getattr(settings, "maps_provider", "openrouteservice")).lower()
