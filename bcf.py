# -*- coding: UTF-8 -*-
import imhdsk
from geopy.geocoders import Nominatim
from geopy.distance import vincenty


STOPS = open('stops/stops.txt', 'r')

class Location:
    def __init__(self, latitude, longitude):
        self.lat = latitude
        self.lon = longitude

    def __repr__(self):
        return self.lat + ' ' + self.lon

    def getCoordList(self):
        return (self.lat, self.lon)


def getLocation(address):
    ''' Returns coordinates for given address. '''
    geolocator = Nominatim()
    location = geolocator.geocode(address)
    return Location(location.latitude, location.longitude)

def getDistance(location_a, location_b):
    ''' Returns distance in meters and seconds between given points. '''
    distance_meters = int(vincenty(location_a.getCoordList,
                          location_b.getCoordList).meters)
    distance_seconds = int(distance_meters)/1.4
    # 1.4m/s is the average walking speed of a human
    return [distance_meters, distance_seconds]

def getFirstRoute(frm, to):
    ''' Returns first available route. '''
    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) > 0:
        return routes[0]
    print 'No route found!'

def getRoutes(frm, to):
    ''' Returns all available routes. '''
    routes = imhdsk.routes(frm, to, time='', date='')
    if len(routes) > 0:
        return routes
    print 'No routes found!'

def getStopLocation(name):
    ''' Returns latitude and longitude of bus stop called <name>. '''
    lines = STOPS.readlines()
    for i in range(0, len(lines)):
        if lines[i].strip() == name:
            coords = lines[i+1].strip().split(',')
            return Location(coords[0], coords[1])
            

def getNearestStop(location):
    ''' Returns nearest stop to the provided location. '''
    # for stop in STOPS:


getStopLocation('Aupark')
"""
class Spoj(imhdsk.Drive):

    FORMAT = 'Line {0} leaving {1} from {2} arriving {3} at {4}.'

    def __init(self, Drive):
        self.Drive = Drive

    def __repr__(self):
        return self.Drive.start + self.Drive.dest
"""
