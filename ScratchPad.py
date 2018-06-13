from petrarch2.EventCoder import EventCoder

import json

coder = EventCoder()

article = json.dumps(json.load(open("test_article_173_2.json", "r")))

events = coder.encode(article)

print events