__author__ = 'root'

import json
from cameoxml import cameoxml
from StringIO import StringIO


discard_words_set = set(['THE', 'A', 'AN', 'OF', 'IN', 'AT', 'OUT', '', ' '])

def read_actors_and_role(cameo_doc):
    actor_dict = dict()
    role_dict = dict()

    for event in cameo_doc.events:
        for participant in event.participants:
            if participant.actor_id not in actor_dict:
                if participant.actor_name != '':
                    actor_name_with_under_score = participant.actor_name
                    actor_dict[participant.actor_id] = actor_name_with_under_score
            if participant.agent_id not in role_dict:
                if participant.agent_name != '':
                    role_dict[participant.agent_name] = 1

    return actor_dict, role_dict

def make_actor_list_for_each_sentence(text):
    response = cameoxml.send_document(text, hostname='10.176.148.60', port=8001, document_date='2016-01-21')
    cameo_doc = cameoxml.build_document_from_response(response)
    actor_list = list()

    actor_dict, role_dict = read_actors_and_role(cameo_doc)

    for item in actor_dict:
        actor_list.append(actor_dict[item].upper())

    return actor_list, role_dict


def make_new_actor_list(line):
    new_actor_list = list()

    sentences = json.load(StringIO(line), encoding='utf-8')
    doc_id = sentences['doc_id']

    count = 0
    ner = set()
    role_dict = dict()

    for s in sentences['sentences']:
        #"(MONEY,$|48|million),(ORGANIZATION,United|Nations),(DATE,30|August|2016|today),(NUMBER,1.3|million),(LOCATION,Central|Africa|West|Central|Africa),(PERSON,WFP/Daouda|Guirou)"

        ner_text_list = ''

        actor_list, role_dict_line = make_actor_list_for_each_sentence(s['sentence'])
        new_actor_list = new_actor_list + actor_list

        for role_item in role_dict_line:
            if role_item not in role_dict:
                role_dict[role_item] = role_dict_line[role_item]
            else:
                role_dict[role_item] = role_dict[role_item] + role_dict_line[role_item]



        if len(s['ner']) > 0:
            for ner_item in s['ner'].replace('),(', ':').split(':'):
                ner_item_list = ner_item.replace('(', '').replace(')', '').split(',')

                if len(ner_item_list) != 2:
                    continue


                if ner_item_list[0] == 'PERSON': # or ner_item_list[0] == 'MISC' or ner_item_list[0] == 'ORGANIZATION':
                    ner_text_list = ner_item_list[1]
                    ner = ner | set([x.strip().upper() for x in ner_text_list.split('|')])
                    ner = ner - discard_words_set



    new_actor_list = list(ner - set(new_actor_list))
    return new_actor_list, doc_id #, role_dict







# response = cameoxml.send_document('The American president Barack Obama met with Putin.', hostname='10.176.148.60', port=8001, document_date='2016-01-21')
#
# print response
#
# print make_actor_list_for_each_sentence('The American president Barack Obama met Putin')



