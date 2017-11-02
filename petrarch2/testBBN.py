import json
import pprint
import re
import sys
import os
from ActorDictionary import ActorDictionary
from ClusterManager import ActorResolver
from readBBN import make_new_actor_list
from UnionFind import UnionFind
from ClusterSImilarityOLd import FuzzyClusterSimilarity
import time

reload(sys)
sys.setdefaultencoding('utf8')

pp = pprint.PrettyPrinter(indent=2)

discard_words_set = set(['THE', 'A', 'AN', 'OF', 'IN', 'AT', 'OUT', '', ' '])


N = 10
new_actor_over_time = dict()



#input_file = open('/root/Desktop/core_nlp_out_large.txt') #open('/root/test_pet')
#input_file = open('/root/test_pet2')

from StringIO import StringIO


def compress(item_list=[], simCalculator=FuzzyClusterSimilarity()):
    uf = UnionFind(item_list)
    count = 1
    for i in range(0, len(item_list)):
        maxRatio = 70
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

#folder_name = '/root/Desktop/files/'
#folder_name = '/root/Desktop/dataset/'
folder_name = '../dataset_new/'
actor_dict = ActorDictionary()
actor_resolver = ActorResolver()


for input_file_name in sorted(os.listdir(folder_name)):
    print ('reading file: ' + input_file_name)

    input_file = open(folder_name + input_file_name)

    total_new_actor_list = []
    word_dic = dict()
    line_count = 0
    for line in input_file:

        print line
        print '==================='

        if not line.startswith('{'): #skip the null entries
            print 'Not a useful line'
            continue
        #pp.pprint(another_coder.encode(line))

        new_actor_meta = dict()

        new_actor_meta['new_actor'], doc_id = make_new_actor_list(line)



        #print new_actor_meta

        new_actor_freq = dict()
        #new_actor_freq['doc_id'] = new_actor_meta['doc_id']


        total_count = 0
        for item in new_actor_meta['new_actor']:
            sentences = json.load(StringIO(line), encoding='utf-8')

            count = 0
            ner = set()

            for s in sentences['sentences']:
                #if item in ner:
                content = s['sentence']

                count += len(re.findall(item, content.upper()))
                if actor_dict.contains(item):
                   continue

                #TO_DO: find NP from tree: findNP(NPParseTreeHashMap, item)
                new_actor_freq[item] = count


        #print new_actor_freq

        new_actor = dict()
        new_actor['doc_id'] = doc_id
        new_actor['new_actor'] = actor_resolver.bbn_compress(new_actor_freq)

        #print  new_actor

        total_new_actor_list.append(new_actor)


    with open('../output/new_actor_bbn.txt', 'a') as outfile:
        outfile.write("\n")
        json.dump(total_new_actor_list, outfile)

    ##=========== ADDED CODE
    all_actor_names = []
    all_actor_freq = {}

    for item in total_new_actor_list:
        if 'new_actor' not in item:
            continue

        for key in item['new_actor']:
            all_actor_names.append(key)
            if key in all_actor_freq:
                all_actor_freq[key] = all_actor_freq[key] + item['new_actor'][key]
                # for k in code_dict:
                #     if k in window_actor_codes[key]:
                #         window_actor_codes[key][k] = window_actor_codes[key][k] + code_dict[k]
                #     else:
                #         window_actor_codes[key][k] = code_dict[k]
            else:
                all_actor_freq[key] = item['new_actor'][key]
                # window_actor_codes[key] = code_dict

    print "ACTOR NAMES FOUND: ", str(len(all_actor_names))

    uf = compress(item_list=all_actor_names)

    print "UNION COMPLETED"

    for item in all_actor_freq:
        if 'new_actor' not in item:
            continue
        temp_dict = {}

        for key in item['new_actor']:
            count = item['new_actor'][key]
            parent = uf.find(key)
            if parent != key:
                pass


                # for k in code_dict:
                #     if k in window_actor_codes[parent]:
                #         temp_event_code[k] = window_actor_codes[parent][k] + window_actor_codes[key][k]
                #     else:
                #         temp_event_code[k] = window_actor_codes[key][k]

            if parent not in temp_dict:
                temp_dict[parent] = all_actor_freq[parent] + count
            else:
                temp_dict[parent] = count + temp_dict[parent]
        item['new_actor'] = temp_dict
        # item['event_code'] = temp_event_code

    print "ENTRIES UPDATED"

    word_dict = dict()
    word_dict_count = dict()

    total_document = 0.0

    for item in total_new_actor_list:
        #{"new_actor": {"DHUBULIA": 2, "PRIMARY": 11, "NADIA\u00c2": 1}, "doc_id": "india_telegraph_bengal20160922.0001"}
        total_count = 0.0
        if 'new_actor' in item and 'doc_id' in item:
            total_document += 1
            for k in item['new_actor'].keys():
                total_count += item['new_actor'][k]

            for k in item['new_actor'].keys():
                if total_count > 0:
                    tf = 1.00 * (item['new_actor'][k]/total_count)
                else:
                    tf = 0.0


                if k not in word_dic:
                    word_dic[k] = tf
                    word_dict_count[k] = 1
                else:
                    word_dic[k] += tf
                    word_dict_count[k] += 1



    for k in word_dic.keys():
        word_dic[k] = word_dic[k] * (word_dict_count[k]/total_document)


    word_dic_sorted = sorted(word_dic.items(), key=lambda x : (-x[1], x[0]))[:N]

    with open('../output/new_actor_td_df_BBN_sorted.txt', 'a') as outfile:
        outfile.write('\n')
        json.dump(word_dic_sorted, outfile)

    for actor_item in  word_dic_sorted:
        actor_noun = actor_item[0]
        if actor_noun in new_actor_over_time:
            new_actor_over_time[actor_noun] += 1
        else:
            new_actor_over_time[actor_noun] = 1


    with open('../output/new_actor_bbn_td_df.txt', 'a') as outfile:
        outfile.write('\n')
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




with open('../output/new_actor_final_BBN.txt', 'w+') as outfile:
    #outfile.write("\nWindow " + str(count) + "\n")
    json.dump(sorted(compressed_new_actors.items(), key=lambda x: (-x[1], x[0])), outfile)
    outfile.close()


# with open('../output/current_actors.txt', 'w+') as outfile:
#     json.dump(current_actors, outfile)
#     outfile.close()







