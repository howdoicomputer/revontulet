import hishel
import httpx
from pydantic import BaseModel, Field
from typing import List

"""
I don't want to overwhelm the upstream API so we're going to cache
responses to 200 GET requests.
"""
transport = hishel.AsyncCacheTransport(
    transport=httpx.AsyncHTTPTransport(),
    storage=hishel.AsyncInMemoryStorage(
        ttl=10
    ),
    controller=hishel.Controller(
        cacheable_methods=["GET"],
        cacheable_status_codes=[200],
        force_cache=True
    ),
)


class GetAboveInputSchema(BaseModel):
    observer_lat: float = Field(..., description="Observer's latitude in decimal degrees.")
    observer_lng: float = Field(..., description="Observer's longitude in decimal degrees.")
    observer_alt: float = Field(..., description="Observer's altitude in meters.")
    category_id: int = Field(..., description="Satellite category ID.")
    search_radius: int = Field(..., description="Search radius in kilometers.")


class SatelliteAboveSchema(BaseModel):
    satid: int = Field(..., description="Satellite NORAD ID.")
    satname: str = Field(..., description="Satellite name.")
    intDesignator: str = Field(..., description="International designator.")
    launchDate: str = Field(..., description="Launch date of the satellite.")
    satlat: float = Field(..., description="Current latitude of the satellite.")
    satlng: float = Field(..., description="Current longitude of the satellite.")
    satalt: float = Field(..., description="Current altitude of the satellite.")


class GetAboveOutputSchema(BaseModel):
    above: List[SatelliteAboveSchema] = Field(..., description="List of satellites above the given location.")


class N2YOClient:
    """
    There is a public N2YO client out there but it is based off
    of the requests library. The requests library is synchronous
    so it blocks FastAPI's event loop. I need to create a new
    one using httpx.
    """
    BASE_URL = "https://api.n2yo.com/rest/v1/satellite"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_above(self, params: GetAboveInputSchema) -> GetAboveOutputSchema:
        """
        I only really need this one method.

        Also, N2YO doesn't use query parameters for its GET requests (yuck)
        """
        url = (
            f"{self.BASE_URL}/above/"
            f"{params.observer_lat}/"
            f"{params.observer_lng}/"
            f"{params.observer_alt}/"
            f"{params.search_radius}/"
            f"{params.category_id}"
        )

        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get(url, params={"apiKey": self.api_key})

            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Error {response.status_code}: {response.text}",
                    request=response.request,
                    response=response
                )

            """
            There is an error where a response can come back 200 but we
            get a SQL error as part of the payload. This seems to be happening
            when there are zero results returned.

            This is dumb.

            We are going to check for the exact error message and just
            handle it internally to deliver an empty object.
            """
            exact_error_message = "You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near ')' at line 7"  # noqa: E501
            data = response.json()
            if "error" in data and data["error"] == exact_error_message:
                return GetAboveOutputSchema(above=[])

            if "error" in data:
                raise ValueError(f"API returned an unexpected error: {data['error']}")

            return GetAboveOutputSchema(**data)
