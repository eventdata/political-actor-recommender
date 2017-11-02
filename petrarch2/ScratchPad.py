from EventCoder import EventCoder


coder = EventCoder()

input_file = open("test_article_173_2.json","r")

content = input_file.read()

print content

print coder.encode(content)