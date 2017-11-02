import os
import yaml
import json

folder_name = "../dataset_new/"

main_dict = {}

for input_file_name in sorted(os.listdir(folder_name)):
    if input_file_name.endswith('_1.txt'):
        try:
            dict = yaml.load(open(folder_name+input_file_name).read())
            main_dict.update(dict)
        except:
            print "Issue with file : "+input_file_name


print len(main_dict)

with open(folder_name+"annotated_1.txt", 'w+') as fp:
    json.dump(main_dict, fp)
    fp.close()