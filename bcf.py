# -*- coding: UTF-8 -*-
import imhdsk
from trams import trams, trams_rev
from mapbox import Directions
from geopy.geocoders import Nominatim
from geopy.distance import vincenty


MAPBOX = Directions()

class Location:
    def __init__(self, latitude, longitude, name=None, distance=None):
        self.name = name
        self.distance = distance
        self.latitude = latitude
        self.longitude = longitude

#    def __repr__(self):
#        return '{0} {1}'.format(self.latitude, self.longitude)

    def get_coord_set(self):
        return (self.latitude, self.longitude)


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

def get_first_route(frm, to):
    ''' Returns first available route. '''

    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) > 0:
        return routes[0]
    print('No route found!')

def get_routes(frm, to):
    ''' Returns all available routes. '''

    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) > 0:
        return routes
    print('No routes found!')

def get_nearest_stop(location):
    ''' Returns nearest stop to the provided location. '''

    stops = {}
    for name, coords in trams.items():
        distance = get_distance_meters(location.get_coord_set(), coords)
        stops.update({name: distance})

    nearest = min(stops.values())
    for name, distance in stops.items():
        if distance == nearest:
            print(name + ' ' + str(distance))

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
