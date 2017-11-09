# from EventCoder import EventCoder
#
#
# coder = EventCoder()
#
# input_file = open("test_article_173_2.json","r")
#
# content = input_file.read()
#
# print content
#
# print coder.encode(content)
from datetime import datetime, timedelta
from pymongo import MongoClient

def get_mongo_connection():
    MONGO_SERVER_IP="172.29.100.14"
    MONGO_PORT="3154"
    MONGO_USER="event_reader"
    MONGO_PSWD="dml2016"


    #password = urllib.quote_plus(MONGO_PSWD)
    return MongoClient('mongodb://'+MONGO_USER+':' + MONGO_PSWD + '@'+MONGO_SERVER_IP+":"+MONGO_PORT)

def get_daily_data(date):
    mongoClient = get_mongo_connection()
    database = mongoClient.event_scrape

    end_date = date.replace(hour=0,minute=0,second=0, microsecond=0)
    start_date = end_date - timedelta(days=1)

    cursor = database.stories.find({"date_added":{"$gte": start_date, "$lt": end_date}})
    list_ids = []
    for entry in cursor:
        list_ids.append(str(entry["_id"]))

    print len(list_ids)

    cursor = database.processed_stories.find({"corenlp.mongo_id": {"$in": list_ids}},{"corenlp": 1})

    story_list = []

    for entry in cursor:
        story_list.append(entry["corenlp"])

    print len(story_list)
    return story_list




time_now = datetime.now()

new_Time = time_now.replace(hour=0,minute=0,second=0, microsecond=0)


print time_now

print new_Time - timedelta(days=1)

get_daily_data(datetime.now()-timedelta(days=1))