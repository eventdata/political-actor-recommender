import requests
import ast
import json
import pprint

class ActorUpdate:

    def __init__(self):
        self.url = "http://104.198.76.143:8080/dictionary/upload"
        self.headers = {"secret-key": "mySecretKey", "Content-Type": "application/json"}

    def actorUpload(self, actorName, synonyms, roles):
        actorDictionary = dict()
        actorDictionary[actorName] = dict()
        actorDictionary[actorName]["roles"] = roles
        actorDictionary[actorName]["synonyms"] = synonyms
        r = requests.post(self.url, data=json.dumps(actorDictionary), headers=self.headers)

        return r

au = ActorUpdate()
roles = ["DEUGOV", "GOV", "USAGOV", "FRA", "FRAGOV"]
print au.actorUpload("EMMANUEL_MACRON", roles, [])
