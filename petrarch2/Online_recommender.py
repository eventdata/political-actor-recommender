from __future__ import unicode_literals


import json
import pprint
import re
import sys
import os


import time
import operator

from multiprocessing import Pool

from ClusterManager import ActorResolver
from ClusterSImilarity import FuzzyClusterSimilarity
from RoleDictionary import RoleDictionary
from UnionFind import UnionFind
from petrarch2 import PETRglobals
from ActorDictionary import ActorDictionary
from pymongo import MongoClient
from datetime import datetime

reload(sys)
sys.setdefaultencoding('utf8')



def log(message):
    log_file.write(message+"\n")
    log_file.flush()

current_actors = {}

pp = pprint.PrettyPrinter(indent=2)

discard_words_set = set(['THE', 'A', 'AN', 'OF', 'IN', 'AT', 'OUT', '', ' '])


from EventCoder import EventCoder

start_time = time.clock()
coder = EventCoder(petrGlobal={})

another_coder = EventCoder(petrGlobal=coder.get_PETRGlobals())
N = input("Number of recommended actors per window = ")
print N

new_actor_over_time = dict()


def compress(item_list=[], simCalculator=FuzzyClusterSimilarity()):
    uf = UnionFind(item_list)

    count = 1

    for i in range(0, len(item_list)):
        maxRatio = simCalculator.THRESHOLD
        maxMatched = None
        p1 = uf.find(item_list[i])
        print count
        count += 1
        for j in range(0, len(item_list)):
            if i == j:
                continue

            p2 = uf.find(item_list[j])

            ratio = simCalculator.measure(p1, p2)
            if ratio > maxRatio:
                maxRatio = ratio
                maxMatched = item_list[j]
        if maxMatched is not None:
            uf.union(maxMatched, item_list[i])
    return uf


#input_file = open('/root/Desktop/core_nlp_out_large.txt') #open('/root/test_pet')
#input_file = open('/root/test_pet2')

from StringIO import StringIO

#folder_name = "../small dataset/"
folder_name = '/Users/sxs149331/PycharmProjects/APART Dataset/APART Dataset/'
#folder_name = '/root/Desktop/dataset/'
#folder_name = '/root/Desktop/test1/'

actor_dict = ActorDictionary()

actorReolver = ActorResolver()

window_actor_roles = {}

skip = 10
num_windows = 10

output_dir = "parallel_output_r"+str(N)+"_d15/"
if os.path.exists(output_dir) is False:
    os.mkdir(output_dir)



log_file = open(output_dir+"apart_log.log", "w+")

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



#==========================================================
def window_processing(file_name):
    log("Starting a new window")
    window_start_time = time.clock()
    print ('reading file: ' + file_name)


    input_file = open(file_name)

    total_new_actor_list = []
    word_dic = dict()
    window_actor_codes = {}
    window_actor_roles = {}

    for line in input_file:

        print line
        print '==================='

        if not line.startswith('{'):  # skip the null entries
            print 'Not a useful line'
            continue
        # pp.pprint(another_coder.encode(line))

        dict_event = another_coder.encode(line)
        if dict_event is None:
            continue

        new_actor_meta = dict()
        nouns = []

        # count the event code
        event_code = dict()
        for k in dict_event.keys():
            new_actor_meta['doc_id'] = k
            if 'sents' in dict_event[k]:
                if (dict_event[k]['sents'] is not None):
                    keys = dict_event[k]['sents'].keys()

                    if keys is not None:
                        for l in keys:
                            if 'meta' in dict_event[k]['sents'][l]:
                                nouns += dict_event[k]['sents'][l]['meta']['nouns_not_matched']

                            if 'events' in dict_event[k]['sents'][l]:
                                for e in dict_event[k]['sents'][l]['events']:
                                    event_who = str(e[0]).replace('~', '').replace('+', '').replace('-', '').replace(
                                        '|', '').strip()
                                    event_whom = str(e[1]).replace('~', '').replace('+', '').replace('-', '').replace(
                                        '|', '').strip()
                                    if event_who in event_code:
                                        event_code[event_who] += 1
                                    else:
                                        event_code[event_who] = 1

                                    if event_whom in event_code:
                                        event_code[event_whom] += 1
                                    else:
                                        event_code[event_whom] = 1

        new_actor_meta['new_actor'] = list(set(nouns))
        # new_actor_meta['event_code'] = event_code


        # print new_actor_meta

        new_actor_freq = dict()
        # new_actor_freq['doc_id'] = new_actor_meta['doc_id']


        total_count = 0
        ner = set()

        ner_dic = dict()
        filter_new_actor = set()

        for item in new_actor_meta['new_actor']:
            sentences = json.load(StringIO(line), encoding='utf-8')

            count = 0
            for s in sentences['sentences']:
                # "(MONEY,$|48|million),(ORGANIZATION,United|Nations),(DATE,30|August|2016|today),(NUMBER,1.3|million),(LOCATION,Central|Africa|West|Central|Africa),(PERSON,WFP/Daouda|Guirou)"

                ner_text_list = ''

                if len(s['ner']) > 0:
                    for ner_item in s['ner'].replace('),(', ':').split(':'):
                        ner_item_list = ner_item.replace('(', '').replace(')', '').split(',')

                        if len(ner_item_list) != 2:
                            continue

                        if str(ner_item_list[
                                   0]) == 'PERSON':  # or ner_item_list[0] == 'MISC' or ner_item_list[0] == 'ORGANIZATION':
                            ner_text_list = ner_item_list[1]
                            ner = ner | set([x.strip().upper() for x in ner_text_list.split('|')])
                            ner = ner - discard_words_set

                            matched_actor_with_ner = item.strip().upper()

                            for m_ner in ner:
                                if (matched_actor_with_ner in m_ner) and (
                                    matched_actor_with_ner not in discard_words_set):
                                    filter_new_actor = set([matched_actor_with_ner]) - discard_words_set
                                    m_ner = m_ner.replace(' ', '_')
                                    if (m_ner in ner_dic):
                                        val = list(set(ner_dic[m_ner][0]) | filter_new_actor)
                                        ner_dic[m_ner] = (val, 0)
                                    else:
                                        ner_dic[m_ner] = (list(filter_new_actor), 0)




                                        # ner = ner | set([x.strip().upper() for x in s['ner'].replace('ORGANIZATION', '').replace('LOCATION', '').replace('PERSON', '').replace('MISC', '').replace('DATE', '').replace('(', '').replace(')', '').replace('|', ',').split(',')])
                                        # ner = ner | set([x.strip().upper() for x in ner_text_list.split('|')])
                                        # ner = ner - discard_words_set

        for dict_actor_item in ner_dic.keys():

            if actor_dict.contains(dict_actor_item):
                continue

            val = ner_dic[dict_actor_item]
            val_count = ner_dic[dict_actor_item][1]

            for item_token in ner_dic[dict_actor_item][0]:
                ner_count = 0
                for s in sentences['sentences']:
                    # if item in ner:
                    content = s['sentence']
                    try:
                        ner_count += len(re.findall(item_token, content.upper()))
                    except:
                        ner_count = 0

                if (val_count < ner_count):
                    val_count = ner_count

            ner_dic[dict_actor_item] = (ner_dic[dict_actor_item][0], val_count)

        # print 'NER'
        # print ner
        # print 'Actor List'
        # print ner_dic


        # print new_actor_freq

        new_actor = dict()
        new_actor['doc_id'] = new_actor_meta['doc_id']
        comp_dict = actorReolver.compress(ner_dic)
        temp_dict = {}
        for key in comp_dict:
            if actor_dict.contains(key):
                if key in current_actors:
                    current_actors[key] += 1
                else:
                    current_actors[key] = 1
                continue
            else:
                temp_dict[key] = comp_dict[key]

        new_actor['new_actor'] = temp_dict
        new_actor['event_code'] = event_code
        if 'DONALD_TRUMP_DONALD_TRUMP' in temp_dict:
            print new_actor['doc_id'], file_name
            # sys.exit()
        pprint.pprint(new_actor['new_actor'])
        # print  new_actor

        total_new_actor_list.append(new_actor)

    with open(output_dir+'new_actor.txt', 'a+') as outfile:
        json.dump(total_new_actor_list, outfile)
        outfile.write('\n')

    word_dict = dict()
    word_dict_count = dict()

    total_document = 0.0

    ##=========== ADDED CODE
    all_actor_names = []
    all_actor_freq = {}

    for item in total_new_actor_list:
        if 'new_actor' not in item:
            continue
        code_dict = item['event_code']

        for key in item['new_actor']:
            all_actor_names.append(key)
            if key in all_actor_freq:
                all_actor_freq[key] = all_actor_freq[key] + item['new_actor'][key][1]
                # for k in code_dict:
                #     if k in window_actor_codes[key]:
                #         window_actor_codes[key][k] = window_actor_codes[key][k] + code_dict[k]
                #     else:
                #         window_actor_codes[key][k] = code_dict[k]
            else:
                all_actor_freq[key] = item['new_actor'][key][1]
                # window_actor_codes[key] = code_dict

    print "ACTOR NAMES FOUND: ", str(len(all_actor_names))
    log("ACTOR NAMES FOUND: " + str(len(all_actor_names)))
    uf = compress(item_list=all_actor_names)

    print "UNION COMPLETED"

    for item in all_actor_freq:
        if 'new_actor' not in item:
            continue
        temp_dict = {}
        temp_event_code = {}

        for key in item['new_actor']:
            sub_actor_list, count = item['new_actor'][key]
            parent = uf.find(key)
            if parent != key:
                sub_actor_list.append(parent)
                code_dict = window_actor_codes[key]

                # for k in code_dict:
                #     if k in window_actor_codes[parent]:
                #         temp_event_code[k] = window_actor_codes[parent][k] + window_actor_codes[key][k]
                #     else:
                #         temp_event_code[k] = window_actor_codes[key][k]

            if parent not in temp_dict:
                temp_dict[parent] = (sub_actor_list, all_actor_freq[parent] + count)
            else:
                temp_dict[parent] = (sub_actor_list, count + temp_dict[parent][1])
        item['new_actor'] = temp_dict
        # item['event_code'] = temp_event_code

    print "ENTRIES UPDATED"

    # Collecting actor roles


    for item in total_new_actor_list:
        actors = item['new_actor']
        for actor_key in actors:
            if actor_key in window_actor_roles:
                for role_key in item['event_code']:
                    if role_key in window_actor_roles[actor_key]:
                        window_actor_roles[actor_key][role_key] += item['event_code'][role_key]
                    else:
                        window_actor_roles[actor_key][role_key] = item['event_code'][role_key]
            else:
                window_actor_roles[actor_key] = item['event_code']

    # ========== END OF ADDED CODE =================

    for item in total_new_actor_list:
        # {"new_actor": {"DHUBULIA": 2, "PRIMARY": 11, "NADIA\u00c2": 1}, "doc_id": "india_telegraph_bengal20160922.0001"}
        total_count = 0.0
        if 'new_actor' in item and 'doc_id' in item:
            total_document += 1
            for k in item['new_actor'].keys():
                total_count += item['new_actor'][k][1]

            for k in item['new_actor'].keys():
                tf = 0.0
                if (total_count != 0):
                    tf = 1.00 * (item['new_actor'][k][1] / total_count)
                else:
                    print item['new_actor'][k]

                if k not in word_dic:
                    word_dic[k] = tf
                    word_dict_count[k] = 1
                else:
                    word_dic[k] += tf
                    word_dict_count[k] += 1

    for k in word_dic.keys():
        word_dic[k] = word_dic[k] * (word_dict_count[k] / total_document)

    word_dic_sorted = sorted(word_dic.items(), key=lambda x: (-x[1], x[0]))[:N]

    # with open('/root/Desktop/new_actor_td_df.txt', 'w') as outfile:
    #    json.dump(word_dic_sorted, outfile)

    for actor_item in word_dic_sorted:
        actor_noun = actor_item[0]
        if actor_noun in new_actor_over_time:
            new_actor_over_time[actor_noun] += 1
        else:
            new_actor_over_time[actor_noun] = 1

    # Replacement of code block above
    window_recomended_actors = []
    for actor_item in word_dic_sorted:
        window_recomended_actors.append(actor_item[0])



    count = 1
    with open(output_dir+'new_actor_td_df.txt', 'a+') as outfile:
        outfile.write("\nWindow " + str(count) + "\n")
        json.dump(sorted(new_actor_over_time.items(), key=lambda x: (-x[1], x[0])), outfile)

    # End of processing for 1 window
    window_end_time = time.clock()
    log("Processing time for this window: " + str(window_end_time - window_start_time))

    return window_recomended_actors, window_actor_roles

#==========================================================


recommended_actors = []
recommended_roles = []

pool = Pool(4)

window_file_names = []
for input_file_name in sorted(os.listdir(folder_name)):

    log("Starting a new window")
    window_start_time = time.clock()
    print ('reading file: ' + input_file_name)

    if skip != 0:
        skip -= 1
        print "Skipping"
        continue
    if num_windows == 0:
        break
    num_windows -= 1
    window_file_names.append(folder_name + input_file_name)




results = pool.map(window_processing, window_file_names)


for result in results:
    window_recommend_actor = result[0]
    window_recommend_roles = result[1]
    recommended_roles.append(window_recommend_roles)

    for actor in window_recommend_actor:
        if actor in new_actor_over_time:
            new_actor_over_time[actor] += 1
        else:
            new_actor_over_time[actor] = 1


for key in new_actor_over_time:
    recommended_actors.append(key)


uf = compress(item_list=recommended_actors)
compressed_actor_roles = {}
compressed_new_actors = {}
for actor_name in recommended_actors:
    parent_actor = uf.find(actor_name)

    if parent_actor in compressed_new_actors:
        compressed_new_actors[parent_actor] += new_actor_over_time[actor_name]
    else:
        compressed_new_actors[parent_actor] = new_actor_over_time[actor_name]

for actor_name in recommended_actors:
    for i in range(0, len(recommended_roles)):
        window_actor_roles = recommended_roles[i]
        parent = uf.find(actor_name)
        if parent in compressed_actor_roles:
            if actor_name not in window_actor_roles:
                continue
            for k in window_actor_roles[actor_name]:
                if k in compressed_actor_roles[parent]:
                    compressed_actor_roles[parent][k] += window_actor_roles[actor_name][k]
                else:
                    compressed_actor_roles[parent][k] = window_actor_roles[actor_name][k]
        elif actor_name in window_actor_roles:
            compressed_actor_roles[parent] = window_actor_roles[actor_name]

end_time = time.clock()

print "Time Required: ", str(end_time - start_time)

with open(output_dir+'new_actor_final.txt', 'w+') as outfile:
    #outfile.write("\nWindow " + str(count) + "\n")
    json.dump(sorted(compressed_new_actors.items(), key=lambda x: (-x[1], x[0])), outfile)
    outfile.close()


with open(output_dir+'new_actor_role.txt', 'w+') as outfile:
    json.dump(compressed_actor_roles, outfile)
    outfile.close()

with open(output_dir+'current_actors.txt', 'w+') as outfile:
    json.dump(current_actors, outfile)
    outfile.close()



excluded_actor_file = open("../output/List_Excluded_Actors")
excluded_actor_list = []
for line in excluded_actor_file:
    excluded_actor_list.append(line.strip())

count = 0

extracted_actors = []

for w in compressed_new_actors.items():
    if w[0] in excluded_actor_list:
        count += 1
        extracted_actors.append(w[0])
        print w[0]
print count

role_dict = RoleDictionary()
simCalculator = FuzzyClusterSimilarity()
count = 0
count_partial = 0;
for actor in extracted_actors:
    suggested_roles = compressed_actor_roles.get(actor)
    sorted_list = sorted(suggested_roles.items(), key=lambda x:x[1])[-5:]
    suggestion_set = set()

    actual_roles  = role_dict.roles(actor)
    for key in actual_roles:
       suggestion_set = actual_roles[key]
    for i in range(0, len(sorted_list)):
        print sorted_list[i]
        if sorted_list[i][0] in suggestion_set:
            count += 1
            break
    maxRatio = simCalculator.THRESHOLD
    maxMatched = None
    for i in range(0, len(sorted_list)):
        for key in suggestion_set:
            ratio = simCalculator.measure(key, sorted_list[i][0])
            if ratio >= maxRatio:
                maxRatio = ratio
                maxMatched = sorted_list[i]
    if maxMatched is not None:
        count_partial += 1

    print  actual_roles, suggested_roles

print count
print count_partial



