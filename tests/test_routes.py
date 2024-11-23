import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from revontulet.main import app
from revontulet.config import settings, Office, SatColorPair
from revontulet.libs.n2yo_client.client import GetAboveOutputSchema, SatelliteAboveSchema

client = TestClient(app)

"""
The general format for these tests is to mock out all input/output
data as well as mock the connections to upstream external services
in order to make sure the HTTP requests we make to the API don't
actually require the APIs to be functional.

These tests don't need Internet to run as everything is mocked out.
"""


@pytest.fixture
def mock_settings(monkeypatch):
    """Mock settings to provide consistent office profiles."""
    mock_profiles = [
        Office(
            name="toulouse",
            lat="43.6045",
            lng="1.444",
            sat_color_pairs=[
                SatColorPair(norad_id="55076", color="blue"),
                SatColorPair(norad_id="48915", color="white"),
                SatColorPair(norad_id="59126", color="red"),
            ],
        ),
        Office(
            name="sf",
            lat="37.7749",
            lng="-122.4194",
            sat_color_pairs=[
                SatColorPair(norad_id="55076", color="red"),
                SatColorPair(norad_id="48915", color="white"),
                SatColorPair(norad_id="59126", color="blue"),
            ],
        ),
        Office(
            name="golden",
            lat="39.7555",
            lng="-105.2211",
            sat_color_pairs=[
                SatColorPair(norad_id="55076", color="red"),
                SatColorPair(norad_id="48915", color="white"),
                SatColorPair(norad_id="59126", color="blue"),
            ],
        ),
    ]

    # Use monkeypatch to override `settings.office_profiles`
    monkeypatch.setattr(settings, "office_profiles", mock_profiles)


@pytest.fixture
def mock_n2yo_response():
    """Mock response from the N2YO client."""
    return GetAboveOutputSchema(
        above=[
            SatelliteAboveSchema(
                satid=55076,
                satname="EXPLORER 7",
                intDesignator="1959-009A",
                launchDate="1959-10-13",
                satlat=47.9982,
                satlng=-0.4382,
                satalt=549.2611,
            )
        ]
    )


@pytest.fixture
def mock_terrestre_response():
    """Mock response from the Terrestre client."""
    return [
        {
            "rise": {
                "alt": "10.01",
                "az": "21.70",
                "az_octant": "N",
                "utc_datetime": "2024-11-21 15:34:19.319281+00:00",
                "utc_timestamp": 1732203259,
                "is_sunlit": True,
                "visible": False,
            },
            "culmination": {
                "alt": "53.94",
                "az": "100.37",
                "az_octant": "E",
                "utc_datetime": "2024-11-21 15:37:49.045240+00:00",
                "utc_timestamp": 1732203469,
                "is_sunlit": True,
                "visible": False,
            },
            "set": {
                "alt": "10.00",
                "az": "179.08",
                "az_octant": "S",
                "utc_datetime": "2024-11-21 15:41:16.328043+00:00",
                "utc_timestamp": 1732203676,
                "is_sunlit": True,
                "visible": False,
            },
            "norad_id": 55076,
        }
    ]


@pytest.mark.asyncio
@patch("revontulet.libs.n2yo_client.client.N2YOClient.get_above", new_callable=AsyncMock)
async def test_get_satellites(mock_get_above, mock_n2yo_response):
    """Test the /api/satellites endpoint."""
    mock_get_above.return_value = mock_n2yo_response

    response = client.get("/api/satellites", params={
        "lat": 43.6045,
        "lng": 1.444,
        "cat": 0,
        "alt": 0,
        "search_radius": 10
    })

    assert response.status_code == 200
    assert response.json()["above"][0]["satid"] == 55076


@pytest.mark.asyncio
@patch("revontulet.libs.terrestre_client.client.TerrestreClient.get_passes", new_callable=AsyncMock)
async def test_get_satellite(mock_get_passes, mock_terrestre_response):
    """Test the /api/satellite endpoint."""
    mock_get_passes.return_value = mock_terrestre_response

    response = client.get("/api/satellite", params={
        "norad_id": "55076",
        "lat": 43.6045,
        "lng": 1.444,
        "days": 1,
        "limit": 1,
        "tz": "America/Los_Angeles"
    })

    assert response.status_code == 200
    data = response.json()
    assert data[0]["rise"]["client_time"].endswith("PST")
    assert data[0]["culmination"]["client_time"].endswith("PST")
    assert data[0]["set"]["client_time"].endswith("PST")


@pytest.mark.asyncio
@patch("revontulet.libs.n2yo_client.client.N2YOClient.get_above", new_callable=AsyncMock)
async def test_get_satellites_above(mock_get_above, mock_n2yo_response):
    """Test the /api/satellites/above endpoint."""
    mock_get_above.return_value = mock_n2yo_response

    response = client.get("/api/satellites/above", params={
        "lat": 43.6045,
        "lng": 1.444,
        "search_radius": 90,
        "sat_color_pairs": "55076,blue"
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["norad_id"] == 55076
    assert data[0]["color"] == "blue"


@pytest.mark.asyncio
@patch("revontulet.libs.n2yo_client.client.N2YOClient.get_above", new_callable=AsyncMock)
async def test_get_satellites_profile_above(mock_get_above, mock_n2yo_response, mock_settings):
    """Test the /api/satellites/above/profile endpoint."""
    mock_get_above.return_value = mock_n2yo_response

    response = client.get("/api/satellites/above/profile", params={
        "name": "toulouse",
        "search_radius": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["norad_id"] == "55076"
    assert data[0]["color"] == "blue"

# This test request requires work and bleh.
#
# @pytest.mark.asyncio
# @patch("revontulet.libs.n2yo_client.client.N2YOClient.get_above", new_callable=AsyncMock)
# async def test_stream_satellites_profile_above(mock_get_above, mock_n2yo_response, mock_settings):
#     """Test the /api/satellites/above/profile/stream endpoint."""
#     mock_get_above.return_value = mock_n2yo_response

#     with client.stream("GET", "/api/satellites/above/profile/stream?name=toulouse&search_radius=10&format=text") as stream:  # noqa: E501
#         assert stream.status_code == 200
#         lines = list(stream.iter_lines())
#         assert "55076: blue" in lines[0]
