import ast
import collections


class PetrarchFormatter:

    def encode(self, petr_output):
        return self.rec_key_replace(petr_output)



    def decode(self, converted_output):
        pass

    def __find_dict(self, list):
        dicts = []
        for item in list:
            if isinstance(item, dict):
                dicts.append(dict)
            elif isinstance(item, list):
                dicts.extend(self.__find_dict(list))
        return dicts


    def __key_collapse(self, key):
        if isinstance(key, tuple):
            return "__".join(key)
        elif not isinstance(key, str):
            return str(key).replace(".", "##")

        return key.replace(".", "##")

    def rec_key_replace(self, obj):
        if isinstance(obj, collections.Mapping):
            return {self.__key_collapse(key): self.rec_key_replace(val) for key, val in obj.items()}
        elif isinstance(obj, list):
            temp_list = []
            for item in obj:
                temp_list.append(self.rec_key_replace(item))
            return temp_list
        return obj





    def __decode(self, original_dict, output_dict):
        pass

# sourceFile = "/Volumes/Untitled 2/Users/sayeed/July_Dataset/20170705.json"
# # destinationFile = "test_phoenix.txt"
# # # geoUrl = raw_input("Enter the url to access Clavin Cliff server: ")
# # # geoPort = raw_input("Enter the port number to access Clavin Cliff server: ")
# #
# fhand = open(sourceFile)
# # fhand2 = open(destinationFile, 'w+')
# # #formatter = PhoenixConverter(geo_ip="149.165.168.205")
# # count = 0
# from pymongo import MongoClient
# from bson import ObjectId
#
#
# mongo_driver = MongoClient(host="localhost")
#
# database = mongo_driver.test
#
# formatter = PetrarchFormatter()
#
# for line in fhand:
#     line = ast.literal_eval(line)
#
#     sample_dict = ast.literal_eval(line["petrarch"])
#
#     dict_2 = formatter.encode(sample_dict)
#
#     print dict_2
#     database.petrarch.insert(dict_2, check_keys=False)


