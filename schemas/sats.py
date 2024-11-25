from typing import Optional, List
from pydantic import BaseModel, Field, RootModel


class GetSatelliteReq(BaseModel):
    norad_id: int = Field(..., description="NORAD ID")
    lat: float = Field(..., description="Latitude of observer point")
    lng: float = Field(..., description="Longitude of oberserver point")
    days: Optional[int] = Field(1, description="Number of days to return")
    limit: Optional[int] = Field(1, description="Number of results to return")
    tz: Optional[str] = Field(None, description="A timezone used to translate the UTC timestamp. Ex: America/Los_Angeles")


class EventDetails(BaseModel):
    alt: float = Field(..., description="The altitude at the event, in degrees.")
    az: float = Field(..., description="The azimuth at the event, in degrees.")
    az_octant: str = Field(..., description="The azimuth octant direction (e.g., S, SE).")
    utc_datetime: str = Field(..., description="The UTC timestamp of the event in ISO format.")
    utc_timestamp: int = Field(..., description="The UTC timestamp of the event as a UNIX epoch.")
    is_sunlit: bool = Field(..., description="Whether the satellite is in sunlight at this event.")
    visible: bool = Field(..., description="Whether the satellite is visible to the observer.")
    client_time: str = Field(..., description="The event time in the client's local timezone.")


class SatellitePass(BaseModel):
    rise: EventDetails = Field(..., description="Details about the satellite's rise event.")
    culmination: EventDetails = Field(..., description="Details about the satellite's culmination event.")
    set: EventDetails = Field(..., description="Details about the satellite's set event.")
    visible: bool = Field(..., description="Whether the satellite is visible during the pass.")
    norad_id: int = Field(..., description="The NORAD ID of the satellite.")


class GetSatelliteRes(RootModel):
    root: List[SatellitePass] = Field(..., description="List of satellite passes.")


class GetSatellitesReq(BaseModel):
    lat: float = Field(..., description="Observer's latitude in decimal degrees.")
    lng: float = Field(..., description="Observer's longitude in decimal degrees.")
    cat: int = Field(..., description="Satellite category ID. See N2YO documentation for category mappings.")
    alt: Optional[float] = Field(0.0, description="Observer's altitude above sea level in meters. Default is 0.")
    search_radius: Optional[int] = Field(0, description="Search radius in degrees around the observer's zenith. Default is 90.")


class SatelliteAbove(BaseModel):
    satid: int = Field(..., description="The NORAD satellite ID.")
    satname: str = Field(..., description="The name of the satellite.")
    intDesignator: str = Field(..., description="The international designator for the satellite.")
    launchDate: str = Field(..., description="The launch date of the satellite in YYYY-MM-DD format.")
    satlat: float = Field(..., description="The current latitude of the satellite.")
    satlng: float = Field(..., description="The current longitude of the satellite.")
    satalt: float = Field(..., description="The current altitude of the satellite in kilometers.")


class GetSatellitesRes(BaseModel):
    above: List[SatelliteAbove] = Field(..., description="A list of satellites above the observer's location.")


class GetSatellitesAboveReq(BaseModel):
    lat: float = Field(..., description="Observer latitutde")
    lng: float = Field(..., description="Observer longitude")
    format: Optional[str] = Field("json", description="The data format for response")
    search_radius: int = Field(..., description="Search radius in degrees around the observer's zenith. Default is 90.")
    sat_color_pairs: str = Field(
        ...,
        description="A comma-separated list of NORAD ID and color pairs (e.g., '12345,blue,65412,yellow')"
    )


class SatColorPair(BaseModel):
    norad_id: int = Field(..., description="The NORAD ID of the satellite")
    color: str = Field(..., description="The color assocated with the satellite being present.")


class GetSatellitesAboveRes(RootModel[List[SatColorPair]]):
    """A list of satellite and color pairs."""


class GetSatellitesProfileAboveReq(BaseModel):
    name: str = Field(..., description="The name of the profile you want to grab")
    search_radius: int = Field(..., description="Search radius in degrees around the observer's zenith. Default is 90.")
    format: Optional[str] = Field("json", description="The data format for response")
