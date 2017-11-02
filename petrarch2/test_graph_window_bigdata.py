from __future__ import unicode_literals

import json
import pprint
import re
import sys
import os

import time
import operator

from ClusterManager import ActorResolver
from ClusterSImilarityOLd import FuzzyClusterSimilarity
from Graph import Graph
from LabelPropagation import LabelPropagation
from RoleDictionary import RoleDictionary
from UnionFind import UnionFind
from petrarch2 import PETRglobals
from ActorDictionary import ActorDictionary
reload(sys)
sys.setdefaultencoding('utf8')

current_actors = {}

pp = pprint.PrettyPrinter(indent=2)

discard_words_set = set(['THE', 'A', 'AN', 'OF', 'IN', 'AT', 'OUT', '', ' '])



from EventCoder import EventCoder

start_time = time.clock()
coder = EventCoder(petrGlobal={})

another_coder = EventCoder(petrGlobal=coder.get_PETRGlobals())
N = 5

new_actor_over_time = dict()

interaction_graph = dict()


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


#input_file = open('/root/Desktop/core_nlp_out_large.txt') #open('/root/test_pet')
#input_file = open('/root/test_pet2')

from StringIO import StringIO


folder_name = '../dataset_new/'
#folder_name = '/root/Desktop/dataset/'
#folder_name = '/root/Desktop/test1/'

actor_dict = ActorDictionary()

actorReolver = ActorResolver()

window_actor_roles = {}

interaction_graph = {}



for input_file_name in sorted(os.listdir(folder_name)):
    print ('reading file: ' + input_file_name)

    input_file = open(folder_name + input_file_name)

    total_new_actor_list = []
    word_dic = dict()
    window_actor_codes = {}

    window_doc_actors = []
    window_all_actors = []

    line_count = 0
    for line in input_file:
        line_count = line_count + 1
        # if line_count == 6:
        #     break
        print line
        print '==================='

        if not line.startswith('{'): #skip the null entries
            print 'Not a useful line'
            continue
        #pp.pprint(another_coder.encode(line))

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

        new_actor_meta['new_actor'] = list(set(nouns))
        #new_actor_meta['event_code'] = event_code


        #print new_actor_meta

        new_actor_freq = dict()
        #new_actor_freq['doc_id'] = new_actor_meta['doc_id']


        total_count = 0
        ner = set()

        ner_dic = dict()
        filter_new_actor = set()

        for item in new_actor_meta['new_actor']:
            sentences = json.load(StringIO(line), encoding='utf-8')

            count = 0
            for s in sentences['sentences']:
                #"(MONEY,$|48|million),(ORGANIZATION,United|Nations),(DATE,30|August|2016|today),(NUMBER,1.3|million),(LOCATION,Central|Africa|West|Central|Africa),(PERSON,WFP/Daouda|Guirou)"

                ner_text_list = ''

                if len(s['ner']) > 0:
                    for ner_item in s['ner'].replace('),(', ':').split(':'):
                        ner_item_list = ner_item.replace('(', '').replace(')', '').split(',')

                        if len(ner_item_list) != 2:
                            continue


                        if str(ner_item_list[0]) == 'PERSON': # or ner_item_list[0] == 'MISC' or ner_item_list[0] == 'ORGANIZATION':
                            ner_text_list = ner_item_list[1]
                            ner = ner | set([x.strip().upper() for x in ner_text_list.split('|')])
                            ner = ner - discard_words_set

                            matched_actor_with_ner = item.strip().upper()

                            for m_ner in ner:
                                if (matched_actor_with_ner in m_ner) and (matched_actor_with_ner not in discard_words_set):
                                    filter_new_actor = set([matched_actor_with_ner])  - discard_words_set
                                    m_ner = m_ner.replace(' ', '_')
                                    if (m_ner in ner_dic):
                                        val = list(set(ner_dic[m_ner][0]) | filter_new_actor)
                                        ner_dic[m_ner] = (val, 0)
                                    else:
                                        ner_dic[m_ner] = (list(filter_new_actor), 0)






        new_actor = dict()
        new_actor['doc_id'] = new_actor_meta['doc_id']
        comp_dict = actorReolver.compress(ner_dic)
        window_doc_actors.append(comp_dict.keys())


        total_new_actor_list.append(new_actor)
        window_all_actors.extend(comp_dict.keys())

    uf = compress(item_list=window_all_actors)

    window_actor_freq = {}

    for actor_list in window_doc_actors:
        for actor in actor_list:
            parent = uf.find(actor)
            if parent in window_actor_freq:
                window_actor_freq[parent] = window_actor_freq[parent] + 1
            else:
                window_actor_freq[parent] = 1

    print "Frequency Calculated"

    #select Top N most frequent non-existing actor
    top_actor_list=[]
    win_actor_freq_sorted = sorted(window_actor_freq.items(), reverse=True)
    count = 0
    for item in win_actor_freq_sorted:
        if actor_dict.contains(item[0]): #existing actor in the dictionary, ignore
            continue

        top_actor_list.append(item[0])
        count = count + 1
        if count > N:
            break

    print top_actor_list

    print "Top Actor List Computed"



    #building inetraction graph between users.
    for actor_list in window_doc_actors:
        eligible_actor_list = []

        for actor in actor_list:
            if uf.find(actor) in top_actor_list or actor_dict.contains(actor):
                eligible_actor_list.append(uf.find(actor))

        for i in range(0, len(eligible_actor_list)):
            for j in range(0, len(eligible_actor_list)):
                if i == j:
                    continue
                if eligible_actor_list[i] in interaction_graph:
                    neighbours = interaction_graph[eligible_actor_list[i]]
                    if eligible_actor_list[j] in neighbours:
                        neighbours[eligible_actor_list[j]] = neighbours[eligible_actor_list[j]] + 1
                    else:
                        neighbours[eligible_actor_list[j]] = 1
                else:
                    interaction_graph[eligible_actor_list[i]] = {eligible_actor_list[j]: 1}

        print interaction_graph





    with open('../output/new_actor.txt', 'a+') as outfile:
        json.dump(total_new_actor_list, outfile)
        outfile.write('\n')

    word_dict = dict()
    word_dict_count = dict()

    total_document = 0.0



    ##=========== ADDED CODE
    all_actor_names = []
    all_actor_freq = {}









    #Collecting actor roles


    for item in total_new_actor_list:
        if 'new_actor' not in item:
            continue

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
    pprint.pprint(current_actors, outfile)
    outfile.close()

with open('../output/interaction_graph.txt', 'w+') as outfile:
    json.dump(interaction_graph, outfile)
    outfile.close()



graph = Graph()
role_dict = RoleDictionary()

for name in interaction_graph:
    neighbours = interaction_graph[name]

    for n in neighbours:
        graph.add_edge(name, n, neighbours[n])


print "Number of Actors: ", graph.get_numVertices()
print "Number of Interactions: ", graph.get_numEdges()

label_prop = LabelPropagation(graph, num_iters=100)

initial_roles = {}

for v in graph.get_vertices():
    if role_dict.roles(v).get(v) is None:
        continue
    print role_dict.roles(v).get(v)
    initial_roles[v] = list(role_dict.roles(v).get(v))

print '========================='

calculated_roles = label_prop.propagate(initial_roles)

temp_file = open('../output/List_Excluded_Actors')

for line in temp_file:
    if line.strip() in calculated_roles:
        print line.strip(), calculated_roles[line.strip()]
    else:
        print 'No Key for ', line.strip()


with open('../output/interaction_graph_roles.txt', 'w+') as outfile:
    json.dump(calculated_roles, outfile)
    outfile.close()



