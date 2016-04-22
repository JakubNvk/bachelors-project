#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import imhdsk
import unicodedata
from mhd import all_stops, all_stops_rev, trams, busses
from mapbox import Directions
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.distance import vincenty


MAPBOX = Directions()

def normalize(stop):
    ''' Removes special characters from given stop.

        stop - string
    '''

    stop = unicodedata.normalize('NFKD', stop)
    normalized = ''

    for letter in stop:
        if not unicodedata.combining(letter):
            normalized += letter
    return normalized

def get_coordinates(address):
    ''' Returns set of coordinates for given address.

        address - string
    '''

    location = Nominatim(timeout=10).geocode(address)
    return (location.latitude, location.longitude)

def get_address(location):
    ''' Returns adress for given set of coordinates.

        location - coordinates set
    '''

    location = Nominatim(timeout=10).reverse(location)
    return location.address

def get_distance_meters(location_a, location_b):
    ''' Returns distance in meters between given points.

        location_a - coordinates set
        location_b - coordinates set
    '''

    distance_meters = int(vincenty(location_a,
                                   location_b).meters)
    return distance_meters

def get_distance_seconds(location_a, location_b):
    ''' Returns distance in seconds between given points.

        location_a - coordinates set
        location_b - coordinates set
    '''

    distance_meters = get_distance_meters(location_a, location_b)
    # 1.4m/s is the average walking speed of a human
    distance_seconds = int(distance_meters)/1.4
    return distance_seconds

def get_midpoint(coord_list):
    ''' Returns middle point from coordinates in given coordinates list.

        coord_list - list of coordinates
    '''

    lats, longs = 0, 0
    for coord_set in coord_list:
        lat, lon = coord_set
        lats += lat
        longs += lon
    midpoint = (lats/len(coord_list), longs/len(coord_list))
    return midpoint

def get_nearest_stop(location):
    # add: second neareset and rename to find nearest stopS
    ''' Returns nearest stop to the provided location.

        location - coordinates set
    '''

    stops = {}
    for name, coord_list in all_stops.items():
        midpoint = get_midpoint(coord_list)
        distance = get_distance_meters(location, midpoint)
        stops.update({name: distance})

    nearest = min(stops.values())
    for name, distance in stops.items():
        if distance == nearest:
            return name

def get_stop_location(name, line_type=None):
    ''' Returns latitude and longitude of tram stop called <name>.

        name - string
    '''

    if line_type == 'tram':
        stop_location = get_midpoint(trams[name])
        return stop_location

    if line_type == 'bus' or line_type == 'tbus':
        stop_location = get_midpoint(busses[name])
        return stop_location

    if name in all_stops:
        stop_location = get_midpoint(all_stops[name])
        return stop_location

    return None
    print('Stop is not in database.')

def get_stop_name(lat_long):
    ''' Returns name of tram stop with <lat> and <long> coordinates.

        lat_long - coordinates set
    '''
    
    for k, v in all_stops_rev.items():
        if lat_long in k:
            return v
    print('Stop with given latitude and longitude is not in database.')

def get_mhd(frm, to):
    ''' Returns all available routes.

        frm - coordinates set
        to - coordinates set
        walking_delta - integer
    '''

    if frm == to:
        print('Location from and to are the same.')
        return None

    stop_frm = get_nearest_stop(frm)
    stop_to = get_nearest_stop(to)

    walking_delta = get_distance_seconds(frm, get_stop_location(stop_frm))
    now = datetime.now()
    time = now + timedelta(seconds=walking_delta)
    time = time.strftime("%H:%M")

    routes = imhdsk.routes(normalize(stop_frm), normalize(stop_to), time=time,
                                                                    date='')
    if len(routes) == 0:
        print('No routes found!')
        return None
    return routes

def check_prefered_way(frm, to):
    ''' Checks if prefered way of transportation is walking or bus/tram.
        If travel time between frm and to is less than 15 minutes, the prefered
        way will automatically be walking.

        frm - coordinates set
        to - coordinates set

        Returns:
            True - prefered way is to walk
            False - prefered way is to use the bus/tram
    '''

    walk = get_distance_seconds(frm, to)
    walk = int(walk/60)
    if walk <= 15:
        return True

    bus = 0
    routes = get_mhd(frm, to)
    drives = routes[0].drives
    for drive in drives:
        bus += int(drive.length.strip(' min'))
    
    if walk < bus:
        return True
    return False

def identify_line(line):
    ''' TODO

        line - string
    '''

    tram = ['1', '2', '3', '4', '5', '6', '8', '9']
    tbus = ['33', '64', '201', '202', '203', '204', '205', '206', '207', '208',
            '209', '210', '211', '212']
    bus = ['20', '21', '23', '24', '25', '26', '27', '28', '29', '30', '31',
           '32', '35', '37', '39', '41', '43', '44', '50', '51', '52', '53',
           '54', '56', '57', '58', '59', '61', '63', '65', '66', '67', '68',
           '69', '70', '74', '75', '77', '78', '79', '80', '82', '83', '84',
           '87', '88', '90', '91', '92', '93', '94', '95', '96', '98', '99',
           '123', '130', '131', '133', '139', '141', '147', '151', '153', '184',
           '191', '192', '196', 'X13', 'N21', 'N29', 'N31', 'N33', 'N34', 'N37',
           'N44', 'N47', 'N53', 'N55', 'N56', 'N61', 'N70', 'N72', 'N74', 'N80',
           'N91', 'N93', 'N95', 'N99']
    
    if line is not None:
        line = line.strip('[]')
    
    if line in tram:
        return 'tram'
    if line in tbus:
        return 'tbus'
    if line in bus:
        return 'bus'

def find(start, dest):
    ''' TODO

        frm - coordinates set
        to - coordinates set
    '''

    frm = get_coordinates(start)
    to = get_coordinates(dest)
    walk_or_bus = check_prefered_way(frm, to)
    routes = []

    if walk_or_bus:
        route = imhdsk.Route()
        drive = imhdsk.Drive()

        drive.start = frm
        drive.start_c = start
        drive.dest = to
        drive.dest_c = dest
        drive.length = int(get_distance_seconds(frm, to)/60)
        drive.walk = True
        drive.bus = False
        drive.tbus = False
        drive.tram = False
        route.drives.append(drive)
        routes.append(route)

        return routes

    r = get_mhd(frm, to)

    for rt in r:
        i = 0
        d = rt.drives
        route = imhdsk.Route()

        # First drive from point A to nearest stop (B_1).
        to_stop = imhdsk.Drive()
        line_type = identify_line(r[0].drives[0].line)
        to_stop.start = start
        to_stop.start_c = frm
        to_stop.dest = r[0].drives[0].start
        to_stop.dest_c = get_stop_location(to_stop.dest, line_type)
        to_stop.length = int(get_distance_seconds(frm, to_stop.dest_c)/60)
        to_stop.walk = True
        to_stop.bus = False
        to_stop.tbus = False
        to_stop.tram = False
        route.drives.append(to_stop)

        # Drives from/to stops/points (B_1, B_2, ..., B_n).
        for drv in d:
            line_type = identify_line(drv.line)
            if drv.walk:
                drv.start_c = d[i-1].dest_c
                drv.dest_c = get_stop_location(d[i+1].start,
                                               identify_line(d[i+1].line))
                drv.bus = False
                drv.tbus = False
                drv.tram = False
                continue

            drv.start_c = get_stop_location(drv.start, line_type)
            drv.dest_c = get_stop_location(drv.dest, line_type)

            if line_type == 'bus':
                drv.bus = True
            else:
                drv.bus = False

            if line_type == 'tbus':
                drv.tbus = True
            else:
                drv.tbus = False

            if line_type == 'tram':
                drv.tram = True
            else:
                drv.tram = False

            i += 1
            route.drives.append(drv)

        # Last drive from last stop (B_n) to point B.
        from_stop = imhdsk.Drive()
        line_type = identify_line(r[-1].drives[-1].line)
        from_stop.start = r[-1].drives[-1].dest
        from_stop.start_c = get_stop_location(from_stop.start, line_type)
        from_stop.dest = dest
        from_stop.dest_c = to
        from_stop.length = int(get_distance_seconds(from_stop.start_c, to)/60)
        from_stop.walk = True
        from_stop.bus = False
        from_stop.tbus = False
        from_stop.tram = False
        route.drives.append(from_stop)

        routes.append(route)

    return routes
