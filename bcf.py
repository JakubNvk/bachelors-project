#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import json
import imhdsk
import unicodedata
from mhd import all_stops, all_stops_rev, trams, busses
from mapbox import Distance
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.distance import vincenty

import functools
import time

MAPBOX_TOKEN = 'pk.eyJ1IjoiamFrdWJudmsiLCJhIjoiY2lsOGV4eTkxMDAybXZ5a3F0ZXNyNnR3cSJ9.5y6GM1S5wsDJl-urjVxYcw'  # noqa


def timeit(func):
    """Profiling function to measure time it takes to finish function."""
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        start_time = time.time()
        out = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        msg = 'function [{}] finished in {} ms'
        print(msg.format(func.__name__, int(elapsed_time * 1000)))
        return out
    return newfunc


def normalize(stop):
    """
    Remove special characters from given stop.

    stop - string
    """
    stop = unicodedata.normalize('NFKD', stop)
    normalized = ''

    for letter in stop:
        if not unicodedata.combining(letter):
            normalized += letter
    return normalized


def get_coordinates(address):
    """
    Return set of coordinates for given address.

    address - string
    """
    city = 'Bratislava'
    location = Nominatim(timeout=10).geocode('{0}, {1}'.format(address, city))
    if location is None:
        return None
    return (location.latitude, location.longitude)


def get_address(location):
    """
    Return adress for given set of coordinates.

    location - coordinates set
    """
    location = Nominatim(timeout=10).reverse(location)
    return location.address


def get_distance_meters(location_a, location_b):
    """
    Return distance in meters between given points.

    location_a - coordinates set
    location_b - coordinates set
    """
    distance_seconds = get_distance_seconds(location_a, location_b)
    # 1.7 m/s is the average walking speed of a human
    distance_meters = int(distance_seconds * 1.7)
    return distance_meters


def get_distance_seconds(location_a, location_b):
    """
    Return distance in seconds between given points.

    location_a - coordinates set
    location_b - coordinates set
    """
    global MAPBOX_TOKEN
    distance_service = Distance(access_token=MAPBOX_TOKEN)
    # Mapbox takes coordinates in reverse order, thats why I use [::-1].
    loc_a = {'type': 'Feature',
             'geometry': {'type': 'Point',
                          'coordinates': location_a[::-1]}}

    loc_b = {'type': 'Feature',
             'geometry': {'type': 'Point',
                          'coordinates': location_b[::-1]}}

    response = distance_service.distances([loc_a, loc_b], 'walking')
    # response.text is a json in {"code":"Ok", "durations":[[0,2650],[2650,0]]}
    # format. 'durations' is a matrix of distances in seconds between each two
    # points, therefore when I use two points, I only need one list. In my list
    # the first item will always be 0 (distance from A to A), therefore I only
    # need the second item from the list (distance from A to B).
    distance_seconds = json.loads(response.text)['durations'][0][1]
    return distance_seconds


def get_midpoint(coord_list):
    """
    Return middle point from coordinates in given coordinates list.

    coord_list - list of coordinates
    """
    lats, longs = 0, 0
    for coord_set in coord_list:
        lat, lon = coord_set
        lats += lat
        longs += lon
    midpoint = (lats / len(coord_list), longs / len(coord_list))
    return midpoint


def get_nearest_stop(location):
    """
    Return nearest stop to the provided location.

    location - coordinates set
    """
    stops = {}
    for name, coord_list in all_stops.items():
        midpoint = get_midpoint(coord_list)
        distance_meters = int(vincenty(location, midpoint).meters)
        # 800 meters is about 10 minutes of walking.
        if distance_meters < 800:
            distance = get_distance_meters(location, midpoint)
            stops.update({name: distance})

    if len(stops) == 0:
        for name, coord_list in all_stops.items():
            midpoint = get_midpoint(coord_list)
            distance = get_distance_meters(location, midpoint)
            stops.update({name: distance})

    nearest = min(stops.values())
    for name, distance in stops.items():
        if distance == nearest:
            nearest_name = name
    del stops[nearest_name]
    return nearest_name


def get_stop_location(name, line_type=None):
    """
    Return latitude and longitude of tram stop called <name>.

    name - string
    """
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
    """
    Return name of tram stop with <lat> and <long> coordinates.

    lat_long - coordinates set
    """
    for k, v in all_stops_rev.items():
        if lat_long in k:
            return v
    print('Stop with given latitude and longitude is not in database.')


def get_mhd(frm, to):
    """
    Return all available routes.

    frm - coordinates set
    to - coordinates set
    walking_delta - integer
    """
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
    """
    Check if prefered way of transportation is walking or bus/tram.

    If travel time between frm and to is less than 15 minutes, the prefered
    way will automatically be walking.

    frm - coordinates set
    to - coordinates set

    Returns:
        True - prefered way is to walk
        False - prefered way is to use the bus/tram
    """
    walk = get_distance_seconds(frm, to)
    walk = int(walk / 60)
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
    """
    Identify whether the line is bus, trolleybus or tram.

    line - string
    """
    tram = ['1', '2', '3', '4', '5', '6', '8', '9']
    tbus = ['33', '64', '201', '202', '203', '204', '205', '206', '207', '208',
            '209', '210', '211', '212']
    bus = ['20', '21', '23', '24', '25', '26', '27', '28', '29', '30', '31',
           '32', '35', '37', '39', '41', '43', '44', '50', '51', '52', '53',
           '54', '56', '57', '58', '59', '61', '63', '65', '66', '67', '68',
           '69', '70', '74', '75', '77', '78', '79', '80', '82', '83', '84',
           '87', '88', '90', '91', '92', '93', '94', '95', '96', '98', '99',
           '123', '130', '131', '133', '139', '141', '147', '151', '153',
           '184', '191', '192', '196', 'X13', 'X31', 'N21', 'N29', 'N31',
           'N33', 'N34', 'N37', 'N44', 'N47', 'N53', 'N55', 'N56', 'N61',
           'N70', 'N72', 'N74', 'N80', 'N91', 'N93', 'N95', 'N99']

    if line is not None:
        line = line.strip('[]')

    if line in tram:
        return 'tram'
    if line in tbus:
        return 'tbus'
    if line in bus:
        return 'bus'


def format_instr(routes):
    """Format route instructions."""
    for route in routes:
        for drive in route.drives:
            if drive.walk:
                instr = ''
            instr += '{}\n\n'.format(drive.instr)
    return routes


@timeit
def find(start, dest):
    """
    Find routes from starting point to destination point.

    Creates a list of Route objects which contain Drive objects with
    information about length,start, destination, coordinates, line number and
    the type of line.

    frm - coordinates set
    to - coordinates set
    """
    frm = get_coordinates(start)
    to = get_coordinates(dest)
    walk_or_bus = check_prefered_way(frm, to)
    routes = []
    walkinstr = 'Presunte sa z {0} na {1}.'
    driveinstr = ('Na {0} zastávke {1} nastúpte na spoj číslo {2}, smer {3}.!'
                  'Vystúpte na zastávke {4}.')

    if walk_or_bus:
        route = imhdsk.Route()
        drive = imhdsk.Drive()

        drive.start = frm
        drive.start_c = list(start)
        drive.dest = to
        drive.dest_c = list(dest)
        d_len = get_distance_seconds(frm, to)
        drive.length = '{} min'.format(int(d_len / 60))
        drive.dist = int(d_len * 1.7)
        drive.walk = True
        drive.bus = False
        drive.tbus = False
        drive.tram = False
        drive.instr = walkinstr.format(frm, to)
        route.drives.append(drive)
        routes.append(route)

        return routes

    r = get_mhd(frm, to)
    if r is None:
        print('get_mhd() returned no results.')
        return None

    for rt in r:
        i = 0
        d = rt.drives
        route = imhdsk.Route()
        route.drives = []

        # First drive from point A to nearest stop (B_1).
        to_stop = imhdsk.Drive()
        line_type = identify_line(r[0].drives[0].line)
        to_stop.start = start
        to_stop.start_c = list(frm)
        to_stop.dest = r[0].drives[0].start
        to_stop.dest_c = list(get_stop_location(to_stop.dest, line_type))
        to_stop.midpoint = list(get_midpoint([to_stop.start_c,
                                              to_stop.dest_c]))
        to_len = get_distance_seconds(frm, to_stop.dest_c)
        if to_len == 0:
            # Minimum value for walk from point A to stop.
            to_len = 1
        to_stop.length = '{} min'.format(int(to_len / 60))
        to_stop.dist = int(to_len * 1.7)
        to_stop.walk = True
        to_stop.bus = False
        to_stop.tbus = False
        to_stop.tram = False
        to_stop.instr = walkinstr.format(to_stop.start, to_stop.dest)
        route.drives.append(to_stop)

        # Drives from/to stops/points (B_1, B_2, ..., B_n).
        j = 0
        for drv in d:
            line_type = identify_line(drv.line)
            if drv.walk:
                if j == 0:
                    continue
                drv.start_c = d[i - 1].dest_c
                drv.dest_c = get_stop_location(d[i + 1].start,
                                               identify_line(d[i + 1].line))
                drv.midpoint = list(get_midpoint([drv.start_c, drv.dest_c]))
                drv_len = int(drv.length.strip(' min'))
                drv.dist = int(drv_len * 60 * 1.7)
                drv.bus = False
                drv.tbus = False
                drv.tram = False
                drv.instr = walkinstr.format(drv.start, drv.dest)
                continue

            drv.start_c = list(get_stop_location(drv.start, line_type))
            drv.dest_c = list(get_stop_location(drv.dest, line_type))

            if line_type == 'bus':
                drv.bus = True
                drv.instr = driveinstr.format('autobusovej', drv.start,
                                              drv.line.strip('[]'), drv.dest,
                                              drv.dest)
            else:
                drv.bus = False

            if line_type == 'tbus':
                drv.tbus = True
                drv.instr = driveinstr.format('trolejbusovej', drv.start,
                                              drv.line.strip('[]'), drv.dest,
                                              drv.dest)
            else:
                drv.tbus = False

            if line_type == 'tram':
                drv.tram = True
                drv.instr = driveinstr.format('električkovej', drv.start,
                                              drv.line.strip('[]'), drv.dest,
                                              drv.dest)
            else:
                drv.tram = False

            i += 1
            route.drives.append(drv)
        # Last drive from last stop (B_n) to point B.
        from_stop = imhdsk.Drive()
        line_type = identify_line(r[-1].drives[-1].line)
        from_stop.start = r[-1].drives[-1].dest
        from_stop.start_c = list(get_stop_location(from_stop.start, line_type))
        from_stop.dest = dest
        from_stop.dest_c = list(to)
        from_stop.midpoint = list(get_midpoint([from_stop.start_c,
                                                from_stop.dest_c]))
        from_len = get_distance_seconds(from_stop.start_c, to)
        if from_len == 0:
            # Minimum value for walk from stop to point B.
            from_len = 1
        from_stop.length = '{} min'.format(int(from_len / 60))
        from_stop.dist = int(from_len * 1.7)
        from_stop.walk = True
        from_stop.bus = False
        from_stop.tbus = False
        from_stop.tram = False
        from_stop.instr = walkinstr.format(from_stop.start, from_stop.dest)
        route.drives.append(from_stop)

        routes.append(route)

    return routes
