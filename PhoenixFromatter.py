from kafka import KafkaConsumer
from petrarch2 import EventCoder
from pymongo import MongoClient
from petrarch2 import PETRwriter
import urllib
import ast
import json
import result_formatter
import postprocess
import datetime
import utilities

MONGO_PORT = "3154"
MONGO_USER = "event_reader"
MONGO_PSWD = "dml2016"
MONGO_SERVER_IP = "172.29.100.14"
MONGO_PORT = "3154"

MONGO_COLLECTION = "processed_stories"
password = urllib.quote_plus(MONGO_PSWD)
client = MongoClient('mongodb://' + MONGO_USER + ':' + password + '@' + MONGO_SERVER_IP + ":" + MONGO_PORT)

db = client.event_scrape

process_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
date_string = '{:02d}{:02d}{:02d}'.format(process_date.year,
                                                  process_date.month,
                                                  process_date.day)
server_details, geo_details, file_details, petrarch_version = utilities.parse_config('PHOX_config.ini')


geo_details._replace(geo_service)

for story in db.processed_stories.find():
    if "petrarch" in story:
        try:
            event_dict = ast.literal_eval(story["petrarch"])
            #print event_dict
            new_dict = PETRwriter.pipe_output(event_dict)
            formatted_dict = result_formatter.main(new_dict)

            event_write = postprocess.main(formatted_dict, date_string, "v0.0.0", file_details, server_details, geo_details)
            print event_write
        except Exception, e:
            print str(e)
            continue