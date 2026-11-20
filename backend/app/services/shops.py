from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0088


def distance_in_kilometers(
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
) -> float:
    latitude_delta = radians(destination_latitude - origin_latitude)
    longitude_delta = radians(destination_longitude - origin_longitude)
    origin_latitude_radians = radians(origin_latitude)
    destination_latitude_radians = radians(destination_latitude)

    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(origin_latitude_radians)
        * cos(destination_latitude_radians)
        * sin(longitude_delta / 2) ** 2
    )
    central_angle = 2 * asin(sqrt(min(1.0, haversine)))
    return EARTH_RADIUS_KM * central_angle
