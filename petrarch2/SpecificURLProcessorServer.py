from newspaper import Article
from pycorenlp import StanfordCoreNLP
import sys
import json
from flask import Flask, redirect
from flask import request, Response
from PetrarchFormatter import PetrarchFormatter


from EventCoder import EventCoder


reload(sys)
sys.setdefaultencoding('utf8')

app = Flask(__name__, static_url_path='')
app.config['PROPAGATE_EXCEPTIONS'] = True

@app.route("/process/sentence")
def process_sentence():
    sentence = request.args.get("sentence")

    formatter = PetrarchFormatter()

    coder = EventCoder()

    input = {}

    nlp = StanfordCoreNLP("http://localhost:9000")

    print type(sentence)

    output = nlp.annotate(str(sentence), properties={'annotators':'tokenize,ssplit,pos,depparse,parse', "outputFormat": "json", "timeout": 30000})

    print output['sentences'][0].keys()

    output['doc_id'] = "DUMMY_ID"

    output['head_line'] = "DUMMY TITLE"

    input["doc_id"] = "DUMMY_ID"
    input["head_line"] = "DUMMY_TITLE"

    input["sentences"] = []

    count = 0
    for entry in output["sentences"]:
        temp_entry = {}
        temp_entry["sentence_id"] = count
        start_offset = entry['tokens'][0]['characterOffsetBegin']  # Begin offset of first token.

        end_offset = entry['tokens'][-1]['characterOffsetEnd']  # End offset of last token.

        sent_str = sentence[start_offset:end_offset]


        count += 1
        temp_entry["sentence"] = sent_str

        temp_entry["parse_sentence"] = entry["parse"]

        input["sentences"].append(temp_entry)

    print output
    result = coder.encode(json.dumps(input))
    event_str =  json.dumps(formatter.encode(result))
    return Response(event_str)



@app.route("/process")
def process():
    article_url = request.args.get("url")
    if article_url is None or len(article_url) == 0:
        return Response("Please specify a valid URL to process.")

    formatter = PetrarchFormatter()
    article = Article(url=article_url)

    article.download()

    article.parse()

    coder = EventCoder()

    input = {}

    nlp = StanfordCoreNLP("http://localhost:9000")

    print type(article.text)

    output = nlp.annotate(str(article.text), properties={'annotators':'tokenize,ssplit,pos,depparse,parse', "outputFormat": "json", "timeout": 30000})

    print output['sentences'][0].keys()
    print output
    output['doc_id'] = "DUMMY_ID"

    output['head_line'] = article.title

    input["doc_id"] = "DUMMY_ID"
    input["head_line"] = article.title

    input["sentences"] = []

    count = 0
    for entry in output["sentences"]:
        temp_entry = {}
        temp_entry["sentence_id"] = count


        start_offset = entry['tokens'][0]['characterOffsetBegin']  # Begin offset of first token.

        end_offset = entry['tokens'][-1]['characterOffsetEnd']  # End offset of last token.

        sent_str = article.text[start_offset:end_offset]


        count += 1
        temp_entry["sentence"] = sent_str
        temp_entry["parse_sentence"] = entry["parse"]

        input["sentences"].append(temp_entry)

    print output
    result = coder.encode(json.dumps(input))
    event_str =  json.dumps(formatter.encode(result))
    return Response(event_str)



if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5123, threaded=True)
