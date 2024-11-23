from pydantic import BaseModel, Field
import hishel
import httpx

"""
Caching configuration to avoid overwhelming the upstream API.
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


class TerrestreClientGetPasses(BaseModel):
    norad_id: int = Field(..., description="The NORAD ID of the satellite")
    lat: float = Field(..., description="Latitude of the observer point")
    lng: float = Field(..., description="Longitude of the observer point")
    days: int = Field(1, description="Number of days to return")
    limit: int = Field(1, description="Number of results to return")


class TerrestreClient:
    """
    Client for the sat.terrestre.ar API to fetch satellite data.
    """
    BASE_URL = "https://sat.terrestre.ar"

    def __init__(self):
        pass

    async def get_passes(self, params: TerrestreClientGetPasses) -> dict:
        url = f"{self.BASE_URL}/passes/{params.norad_id}"

        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get(
                url,
                params={
                    "lat": params.lat,
                    "lon": params.lng,
                    "days": params.days,
                    "limit": params.limit
                }
            )

            if response.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Error {response.status_code}: {response.text}",
                    request=response.request,
                    response=response
                )

            data = response.json()

            if "error" in data:
                raise ValueError(f"API returned an error: {data['error']}")

            return data
