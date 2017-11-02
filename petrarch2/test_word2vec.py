
from EventCoder import EventCoder

event_coder = EventCoder()

fp = open("test_article_2.json")

article = fp.read()

events  = event_coder.encode(article)

print events
