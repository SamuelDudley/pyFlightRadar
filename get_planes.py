__author__ = 'danmir'
import requests
import json
from pymavlink import mavutil


def linear_dict_search(inp_dict, input_value):
    for key in inp_dict:
        if inp_dict[key] == input_value:
            return key
    return -1


class FlightRadarAPI():

    def __init__(self):
        self.load_balancer_link = 'http://www.flightradar24.com/balance.json'
        self.server_data_link = self.choose_server(self.load_balancer_link)

        self.airports_link = "http://www.flightradar24.com/_json/airports.php"
        self.airports = self.get_airports(self.airports_link)

        self.airlines_link = "http://www.flightradar24.com/_json/airlines.php"
        self.airlines = self.get_airlines(self.airlines_link)

        self.zones_link = "http://www.flightradar24.com/js/zones.js.php"
        self.zones = self.get_zones(self.zones_link)

        self._aircrafts_link = None

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

    def choose_server(self, load_balancer_options):
        load_balancer = self.parce_json(load_balancer_options)
        server_data_link_num = sorted(load_balancer.values())[0]
        server_data_link = linear_dict_search(load_balancer, server_data_link_num)
        return server_data_link

    def get_airports(self, link):
        """
        Return list of all airports. Every airport is a dict
        :param link: link to the airport api
        :return: list
        """
        return self.parce_json(link)["rows"]

    def is_there_airport_with_iata(self, iata):
        airports_dict = self.airports
        for airport in airports_dict:
            if airport["iata"] == iata:
                return True
        return False

    def get_airlines(self, link):
        return self.parce_json(link)

    def get_zones(self, link):
        return self.parce_json(link)

    def get_aircrafts(self):
        """
        Get all aircrafts
        :rtype : dict
        :return: dict with all aircrafts
        """
        return self.get_aircrafts_by_zone("full")

    def get_aircrafts_by_flight_num(self, flight_num):
        all_aircrafts_new_dict = dict()
        all_aircrafts_dict = self.get_aircrafts()
        for flight_id in all_aircrafts_dict:
            if flight_id != "full_count" and flight_id != "version":
                fi = [flight_id, ]
                # print(fi)
                res = all_aircrafts_dict[flight_id] + fi
                # print(res)
                # print(str(all_aircrafts_dict[flight_id][13]))
                all_aircrafts_new_dict[str(all_aircrafts_dict[flight_id][13])] = res
        try:
            return all_aircrafts_new_dict[flight_num]
        except KeyError:
            return "No such flight"

    def get_aircrafts_by_zone(self, zone):
        self._aircrafts_link = "http://{}/zones/fcgi/{}_all.json".format(self.server_data_link, zone)
        return self.parce_json(self._aircrafts_link)

    def get_zone_by_coord(self, lon, lat):
        for zone in self.zones:
            print(zone)
            #TODO make this work?

    def _get_zone(self, zone, start_zone):
        pass

    def get_aircrafts_by_bounds(self, lat_ne, lat_sw, lng_sw, lng_ne, **kwargs):
        """
        Get all aircrafts by given bounds
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
        """
        lat_ne = int(lat_ne) + 1
        lat_sw = int(lat_sw) - 1
        lng_ne = int(lng_ne) + 1
        lng_sw = int(lng_sw) - 1
        """
        lat_ne = int(lat_ne)
        lat_sw = int(lat_sw)
        lng_ne = int(lng_ne)
        lng_sw = int(lng_sw)
        
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

    def get_aircraft_info(self, flight_id):
        aircraft_link = "http://{}/_external/planedata_json.1.4.php?f={}".format(self.server_data_link, flight_id)
        info = self.parce_json(aircraft_link)
        return info

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
    
    """
     <message id="246" name="ADSB_VEHICLE">
          <description>The location and information of an ADSB vehicle</description>
          <field type="uint32_t" name="ICAO_address">ICAO address</field>
          <field type="int32_t" name="lat">Latitude, expressed as degrees * 1E7</field>
          <field type="int32_t" name="lon">Longitude, expressed as degrees * 1E7</field>
          <field type="uint8_t" name="altitude_type" enum="ADSB_ALTITUDE_TYPE">Type from ADSB_ALTITUDE_TYPE enum</field>
          <field type="float" name="altitude">Altitude(ASL) in meters</field>
          <field type="uint16_t" name="heading">Course over ground in centidegrees</field>
          <field type="float" name="hor_velocity">The horizontal velocity in meters/second</field>
          <field type="float" name="ver_velocity">The vertical velocity in meters/second, positive is up</field>
          <field type="char[9]" name="callsign">The callsign, 8+null</field>
          <field type="uint8_t" name="emitter_type" enum="ADSB_EMITTER_TYPE">Type from ADSB_EMITTER_TYPE enum</field>
          <field type="uint8_t" name="tslc">Time since last communication in seconds</field>
          <field type="uint16_t" name="flags" enum="ADSB_FLAGS">Flags to indicate various statuses including valid data fields</field>
        </message>
    """

if __name__ == "__main__":
    
    import time
    flapi = FlightRadarAPI()
    print(flapi.server_data_link)
#     print(flapi.airports)
#     print(flapi.airlines)
#     print(flapi.zones)
#     print(flapi.get_aircrafts_by_zone("atlantic"))
#     print(flapi.get_aircraft_info("50e10b0"))
#

    while True:
        rep = (flapi.get_aircrafts_by_bounds(-29, -40, 128, 143))
        format_aircraft_data(rep)
        
#     print(flapi.get_zone_by_coord(60.599637, 56.834280))
#     print(flapi.get_aircrafts_by_flight_num("SU1501"))
