from newspaper import Article
from pycorenlp import StanfordCoreNLP
import sys
import json

from EventCoder import EventCoder


reload(sys)
sys.setdefaultencoding('utf8')

article_url = "http://www.bbc.com/news/uk-politics-42277040"

article = Article(url=article_url)

article.download()

article.parse()

coder = EventCoder()

input = {}

nlp = StanfordCoreNLP("http://localhost:9000")

print type(article.text)

output = nlp.annotate(str(article.text), properties={'annotators':'tokenize,ssplit,pos,depparse,parse', "outputFormat": "json", "timeout": 30000})

print output['sentences'][0].keys()

output['doc_id'] = "DUMMY_ID"

output['head_line'] = article.title

input["doc_id"] = "DUMMY_ID"
input["head_line"] = article.title

input["sentences"] = []

count = 0
for entry in output["sentences"]:
    temp_entry = {}
    temp_entry["sentence_id"] = count

    count += 1
    temp_entry["sentence"] = ""
    temp_entry["parse_sentence"] = entry["parse"]

    input["sentences"].append(temp_entry)

print output

print coder.encode(json.dumps(input))





