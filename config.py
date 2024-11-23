from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from typing import List
from functools import lru_cache

import json


class SatColorPair(BaseModel):
    norad_id: str = Field(..., description="NORAD identifier")
    color: str = Field(
        ...,
        description="A color. Colors can be hex values, RGB565, or just plain English words like 'blue'"  # noqa: E501
    )


class Office(BaseModel):
    name: str = Field(..., description="The name of the office")
    lat: str = Field(..., description="The latitude for the office")
    lng: str = Field(..., description="The longitude for the office")
    sat_color_pairs: List[SatColorPair]


class Settings(BaseSettings):
    n2yo_api_key: str = Field(..., description="The API key for N2YO")
    office_profiles: List[Office] = Field(
        default=[
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
        ],
        description="A list of all office profiles",
    )


@lru_cache()
def load_settings():
    """
    config.json will take priority but we can set
    other variables via .env.

    Additionally, the LRU cache decorator will make
    settings fetching efficient.
    """
    try:
        with open("config.json", "r") as f:
            return Settings(**json.load(f))
    except FileNotFoundError:
        print("config.json not found. Falling back to default settings.")
        return Settings()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config.json: {e}")


settings = load_settings()
