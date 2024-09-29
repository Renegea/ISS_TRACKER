import math

import numpy as np
import requests
import geocoder

ISS_api = 'https://api.wheretheiss.at/v1/satellites/25544'


def get_observer_position():
    geo = geocoder.ip('me')
    latitude, longitude = geo.latlng
    return latitude, longitude


def get_iss_position(API_URL: str):
    response = requests.get(API_URL)

    if response.status_code == 200:
        data = response.json()
        return data['longitude'], data['latitude'], data['altitude']
    else:
        return Exception('Failed to connect API.')


def rad_to_deg(inp):  # rad to deg
    return 180 / math.pi * inp


def deg_to_rad(inp):  # deg to rad
    return math.pi / 180 * inp


def spherical_to_cartesian(altitude, longitude, latitude):
    r = altitude + 6371000
    theta = math.fmod(longitude + 360, 360)
    phi = 90 - latitude

    x = r * math.cos(deg_to_rad(theta)) * math.sin(deg_to_rad(phi))
    y = r * math.sin(deg_to_rad(theta)) * math.sin(deg_to_rad(phi))
    z = r * math.cos(deg_to_rad(phi))
    return [x, y, z]


def cartesian_to_spherical(x, y, z):
    r = math.sqrt(x ** 2 + y ** 2 + z ** 2)
    theta = math.atan2(y, x)
    phi = np.arccos(z / r)

    return [r, theta, phi]


def calc_transformation(lon, lat):
    r = 1
    theta = math.fmod(lon + 360, 360)
    phi = 90 - lat

    r_hat = [np.cos(deg_to_rad(theta)) * np.sin(deg_to_rad(phi)),
             np.sin(deg_to_rad(phi)) * np.sin(deg_to_rad(theta)),
             np.cos(deg_to_rad(phi))]

    phi_hat = [np.cos(deg_to_rad(phi)) * np.cos(deg_to_rad(theta)),
               np.cos(deg_to_rad(phi)) * np.sin(deg_to_rad(theta)),
               -np.sin(deg_to_rad(phi))]

    theta_hat = [np.cos(deg_to_rad(theta)),
                 -np.sin(deg_to_rad(theta)),
                 0]

    transformation_matrix = np.array([[-phi_hat[0], -theta_hat[0], r_hat[0]],
                                      [-phi_hat[1], -theta_hat[1], r_hat[1]],
                                      [-phi_hat[2], -theta_hat[2], r_hat[2]]])

    inverse_matrix = np.linalg.inv(transformation_matrix)
    return inverse_matrix


def angles_between_ISS(longitude, latitude, ISS_longitude, ISS_latitude, ISS_altitude):
    observer_cartesian = spherical_to_cartesian(0, longitude, latitude)
    ISS_cartesian = spherical_to_cartesian(ISS_altitude, ISS_longitude, ISS_latitude)
    displacement = [ISS_cartesian[0] - observer_cartesian[0], ISS_cartesian[1] - observer_cartesian[1], ISS_cartesian[2] - observer_cartesian[2]]
    final_crt = np.dot(calc_transformation(longitude, latitude), displacement)
    final_sph = cartesian_to_spherical(final_crt[0], final_crt[1], final_crt[2])
    final_sph = [final_sph[0], rad_to_deg(final_sph[1]), rad_to_deg(final_sph[2])]

    return final_sph


def main():
    obs_location = {}

    latitude, longitude = get_observer_position()
    ISS_longitude, ISS_latitude, ISS_altitude = get_iss_position(ISS_api)

    result = angles_between_ISS(longitude, latitude, ISS_longitude, ISS_latitude, ISS_altitude * 1000)

    print(f"Mesafe: {result[0]:.2f} metre")
    print(f"Kuzey: {(result[1] + 360)%360:.2f} derece")
    print(f"Yukarıdan Açı: {result[2]:.2f} derece")
