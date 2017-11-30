from EventCoder import EventCoder
import json

coder = EventCoder()
article = json.dumps(json.load(open("test_article_173_2.json","r"), encoding='utf-8'))
print article
result = coder.encode(article)

print result