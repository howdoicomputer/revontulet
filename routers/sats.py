from fastapi import HTTPException, APIRouter, Depends
from fastapi.responses import StreamingResponse
from revontulet.libs.n2yo_client.client import N2YOClient, GetAboveInputSchema
from revontulet.libs.terrestre_client.client import TerrestreClient, TerrestreClientGetPasses
from typing import AsyncGenerator
from revontulet.schemas.sats import (
    GetSatelliteSchema,
    GetSatellitesSchema,
    GetSatellitesAboveSchema,
    GetSatellitesProfileAboveSchema
)
from ..config import settings
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
import json


router = APIRouter()
n2yo_client = N2YOClient(settings.n2yo_api_key)
terrestre_client = TerrestreClient()


@router.get("/satellite")
async def get_satellite(params: GetSatelliteSchema = Depends()):
    """
    This route mirrors the Terrestre Pass API but adds some additional
    annotations. Namely, it makes it so that the a caller can pass
    in a timezone and receive back a translation of the UTC timestamp
    to a local time.
    """
    get_passes_params = TerrestreClientGetPasses(**params.model_dump(exclude={"tz"}))

    data = await terrestre_client.get_passes(get_passes_params)

    """
    I want to annotate the returned pass data so that a client
    can localize the projected pass times to their time zone.
    """
    user_tz = ZoneInfo(params.tz or "UTC")
    for passes in data:
        for key in ["rise", "culmination", "set"]:
            utc_time = datetime.fromisoformat(
                passes[key]["utc_datetime"].replace("Z", "+00:00")
            )
            client_time = utc_time.astimezone(user_tz)
            passes[key]["client_time"] = client_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    return data


@router.get("/satellites")
async def get_satellites(params: GetSatellitesSchema = Depends()):
    """
    Fetch satellites above a specific observer location using the N2YO API.

    This is exposed for flexibility and general testing. All it does is act as a proxy for
    N2YO's main input. It does add caching and the API token is handled so it's not a 1:1 comparison.

    For example, here is using this endpoint to grab four satellites that are over Toulouse, France:

    revontulet main*​
    ❯ curl -s -X 'GET' \
            'http://0.0.0.0:8000/api/satellites?lat=43.6045&lng=1.444&cat=0&alt=0&search_radius=15' \
            -H 'accept: application/json' | jq -r '.above | map(.satid) | .[:4] | join(",")'

    8018,10155,11690,12671
    """
    try:
        get_above_input = GetAboveInputSchema(
            observer_lat=params.lat,
            observer_lng=params.lng,
            observer_alt=params.alt or 0.0,
            category_id=params.cat,
            search_radius=params.search_radius or 0
        )

        result = await n2yo_client.get_above(get_above_input)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/satellites/above")
async def get_satellites_above(params: GetSatellitesAboveSchema = Depends()):
    """
    Given a dictionary of NORAD_IDs and colors (sat_color_pairs), a search radius, and a lat/lng pair,
    this route will query out the satellites above the lat/lng pair and then check to see which of the
    passed in satellites (NORAD_IDs) are over that set of coordinates. If they are then
    the response will be the filtered set of sat_color_pairs will be returned either
    as JSON or text (depending on parameter).

    For example,

    Assuming that satellite 11690 is over Toulouse, France with a 90 degree search radius,

    revontulet main*​
    ❯ curl -X 'GET' \
         'http://0.0.0.0:8000/api/satellites/above?lat=43.6045&lng=1.444&search_radius=90&sat_color_pairs=11690,blue' \
         -H 'accept: application/json'
    "NORAD_11690: blue"⏎
    """
    try:
        # Parse the `sat_color_pairs` into a dictionary
        sat_color_pairs_dict = {}
        if params.sat_color_pairs:
            parts = params.sat_color_pairs.split(",")

            if len(parts) % 2 != 0:
                raise ValueError("sat_color_pairs must contain an even number of items (NORAD ID, color pairs)")

            sat_color_pairs_dict = {int(parts[i]): parts[i + 1] for i in range(0, len(parts), 2)}

        # Prepare the input schema for the N2YO client
        get_above_input = GetAboveInputSchema(
            observer_lat=params.lat,
            observer_lng=params.lng,
            observer_alt=0,
            category_id=0,
            search_radius=params.search_radius
        )

        result = await n2yo_client.get_above(get_above_input)

        # Filter the satellites based on sat_color_pairs
        filtered = [
            {"norad_id": satellite.satid, "color": sat_color_pairs_dict.get(satellite.satid)}
            for satellite in result.above
            if satellite.satid in sat_color_pairs_dict
        ]

        match params.format:
            case "json":
                return filtered
            case "text":
                formatted_data = ", ".join(
                    f"NORAD_ID_{pair['norad_id']}: {pair['color']}" for pair in filtered
                )

                return formatted_data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))


@router.get("/satellites/above/stream")
async def get_satellites_above_stream(params: GetSatellitesAboveSchema = Depends()):
    """
    Same as /satellites/above but creates an HTTP stream and delivers results over that
    stream on a 10 second timer.
    """
    sat_color_pairs_dict = {}
    if params.sat_color_pairs:
        parts = params.sat_color_pairs.split(",")
        if len(parts) % 2 != 0:
            raise ValueError("sat_color_pairs must contain an even number of items (NORAD ID, color pairs)")

        sat_color_pairs_dict = {int(parts[i]): parts[i + 1] for i in range(0, len(parts), 2)}

    get_above_input = GetAboveInputSchema(
        observer_lat=params.lat,
        observer_lng=params.lng,
        observer_alt=0,
        category_id=0,
        search_radius=params.search_radius
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        while True:
            try:
                result = await n2yo_client.get_above(get_above_input)

                filtered = [
                    {"norad_id": satellite.satid, "color": sat_color_pairs_dict.get(satellite.satid)}
                    for satellite in result.above
                    if satellite.satid in sat_color_pairs_dict
                ]

                match params.format:
                    case "text":
                        formatted_data = ", ".join(
                            f"NORAD_ID_{pair['norad_id']}: {pair['color']}" for pair in filtered
                        )

                        yield f"{formatted_data}\n"
                    case "json":
                        yield json.dumps(filtered) + "\n"

                await asyncio.sleep(10)
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/satellites/above/profile")
async def get_satellites_profile_above(params: GetSatellitesProfileAboveSchema = Depends()):  # noqa: E501
    """
    This route uses premade profiles to return satellite data
    for destinations that we know we care about.

    For example, we can create a profile that pairs the Loft
    Orbital satellites with a set of colors and then associate
    those satellites with the coordinates for the city of
    Toulouse. Let's call that profile 'toulouse.'

    Then a client that wants to control a device for that office
    can issue a GET request to /api/satellites/above/profile
    with the query parameter of 'name=toulouse' to receive the
    satellite data for that set of conditions.

    The defaults are listed in the OpenAPI docs and include
    Golden, SF, and Toulouse. However, this is an overridable
    behavior.
    """
    profiles = settings.office_profiles
    profile = next(
        (office for office in profiles if office.name == params.name), None
    )

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    get_above_input = GetAboveInputSchema(
        observer_lat=profile.lat,
        observer_lng=profile.lng,
        observer_alt=0,
        category_id=0,
        search_radius=params.search_radius
    )

    try:
        result = await n2yo_client.get_above(get_above_input)
        satids = {str(sat.satid) for sat in result.above}

        matching_pairs = [
            pair for pair in profile.sat_color_pairs if pair.norad_id in satids
        ]

        return matching_pairs

        match params.format:
            case "text":
                formatted_data = ", ".join(
                    f"NORAD_ID_{pair.norad_id}: {pair.color}" for pair in matching_pairs
                )

                return f"{formatted_data}\n"
            case "json":
                serialized_data = [pair.dict() for pair in matching_pairs]
                return json.dumps(serialized_data) + "\n"

    except Exception as e:
        raise HTTPException(status_code=500, detail=(str(e)))


@router.get("/satellites/above/profile/stream")
async def stream_satellites_profile_above(
    params: GetSatellitesProfileAboveSchema = Depends()
) -> StreamingResponse:
    """
    This route is the same as /satellites/above/profile except
    it continuously streams the results on a 10 second timer.

    This is a useful route but it can be abused as keeping a
    connection open can be expensive. It's preferrable to have
    a client long poll an endpoint.
    """

    profiles = settings.office_profiles
    profile = next(
        (office for office in profiles if office.name == params.name), None
    )

    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{params.name}' not found."
        )

    get_above_input = GetAboveInputSchema(
        observer_lat=profile.lat,
        observer_lng=profile.lng,
        observer_alt=0,
        category_id=0,
        search_radius=params.search_radius
    )

    async def event_stream() -> AsyncGenerator[str, None]:
        while True:
            try:
                result = await n2yo_client.get_above(get_above_input)
                satids = {str(sat.satid) for sat in result.above}

                matching_pairs = [
                    pair for pair in profile.sat_color_pairs if pair.norad_id in satids
                ]

                if matching_pairs != []:
                    match params.format:
                        case "text":
                            formatted_data = ", ".join(
                                f"NORAD_ID_{pair.norad_id}: {pair.color}" for pair in matching_pairs
                            )

                            yield f"{formatted_data}\n"
                        case "json":
                            serialized_data = [pair.dict() for pair in matching_pairs]
                            yield json.dumps(serialized_data) + "\n"

                await asyncio.sleep(10)
            except Exception as e:
                yield f"event: error\ndata: {str(e)}\n\n"
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")
