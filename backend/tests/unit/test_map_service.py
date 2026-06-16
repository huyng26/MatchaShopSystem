from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services import map_service
from app.services.errors import ServiceError


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url, params):
        return FakeResponse(
            {
                "status": "OK",
                "results": [
                    {
                        "formatted_address": "Quan 3, TP.HCM, Viet Nam",
                        "place_id": "place-123",
                        "geometry": {
                            "location": {"lat": 10.7829, "lng": 106.6934},
                            "location_type": "ROOFTOP",
                        },
                    }
                ],
            }
        )


class FakeOpenRouteServiceClient(FakeAsyncClient):
    async def get(self, url, params, headers=None):
        return FakeResponse(
            {
                "features": [
                    {
                        "geometry": {"coordinates": [106.6934, 10.7829]},
                        "properties": {
                            "label": "Quan 3, TP.HCM, Viet Nam",
                            "id": "ors-place-123",
                            "confidence": 0.92,
                        },
                    }
                ],
            }
        )

    async def post(self, url, json, headers=None):
        return FakeResponse(
            {
                "distances": [
                    [0, 1500, 2400],
                    [1600, 0, 900],
                    [2500, 1000, 0],
                ],
                "durations": [
                    [0, 420, 700],
                    [430, 0, 220],
                    [720, 240, 0],
                ],
            }
        )


@pytest.mark.asyncio
async def test_geocode_address_returns_openrouteservice_result(monkeypatch):
    monkeypatch.setattr(
        map_service,
        "get_settings",
        lambda: SimpleNamespace(
            openrouteservice_api_key="key",
            maps_request_timeout_seconds=1,
            maps_provider="openrouteservice",
            shop_latitude=21.006237,
            shop_longitude=105.843127,
        ),
    )
    monkeypatch.setattr(map_service.httpx, "AsyncClient", FakeOpenRouteServiceClient)

    result = await map_service.geocode_address("Quan 3, TP.HCM")

    assert result.latitude == Decimal("10.7829000")
    assert result.longitude == Decimal("106.6934000")
    assert result.formatted_address == "Quan 3, TP.HCM, Viet Nam"
    assert result.place_id == "ors-place-123"
    assert result.provider == "openrouteservice"
    assert result.status == "OK"


@pytest.mark.asyncio
async def test_geocode_address_openrouteservice_prefers_candidate_near_shop(
    monkeypatch,
):
    class MultiCandidateOpenRouteServiceClient(FakeAsyncClient):
        async def get(self, url, params, headers=None):
            assert params["focus.point.lat"] == 21.006237
            assert params["focus.point.lon"] == 105.843127
            assert params["size"] == map_service.OPENROUTESERVICE_GEOCODE_CANDIDATE_LIMIT
            return FakeResponse(
                {
                    "features": [
                        {
                            "geometry": {"coordinates": [106.6934, 10.7829]},
                            "properties": {
                                "label": "100 Truong Dinh, TP.HCM, Viet Nam",
                                "id": "ors-hcm",
                                "confidence": 0.94,
                            },
                        },
                        {
                            "geometry": {"coordinates": [105.8429, 21.0008]},
                            "properties": {
                                "label": "100 Truong Dinh, Ha Noi, Viet Nam",
                                "id": "ors-hanoi",
                                "confidence": 0.9,
                            },
                        },
                    ],
                }
            )

    monkeypatch.setattr(
        map_service,
        "get_settings",
        lambda: SimpleNamespace(
            openrouteservice_api_key="key",
            maps_request_timeout_seconds=1,
            maps_provider="openrouteservice",
            shop_latitude=21.006237,
            shop_longitude=105.843127,
        ),
    )
    monkeypatch.setattr(
        map_service.httpx,
        "AsyncClient",
        MultiCandidateOpenRouteServiceClient,
    )

    result = await map_service.geocode_address("100 Truong Dinh, Ha Noi")

    assert result.latitude == Decimal("21.0008000")
    assert result.longitude == Decimal("105.8429000")
    assert result.formatted_address == "100 Truong Dinh, Ha Noi, Viet Nam"
    assert result.place_id == "ors-hanoi"


@pytest.mark.asyncio
async def test_route_matrix_returns_openrouteservice_matrix(monkeypatch):
    monkeypatch.setattr(
        map_service,
        "get_settings",
        lambda: SimpleNamespace(
            openrouteservice_api_key="key",
            maps_request_timeout_seconds=1,
            maps_provider="openrouteservice",
        ),
    )
    monkeypatch.setattr(map_service.httpx, "AsyncClient", FakeOpenRouteServiceClient)

    result = await map_service.build_route_matrix(
        [
            map_service.Coordinate(Decimal("10.776889"), Decimal("106.700806")),
            map_service.Coordinate(Decimal("10.782900"), Decimal("106.693400")),
            map_service.Coordinate(Decimal("10.788100"), Decimal("106.690500")),
        ]
    )

    assert result.distance_km == [
        [0, 1.5, 2.4],
        [1.6, 0, 0.9],
        [2.5, 1.0, 0],
    ]
    assert result.duration_minutes == [
        [0, 7, 12],
        [7, 0, 4],
        [12, 4, 0],
    ]
    assert result.provider == "openrouteservice"


@pytest.mark.asyncio
async def test_geocode_address_returns_google_result(monkeypatch):
    monkeypatch.setattr(
        map_service,
        "get_settings",
        lambda: SimpleNamespace(
            google_maps_api_key="key",
            maps_request_timeout_seconds=1,
            maps_provider="google",
        ),
    )
    monkeypatch.setattr(map_service.httpx, "AsyncClient", FakeAsyncClient)

    result = await map_service.geocode_address("Quan 3, TP.HCM")

    assert result.latitude == Decimal("10.7829000")
    assert result.longitude == Decimal("106.6934000")
    assert result.formatted_address == "Quan 3, TP.HCM, Viet Nam"
    assert result.place_id == "place-123"
    assert result.provider == "google"
    assert result.status == "OK"


@pytest.mark.asyncio
async def test_geocode_address_requires_api_key(monkeypatch):
    monkeypatch.setattr(
        map_service,
        "get_settings",
        lambda: SimpleNamespace(google_maps_api_key=None),
    )

    with pytest.raises(ServiceError) as error:
        await map_service.geocode_address("Quan 3, TP.HCM")

    assert error.value.code == "maps_api_key_required"


@pytest.mark.asyncio
async def test_geocode_address_rejects_ambiguous_partial_match(monkeypatch):
    class PartialMatchClient(FakeAsyncClient):
        async def get(self, url, params):
            return FakeResponse(
                {
                    "status": "OK",
                    "results": [
                        {
                            "partial_match": True,
                            "formatted_address": "TP.HCM",
                            "place_id": "place-ambiguous",
                            "geometry": {
                                "location": {"lat": 10.7, "lng": 106.7},
                                "location_type": "APPROXIMATE",
                            },
                        }
                    ],
                }
            )

    monkeypatch.setattr(
        map_service,
        "get_settings",
        lambda: SimpleNamespace(
            google_maps_api_key="key",
            maps_request_timeout_seconds=1,
            maps_provider="google",
        ),
    )
    monkeypatch.setattr(map_service.httpx, "AsyncClient", PartialMatchClient)

    with pytest.raises(ServiceError) as error:
        await map_service.geocode_address("bad address")

    assert error.value.code == "geocoding_ambiguous_address"
