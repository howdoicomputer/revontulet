from typing import Optional, List
from pydantic import BaseModel, Field


class GetSatellitesSchema(BaseModel):
    lat: float = Field(
        ...,
        description="Observer's latitude in decimal degrees."
    )
    lng: float = Field(
        ...,
        description="Observer's longitude in decimal degrees."
    )
    cat: int = Field(
        ...,
        description="Satellite category ID. See N2YO documentation for category mappings."  # noqa: E501
    )
    alt: Optional[float] = Field(
        0.0, description="Observer's altitude above sea level in meters. Default is 0."  # noqa: E501
    )
    search_radius: Optional[int] = Field(
        0,
        description="Search radius in degrees around the observer's zenith. Default is 90."  # noqa: E501
    )


class GetSatelliteSchema(BaseModel):
    norad_id: int = Field(..., description="NORAD ID")
    lat: float = Field(..., description="Latitude of observer point")
    lng: float = Field(..., description="Longitude of oberserver point")
    days: Optional[int] = Field(1, description="Number of days to return")
    limit: Optional[int] = Field(1, description="Number of results to return")
    tz: Optional[str] = Field(None, description="A timezone used to translate the UTC timestamp. Useful for clients. Ex: America/Los_Angeles")  # noqa: E501


class GetSatellitesAboveSchema(BaseModel):
    lat: float = Field(..., description="Observer latitutde")
    lng: float = Field(..., description="Observer longitude")
    format: Optional[str] = Field("json", description="The data format for response")
    search_radius: int = Field(..., description="Search radius in degrees around the observer's zenith. Default is 90.")
    sat_color_pairs: Optional[str] = Field(
        None,
        description="A comma-separated list of NORAD ID and color pairs (e.g., '12345,blue,65412,yellow')",
    )


class GetSatellitesProfileAboveSchema(BaseModel):
    name: str = Field(..., description="The name of the profile you want to grab")
    search_radius: int = Field(..., description="Search radius in degrees around the observer's zenith. Default is 90.")
    format: Optional[str] = Field("json", description="The data format for response")


class SatelliteColorPair(BaseModel):
    norad_id: int
    color: str


class ReturnSatellitesProfileAboveSchema(BaseModel):
    List[SatelliteColorPair]
