import ast
import pprint
import re
import logging
import json
import requests
import urllib
from datetime import datetime

#from mediameter.cliff import Cliff

class PhoenixConverter:

    def __init__(self, geo_ip="localhost", geo_port="8080"):
        phoenix_data = json.load(open("phoenix_data.json","r"))

        self.goldstein_scale = phoenix_data.get("goldstein_score")
        self.quad_conversion = phoenix_data.get("quad_class")
        self.countries = phoenix_data.get("countries")
        self.root_actors = phoenix_data.get("root_actors")
        self.primary_agent = phoenix_data.get("primary_agents")
        self.geo_ip = geo_ip
        self.geo_port = geo_port
        self.iso_country_code = phoenix_data.get("iso_country_code")

        print self.primary_agent



    def process_cameo(self, event):

        """
        Provides the "root" CAMEO event, a Goldstein value for the full CAMEO code,
        and a quad class value.
        Parameters
        ----------
        event: Tuple.

                (DATE, SOURCE, TARGET, EVENT) format.
        Returns
        -------
        root_code: String.

                    First two digits of a CAMEO code. Single-digit codes have

                    leading zeros, hence the string format rather than
       event_quad: Int.

                        Quad class value for a root CAMEO category.

        goldstein: Float.
                    Goldstein value for the full CAMEO code.
        """

        #Goldstein values pulled from

        #http://eventdata.parusanalytics.com/cameo.dir/CAMEO.SCALE.txt

        root_code = event[:2]

        try:
            event_quad = self.quad_conversion[root_code]
        except KeyError:
            print('Bad event: {}'.format(event))
            event_quad = ''

        try:
            goldstein = self.goldstein_scale[event]
        except KeyError:
            print('\nMissing Goldstein Value: {}'.format(event[3]))
            try:
                goldstein = self.goldstein_scale[root_code]
            except KeyError:
                print('Bad event: {}'.format(event))
                goldstein = ''
        return root_code, event_quad, goldstein


    def process_actors(self, event):
        """
        Splits out the actor codes into separate fields to enable easier
        querying/formatting of the data.
        Parameters
        ----------
        event: Tuple.

                (DATE, SOURCE, TARGET, EVENT) format.
        Returns
        -------
        actors: Tuple.
                Tuple containing actor information. Format is
                (source, source_root, source_agent, source_others, target,
                target_root, target_agent, target_others). Root is either
                a country code or one of IGO, NGO, IMG, or MNC. Agent is
                one of GOV, MIL, REB, OPP, PTY, COP, JUD, SPY, MED, EDU, BUS, CRM,
                or CVL. The ``others`` contains all other actor or agent codes.
        """


        sauce = event
        if sauce[:3] in self.countries or sauce[:3] in self.root_actors:
            sauce_root = sauce[:3]
        else:
            sauce_root = ''

        if sauce[3:6] in self.primary_agent:
            sauce_agent = sauce[3:6]
        else:
            sauce_agent = ''
        sauce_others = ''

        if len(sauce) > 3:
            if sauce_agent:
                start = 6
                length = len(sauce[6:])
            else:
                start = 3
                length = len(sauce[3:])

            for i in range(start, start + length, 3):
                sauce_others += sauce[i:i + 3] + ';'

            sauce_others = sauce_others[:-1]

        actors = (sauce, sauce_root, sauce_agent, sauce_others)
        return actors

    def geoLocation(self, host, port, text):
        logger = logging.getLogger('pipeline_log')
        locationDetails = {'lat': '', 'lon': '', 'placeName': '', 'countryCode': '', 'stateName': '', 'restype' : ''}

        request_url = "http://{}:{}/CLIFF-2.3.0/parse/text?q={}".format(self.geo_ip, self.geo_port, urllib.quote_plus(text.encode('utf8')))


        cliffDict = requests.get(request_url).json()
        #print cliffDict
        try:
            focus = cliffDict['results']['places']['focus']
        except:
            print "ISSUE"
            return locationDetails

        if not focus:
            return locationDetails

        if len(focus['cities']) >= 1:
            try:
                lat = focus['cities'][0]['lat']
                lon = focus['cities'][0]['lon']
                placeName = focus['cities'][0]['name']
                countryCode = focus['cities'][0]['countryCode']
                stateCode = focus['cities'][0]['stateCode']
                stateDetails = focus['states']
                for deet in stateDetails:
                    if deet['stateCode'] == stateCode:
                        stateName = deet['name']
                    else:
                        stateName = ''

                locationDetails = {'lat': lat, 'lon': lon, 'placeName': placeName, 'restype': 'city', 'countryCode': countryCode, 'stateName': stateName}
                return locationDetails
            except Exception, e:
                print str(e)
                return locationDetails
        elif (len(focus['states']) > 0) & (len(focus['cities']) == 0):
            try:
                lat = focus['states'][0]['lat']
                lon = focus['states'][0]['lon']
                stateName = focus['states'][0]['name']
                countryCode = focus['states'][0]['countryCode']
                locationDetails = {'lat': lat, 'lon': lon, 'placeName': '', 'restype': 'state', 'countryCode': countryCode, 'stateName': stateName}
                return locationDetails
            except:
                return locationDetails
        elif (len(focus['cities']) == 0) & (len(focus['states']) == 0):
            try:
                lat = focus['countries'][0]['lat']
                lon = focus['countries'][0]['lon']
                countryCode = focus['countries'][0]['countryCode']
                placeName = focus['countries'][0]['name']
                locationDetails = {'lat': lat, 'lon': lon, 'placeName': placeName, 'restype': 'country', 'countryCode': countryCode, 'stateName': ''}
                return locationDetails
            except:
                return locationDetails

    def format(self, event_dict, additional_info={}):
        petrarch = event_dict
        dateId = petrarch.keys()
        date8 = re.findall('[0-9]+', dateId[0])[0]
        sents = petrarch[dateId[0]]['sents']

        phoenixDict = dict()
        phoenixDict["code"] = None
        phoenixDict["root_code"] = None
        phoenixDict["quad_class"] = None
        phoenixDict["goldstein"] = None
        phoenixDict["source"] = None
        phoenixDict["target"] = None
        phoenixDict["src_actor"] = None
        phoenixDict["tgt_actor"] = None
        phoenixDict["src_agent"] = None
        phoenixDict["tgt_agent"] = None
        phoenixDict["src_other_agent"] = None
        phoenixDict["tgt_other_agent"] = None

        phoenixDict["date8"] = date8
        try:
            phoenixDict["date8_val"] = datetime.strptime(date8, "%Y%m%d")
        except:
            phoenixDict["date8_val"] = None
        phoenixDict["year"] = date8[0:4]
        phoenixDict["month"] = date8[4:6]
        phoenixDict["day"] = date8[6:]
        phoenixDict["source_text"] = additional_info.get("source", "")
        phoenixDict["url"] = additional_info.get("url", "")

        events = []

        if (sents != None):
            for s in sents:
                info = sents[s]
                if "meta" in info.keys():
                    meta = info["meta"]
                    phoenixDict = {}
                    if (len(meta['actorroot'].keys()) > 0):
                        phoenixDict["code"] = meta['actorroot'].keys()[0][2]
                        phoenixDict["root_code"], phoenixDict["quad_class"], phoenixDict["goldstein"] = self.process_cameo(
                            phoenixDict["code"])
                        phoenixDict["source"], phoenixDict["src_actor"], phoenixDict["src_agent"], phoenixDict[
                            "src_other_agent"] = self.process_actors(meta['actorroot'].keys()[0][0])
                        phoenixDict["target"], phoenixDict["tgt_actor"], phoenixDict["tgt_agent"], phoenixDict[
                            "tgt_other_agent"] = self.process_actors(meta['actorroot'].keys()[0][1])
                    geoDict = self.geoLocation(self.geo_ip, self.geo_port, info['content'])
                    phoenixDict['latitude'] = geoDict['lat']
                    phoenixDict['longitude'] = geoDict['lon']
                    phoenixDict['country_code'] = self.iso_country_code.get(geoDict['countryCode'],geoDict['countryCode'])
                    phoenixDict['geoname'] = geoDict['placeName'] + ' ' + geoDict['stateName']
                    phoenixDict['id'] = additional_info.get("mongo_id","")+"_"+str(s)
                    phoenixDict["date8"] = date8
                    try:
                        phoenixDict["date8_val"] = datetime.strptime(date8, "%Y%m%d")
                    except:
                        phoenixDict["date8_val"] = None
                    phoenixDict["year"] = date8[0:4]
                    phoenixDict["month"] = date8[4:6]
                    phoenixDict["day"] = date8[6:]
                    phoenixDict["source_text"] = additional_info.get("source", "")
                    phoenixDict["url"] = additional_info.get("url", "")
                    events.append(phoenixDict)
        return events

# sourceFile = "/Volumes/Untitled 2/Users/sayeed/July_Dataset/20170704.json"
# destinationFile = "test_phoenix.txt"
# # geoUrl = raw_input("Enter the url to access Clavin Cliff server: ")
# # geoPort = raw_input("Enter the port number to access Clavin Cliff server: ")
#
# fhand = open(sourceFile)
# fhand2 = open(destinationFile, 'w+')
# formatter = PhoenixConverter(geo_ip="149.165.168.205")
# count = 0
# for line in fhand:
#     line = ast.literal_eval(line)
#
#     petrarch = ast.literal_eval(line["petrarch"])
#
#     events = formatter.format(petrarch)
#
#     print len(events)
#
#     print events