from kafka import KafkaConsumer
from kafka import KafkaProducer
from petrarch2 import EventCoder
from pymongo import MongoClient
from petrarch2 import PETRwriter
import urllib
import json
from bson import ObjectId
from PhoenixConverter import PhoenixConverter
from kafka.client import SimpleClient
from kafka.producer.simple import SimpleProducer


MONGO_PORT="3154"
MONGO_USER="event_reader"
MONGO_PSWD="dml2016"
MONGO_SERVER_IP="172.29.100.8"
MONGO_PORT="3154"

MONGO_COLLECTION = "processed_stories"
password = urllib.quote_plus(MONGO_PSWD)
client = MongoClient('mongodb://'+MONGO_USER+':' + password + '@'+MONGO_SERVER_IP+":"+MONGO_PORT)

db = client.event_scrape

consumer = KafkaConsumer('petrarch',bootstrap_servers='172.29.100.6:9092')

formatter = PhoenixConverter(geo_ip="149.165.168.205", geo_port="8080")



coder = EventCoder()

def get_info_from_mongo(id_str):
    object_id = ObjectId(id_str)
    article = db.stories.find_one({"_id": object_id})

    if article is not None:
        return article['source'], article['url']
    else:
        return None, None


for msg in consumer:
    #print msg
    try:
        event_dict = coder.encode(msg.value)

        # formatted_dict = PETRwriter.pipe_output(event_dict)

        db_value = {}
        db_value['corenlp'] = json.loads(msg.value)
        str_id = db_value['corenlp']['mongo_id']
        source, url = get_info_from_mongo(str_id)

        additional_info = {"source": source, "url": url, "mongo_id": str_id}

        events = formatter.format(event_dict, additional_info)

        print "Number of events ", str(len(events))

        db_value['petrarch'] = str(event_dict)

        db.processed_stories.insert(db_value, check_keys=False)

        for event in events:
            print "========"
            print event
            db.phoenix_events.insert(event, check_keys=False)

    except Exception, e:
        issue_article = {}
        issue_article['article'] = msg.value
        issue_article['issue'] = str(e)

        db.issue_for_stories.insert(issue_article, check_keys=False)

