# -*- coding: UTF-8 -*-

import imhdsk
import unicodedata
from trams import trams, trams_rev
from mapbox import Directions
from geopy.geocoders import Nominatim
from geopy.distance import vincenty


MAPBOX = Directions()

class Location:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def get_coord_set(self):
        return (self.latitude, self.longitude)

def normalize(stop):
    ''' Removes special characters from given stop. '''

    stop = unicodedata.normalize('NFKD', stop)
    normalized = ''

    for letter in stop:
        if not unicodedata.combining(letter):
            normalized += letter
    return normalized

def get_location(address):
    ''' Returns coordinates for given address. '''

    location = Nominatim().geocode(address)
    return Location(location.latitude, location.longitude)

def get_distance_meters(location_a_coords, location_b_coords):
    ''' Returns distance in meters between given points. '''

    distance_meters = int(vincenty(location_a_coords,
                                   location_b_coords).meters)
    return distance_meters

def get_distance_seconds(distance_meters):
    ''' Returns distance in seconds from given distance in meters. '''

    # 1.4m/s is the average walking speed of a human
    distance_seconds = int(distance_meters)/1.4
    return distance_seconds

def get_first_mhd(frm, to):
    ''' Returns first available route. '''

    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) == 0:
        print('No route found!')
        return
    return routes[0]


def get_mhd(frm, to):
    ''' Returns all available routes. '''

    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) == 0:
        print('No routes found!')
        return
    return routes

def get_nearest_stop(location):
    ''' Returns nearest stop to the provided location. '''

    stops = {}
    for name, coords in trams.items():
        distance = get_distance_meters(location.get_coord_set(), coords)
        stops.update({name: distance})

    nearest = min(stops.values())
    for name, distance in stops.items():
        if distance == nearest:
            return name

def get_tram_stop_location(name):
    ''' Returns latitude and longitude of tram stop called <name>. '''

    if name in trams:
        return trams[name]
    print('Tram stop is not in database.')

def get_tram_stop_name(lat_long):
    ''' Returns name of tram stop with <lat> and <long> coordinates. '''

    if lat_long in trams_rev:
        return trams_rev[lat_long]
    print('Tram with given latitude and longitude is not in database.')

def find_route(frm, to):
    ''' Finds route from location A to location B. '''

    if frm == to:
        print('Location from and to are the same.')
        return

    loc_a = get_location(frm)
    loc_b = get_location(to)
    stop_a = get_nearest_stop(loc_a)
    stop_b = get_nearest_stop(loc_b)
    print(get_first_mhd(normalize(stop_a), normalize(stop_b)))

find_route('Ružinovská 2747', 'Kollárovo námestie')
