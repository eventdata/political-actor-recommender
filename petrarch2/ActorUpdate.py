import requests
import ast
import json
import pprint
#from DataAccess import get_mongo_connection

class ActorUpdate:

    def __init__(self):
        self.url = "http://149.165.157.42:3000/upload"
        #.headers = {"secret-key": "mySecretKey", "Content-Type": "application/json"}

    def actorUpload(self, actorName, synonyms, roles):
        actorDictionary = dict()
        actorDictionary[actorName] = dict()
        actorDictionary[actorName]["roles"] = roles
        actorDictionary[actorName]["synonyms"] = synonyms


        r = requests.post(self.url, data=json.dumps(actorDictionary), headers=self.headers)
        if r.status_code == 200:
            # conn = get_mongo_connection()
            # db = conn.event_scrape
            # db.uploaded_actors.insert(actorDictionary)
            # conn.close()
            print "Success"
        return r


# au = ActorUpdate()
# roles = ["DEUGOV", "GOV", "USAGOV", "FRA", "FRAGOV"]
# print au.actorUpload("EMMANUEL_MACRON", roles, [])
