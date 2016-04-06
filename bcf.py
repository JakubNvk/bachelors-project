# -*- coding: UTF-8 -*-
import imhdsk
from trams import trams
from mapbox import Directions
from geopy.geocoders import Nominatim
from geopy.distance import vincenty


MAPBOX = Directions()

class Location:
    def __init__(self, latitude, longitude):
        self.lat = latitude
        self.lon = longitude

    def __repr__(self):
        return self.lat + ' ' + self.lon

    def get_coord_list(self):
        return [self.lat, self.lon]


def get_location(address):
    ''' Returns coordinates for given address. '''

    geolocator = Nominatim()
    location = geolocator.geocode(address)
    return Location(location.latitude, location.longitude)

def get_distance(location_a, location_b):
    ''' Returns distance in meters and seconds between given points. '''

    distance_meters = int(vincenty(location_a.getCoordList,
                          location_b.getCoordList).meters)
    distance_seconds = int(distance_meters)/1.4
    # 1.4m/s is the average walking speed of a human
    return [distance_meters, distance_seconds]

def get_first_route(frm, to):
    ''' Returns first available route. '''

    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) > 0:
        return routes[0]
    print 'No route found!'

def get_routes(frm, to):
    ''' Returns all available routes. '''

    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) > 0:
        return routes
    print 'No routes found!'

def get_nearest_stop(location):
    ''' Returns nearest stop to the provided location. '''

    loc_coords = location.getCoordList()
    for t_stop in trams:
        #

def get_tram_stop_location(name):
    ''' Returns latitude and longitude of tram stop called <name>. '''

    if name in trams:
       return trams[name]
    print('Tram stop is not in database.')

def get_tram_stop_name(latitude, longitude):
    ''' Returns name of tram stop with <lat> and <long> coordinates. '''

    try:
        stop_name = trams.keys()[trams.values().index([latitude, longitude])]
        return stop_name
    except ValueError:
        print('Cannot retrieve stop name from database.')


getStopLocation('Aupark')
