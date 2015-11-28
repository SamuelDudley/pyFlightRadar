__author__ = 'danmir'
import requests
import json
import time
from pymavlink import mavutil, mavextra




class FlightRadarAPI():

    def __init__(self):
        self.load_balancer_link = 'http://www.flightradar24.com/balance.json'
        self.server_data_link = self.choose_server()
        self.last_request_time = time.time()

    def parce_json(self, link):
        try:
            data = requests.get(link)
        except requests.exceptions.ConnectionError:
            print("Network problems")
            return
        except requests.exceptions.HTTPError:
            print("HTTP responce error")
            return
        except requests.exceptions.Timeout:
            print("Timeout")
            return
        # print(data)
        return data.json()

    def choose_server(self):
        server_data_link = None
        load_balancer = self.parce_json(self.load_balancer_link)
        server_data_link_num = sorted(load_balancer.values())[0]
        #try to find the requested server for use
        for key in load_balancer:
            if load_balancer[key] == server_data_link_num:
                return key
        return -1 #pick the last server
    
    def get_aircraft_near_location(self, lat, lon, distance):
        (lat_ne,lng_ne) = mavextra.gps_offset(lat, lon, distance, distance)
        (lat_sw,lng_sw) = mavextra.gps_offset(lat, lon, -distance, -distance)
        return self.get_aircraft_by_bounds(lat_ne, lat_sw, lng_sw, lng_ne)

    def get_aircraft_by_bounds(self, lat_ne, lat_sw, lng_sw, lng_ne, **kwargs):
        """
        Get all aircraft given bounds
        Filter information in addition:
            "filter_type" = ["from_iata" | "to_iata"]
            "iata" = [iata]
        :param lat_ne:
        :param lat_sw:
        :param lng_sw:
        :param lng_ne:
        :return: list
        """
        # Expand zone a little
        lat_ne = int(lat_ne) + 1
        lat_sw = int(lat_sw) - 1
        lng_ne = int(lng_ne) + 1
        lng_sw = int(lng_sw) - 1
       
        
        zone_link = "http://{}/zones/fcgi/feed.js?bounds={},{},{},{}&adsb=1&mlat=1&flarm=1&faa=1&estimated=1&air=1&gnd=1&vehicles=1&gliders=1&array=1".format(self.server_data_link, lat_ne, lat_sw, lng_sw, lng_ne)
        # print(zone_link)
        info = self.parce_json(zone_link)
        # print(info)
        if not len(kwargs):
            return info["aircraft"]
        elif kwargs["filter_type"] and kwargs["iata"]:
            ans = []
            if kwargs["filter_type"] == "from_iata":
                for plane in info["aircraft"]:
                    if plane[12] == kwargs["iata"]:
                        ans.append(plane)
            elif kwargs["filter_type"] == "to_iata":
                for plane in info["aircraft"]:
                    if plane[13] == kwargs["iata"]:
                        ans.append(plane)
            return ans
        else:
            print("Wrong filter parameters. Nothing filtered")
            return info["aircraft"]

def format_aircraft_data(aircrafts):
    
    for aircraft in aircrafts:
        print aircraft
        unsure = aircraft[0] #hash for that flight?
        ICAO_address = aircraft[1] #hex reg, unique
        lat = aircraft[2]*1e7
        lon = aircraft[3]*1e7
        heading = aircraft[4]
        altitude = aircraft[5]*0.3048 #ft to m
        hor_velocity = aircraft[6]*0.514444 #knots to m/s
        squawk = aircraft[7]
        id_radar = aircraft[8] #id picking up the plane, where data comes from
        aircraft_type = aircraft[9]
        callsign = str(aircraft[10]) #unique reg (not hex)
        data_get_time = aircraft[11] #utc?
        takeoff_airport = aircraft[12]
        dest_airport = aircraft[13]
        flight_name_takeoff = aircraft[14]
        on_ground_flag = aircraft[15] #0 = air, 1 = ground
        ver_velocity=aircraft[16]*0.00508 #fpm to m/s
        flight_name_dest = aircraft[17]
        unsure = aircraft[18]
    print ""

if __name__ == "__main__":
    
    import time
    airspace_size = (500000,50000)  #(north to south, east to west)m
    poll_time = 0.5#sec
    
    flapi = FlightRadarAPI()
    print(flapi.server_data_link)
    while True:
        if time.time() - flapi.last_request_time > poll_time:
            rep = flapi.get_aircraft_near_location(lat=-34.92, lon=138.52, distance=max(airspace_size))
            format_aircraft_data(rep)
            flapi.last_request_time = time.time()
        time.sleep(0.1)