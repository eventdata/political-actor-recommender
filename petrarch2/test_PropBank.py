from __future__ import unicode_literals

import json
import pprint
import re
import sys
import os

import time
import operator

from ClusterManager import ActorResolver
from ClusterSImilarity import FuzzyClusterSimilarity
from ClusterSImilarity import MinhashClusterSimilarity
from RoleDictionary import RoleDictionary
from UnionFind import UnionFind
from petrarch2 import PETRglobals
from ActorDictionary import ActorDictionary
from PropbankAnnotator import PropbankAnnotator
import yaml

reload(sys)
sys.setdefaultencoding('utf8')

current_actors = {}

pp = pprint.PrettyPrinter(indent=2)

discard_words_set = set(['THE', 'A', 'AN', 'OF', 'IN', 'AT', 'OUT', '', ' '])


from EventCoder import EventCoder

start_time = time.clock()
coder = EventCoder(petrGlobal={})
propbank = PropbankAnnotator()
 
another_coder = EventCoder(petrGlobal=coder.get_PETRGlobals())
N = 5
new_actor_over_time = dict()


def compress(item_list=[], simCalculator=FuzzyClusterSimilarity()):
    uf = UnionFind(item_list)

    count = 1

    print "Threshold ", simCalculator.THRESHOLD

    #sys.exit(0)

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
            print maxMatched, item_list[i]
        else:
            print item_list[i]
    return uf


#input_file = open('/root/Desktop/core_nlp_out_large.txt') #open('/root/test_pet')
#input_file = open('/root/test_pet2')

from StringIO import StringIO


folder_name = '../dataset_new/'
#folder_name = '/root/Desktop/dataset/'
#folder_name = '/root/Desktop/test1/'

actor_dict = ActorDictionary()

actorReolver = ActorResolver(clsSimilarity=FuzzyClusterSimilarity())

window_actor_roles = {}

for input_file_name in sorted(os.listdir(folder_name)):
    print ('reading file: ' + input_file_name)
    if 'annotated' in input_file_name:
        continue
    input_file = open(folder_name + input_file_name)
    propbank_dict = json.load(open(folder_name+"annotated_"+input_file_name))
    print "Annotation Dictionary loaded."

    print "No. of Entries(Articles): "+str(len(propbank_dict))

    total_new_actor_list = []
    word_dic = dict()
    window_actor_codes = {}
    lcount = 0

    for line in input_file:
        lcount = lcount + 1


        print line
        print '==================='

        if not line.startswith('{'): #skip the null entries
            print 'Not a useful line'
            continue
        #pp.pprint(another_coder.encode(line))
        dict_event = None
        try:
            dict_event = another_coder.encode(line)
        except:
            continue

        if dict_event is None:
            continue

        new_actor_meta = dict()
        nouns = []

        ner_dic = dict()
        filter_new_actor = set()
        article = json.load(StringIO(line), encoding='utf-8')
        article_id = article['doc_id']
        annotation_not_found = False

        scount = 0
        count = 0

        annotation = propbank_dict.get(article_id)

        if annotation is None:
            annotation_not_found = True
            print "MISSING Article ANNOTATION, ", article_id
            continue

        article_actor_list = []
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
                                actor_list = None
                                try:
                                    sent_annotation = annotation.get(str(l))
                                    if sent_annotation is None:
                                        print "ANNOTATION MISSING"
                                        continue
                                    actor_list = propbank.retrieve_actors(sent_annotation)
                                    print "Sentence ", l , actor_list
                                except:
                                    actor_list = None
                                if actor_list is not None:
                                    for a in actor_list:
                                        article_actor_list.append(a)

                            if 'events' in dict_event[k]['sents'][l]:
                                for e in dict_event[k]['sents'][l]['events']:
                                    event_who = str(e[0]).replace('~','').replace('+','').replace('-','').replace('|','').strip()
                                    event_whom = str(e[1]).replace('~','').replace('+','').replace('-','').replace('|','').strip()
                                    if event_who in event_code:
                                        event_code[event_who] += 1
                                    else:
                                        event_code[event_who] = 1

                                    if event_whom in event_code:
                                        event_code[event_whom] += 1
                                    else:
                                        event_code[event_whom] = 1

        #new_actor_meta['new_actor'] = list(set(nouns))
        #new_actor_meta['event_code'] = event_code


        #print new_actor_meta

        new_actor_freq = dict()
        #new_actor_freq['doc_id'] = new_actor_meta['doc_id']


        total_count = 0
        ner = set()


        print "Number of Actors Found ", len(article_actor_list)

        for actor_name in article_actor_list:

            temp_name = actor_name.strip().replace(' ','_').upper()

            if actor_dict.contains(temp_name): #this actor exists in the CAMEO dictionary
                continue

            if temp_name in ner_dic:
                ner_dic[temp_name] = (temp_name, ner_dic[temp_name][1]+1)
            else:
                ner_dic[temp_name] = (temp_name, 1)

        if annotation_not_found == True:
            print "Annotation Not Found"

            continue

        print "Number of Possible New Actors ", len(ner_dic)




        #print new_actor_freq

        new_actor = dict()
        new_actor['doc_id'] = new_actor_meta['doc_id']
        print "Before Compression: ", ner_dic
        comp_dict = actorReolver.compress(ner_dic)
        print "After Compression: ", ner_dic
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
        if 'DUTERTE' in temp_dict:
            print new_actor['doc_id'], input_file_name
            #sys.exit()
        pprint.pprint(new_actor['new_actor'])
        #print  new_actor

        total_new_actor_list.append(new_actor)


    with open('../output/new_actor.txt', 'a+') as outfile:
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
                all_actor_freq[key] = all_actor_freq[key]+item['new_actor'][key][1]
                # for k in code_dict:
                #     if k in window_actor_codes[key]:
                #         window_actor_codes[key][k] = window_actor_codes[key][k] + code_dict[k]
                #     else:
                #         window_actor_codes[key][k] = code_dict[k]
            else:
                all_actor_freq[key] = item['new_actor'][key][1]
                #window_actor_codes[key] = code_dict

    print "ACTOR NAMES FOUND: ", str(len(all_actor_names))

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
                temp_dict[parent] = (sub_actor_list, all_actor_freq[parent]+count)
            else:
                temp_dict[parent] = (sub_actor_list, count + temp_dict[parent][1])
        item['new_actor'] = temp_dict
        #item['event_code'] = temp_event_code

    print "ENTRIES UPDATED"

    #Collecting actor roles


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

    #========== END OF ADDED CODE =================

    for item in total_new_actor_list:
        #{"new_actor": {"DHUBULIA": 2, "PRIMARY": 11, "NADIA\u00c2": 1}, "doc_id": "india_telegraph_bengal20160922.0001"}
        total_count = 0.0
        if 'new_actor' in item and 'doc_id' in item:
            total_document += 1
            for k in item['new_actor'].keys():
                total_count += item['new_actor'][k][1]

            for k in item['new_actor'].keys():
                tf = 0.0
                if (total_count != 0):
                    tf = 1.00 * (item['new_actor'][k][1]/total_count)
                else:
                    print item['new_actor'][k]


                if k not in word_dic:
                    word_dic[k] = tf
                    word_dict_count[k] = 1
                else:
                    word_dic[k] += tf
                    word_dict_count[k] += 1



    for k in word_dic.keys():
        word_dic[k] = word_dic[k] * (word_dict_count[k]/total_document)


    word_dic_sorted = sorted(word_dic.items(), key=lambda x : (-x[1], x[0]))[:N]

    #with open('/root/Desktop/new_actor_td_df.txt', 'w') as outfile:
    #    json.dump(word_dic_sorted, outfile)

    for actor_item in  word_dic_sorted:
        actor_noun = actor_item[0]
        if actor_noun in new_actor_over_time:
            new_actor_over_time[actor_noun] += 1
        else:
            new_actor_over_time[actor_noun] = 1


    # Replacement of code block above




    count = 1
    with open('../output/new_actor_td_df.txt', 'a+') as outfile:
        outfile.write("\nWindow "+str(count)+"\n")
        json.dump(sorted(new_actor_over_time.items(), key=lambda x : (-x[1], x[0])), outfile)

recommended_actors = []
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
    parent = uf.find(actor_name)
    if parent in compressed_actor_roles:
        for k in window_actor_roles[actor_name]:
            if k in compressed_actor_roles[parent]:
                compressed_actor_roles[parent][k] += window_actor_roles[actor_name][k]
            else:
                compressed_actor_roles[parent][k] = window_actor_roles[actor_name][k]
    else:
        compressed_actor_roles[parent] = window_actor_roles[actor_name]

end_time = time.clock()

print "Time Required: ", str(end_time - start_time)

with open('../output/new_actor_final.txt', 'w+') as outfile:
    #outfile.write("\nWindow " + str(count) + "\n")
    json.dump(sorted(compressed_new_actors.items(), key=lambda x: (-x[1], x[0])), outfile)
    outfile.close()


with open('../output/new_actor_role.txt', 'w+') as outfile:
    json.dump(compressed_actor_roles, outfile)
    outfile.close()

with open('../output/current_actors.txt', 'w+') as outfile:
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
count = 0
for actor in extracted_actors:
    suggested_roles = compressed_actor_roles.get(actor)
    sorted_list = sorted(suggested_roles.items(), key=lambda x:x[1])[-10:]
    suggestion_set = set()

    actual_roles = role_dict.roles(actor)
    for key in actual_roles:
       suggestion_set = actual_roles[key]
    for i in range(0, len(sorted_list)):
        print sorted_list[i]
        if sorted_list[i][0] in suggestion_set:
            count += 1
            break

    print  actual_roles, suggested_roles

print count



