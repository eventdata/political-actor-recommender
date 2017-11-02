from __future__ import unicode_literals
from StringIO import StringIO

from practnlptools.tools import Annotator
import os
import json
import sys
import multiprocessing




reload(sys)
sys.setdefaultencoding('utf8')

annotator = Annotator()
pool = multiprocessing.Pool(processes=8)
queue = multiprocessing.Queue()



folder_name = '/Users/sxs149331/PycharmProjects/APART Dataset/APART Dataset/'

#output_file = open('../output/annotated_articles.txt')

num_skip_files = 0
num_skip_articles = 0
skip_count = 0
limit = -1

# def parse_job(line, queue):
#     article = json.load(StringIO(line), encoding='utf-8')
#
#     article_id = article['doc_id']
#
#     annotation_map = {}
#
#     for sentence in article['sentences']:
#         annotations = None
#         try:
#             annotations = annotator.getAnnotations(sentence['sentence'], dep_parse=True)
#         except:
#             continue
#         sentence_id = sentence['sentence_id']
#
#         events_map = {}
#
#         events_map['events'] = annotations['srl']
#         events_map['ner'] = annotations['ner']
#
#         annotation_map[sentence_id] = events_map
#
#     queue.put((article_id, annotation_map))

for input_file_name in sorted(os.listdir(folder_name)):
    print ('reading file: ' + input_file_name)

    if 'annotated' in input_file_name:
        continue

    if num_skip_files != 0:
        num_skip_files = num_skip_files - 1
        continue





    #decision = raw_input('Start the Job??')



    input_file = open(folder_name + input_file_name)
    output_file = open(folder_name+'annotated_'+str(num_skip_articles)+"_"+input_file_name, 'w+')
    articles_info = {}


    lcount = 0
    for line in input_file:

        lcount = lcount + 1
        if skip_count < num_skip_articles:
            skip_count = skip_count + 1
            print "Skipping ", skip_count
            continue
        if limit != 0:
            limit = limit - 1
        else:
            break

        # if lcount == 20:
        #     break
        print "Article No: ",lcount
        # print line
        # print '==================='

        if not line.startswith('{'): #skip the null entries
            print 'Not a useful line'
            continue

        article = json.load(StringIO(line), encoding='utf-8')

        article_id = article['doc_id']

        annotation_map = {}

        for sentence in article['sentences']:
            annotations = None
            try:
                annotations = annotator.getAnnotations(sentence['sentence'], dep_parse=True)
            except:
                continue
            sentence_id = sentence['sentence_id']

            events_map = {}

            events_map['events'] = annotations['srl']
            events_map['ner'] = annotations['ner']

            annotation_map[sentence_id] = events_map


        articles_info[article_id] = annotation_map
        #
        # pool.map(parse_job, [line, queue])

    #
    # pool.join()
    #
    # for item in queue:
    #     articles_info[item[0]] = item[1]

    json.dump(articles_info, output_file)

    output_file.close()

    break















