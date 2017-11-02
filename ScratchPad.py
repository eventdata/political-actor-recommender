# coding=utf-8

# import json
# import operator
# import os
#
# actor_roles = json.load(open("output/new_actor_role.txt", "r"))
#
# new_actors = json.load(open("output/new_actor_final.txt", "r"))
#
# for (actor, freq) in new_actors:
#     roles = actor_roles[actor]
#
#     sorted_roles = sorted(roles.items(), key=operator.itemgetter(1))
#
#     print actor,": ", sorted_roles[-5:]
#
#
# output_dir = "parallel_output/"
# if os.path.exists(output_dir) is False:
#     os.mkdir(output_dir)


import pymongo

from pymongo import MongoClient
from bson import ObjectId


mongo_driver = MongoClient(host="localhost")

database = mongo_driver.test

mongo_id = database.temp.insert({"a": 123, "b":234})

print  mongo_id

id_str = str(mongo_id)

mongo_id = ObjectId(id_str)

db_object = database.temp.find_one({"_id": mongo_id})

new_fields = {'c': 'test'}

mongo_id = database.temp.update({"_id": mongo_id}, new_fields)

print mongo_id

print database.temp.count()


a = ('a','b','100')

print type(a)



