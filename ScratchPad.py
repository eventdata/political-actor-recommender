import requests
import shutil

params = {"secret-key": "mySecretKey"}
url = "http://104.198.76.143:8080/dictionary/downloadDictionary"
local_filename = url.split('/')[-1] + ".txt"
r = requests.get(url, headers = params, stream=True)
with open(local_filename, 'wb+') as f:
	shutil.copyfileobj(r.raw, f)
print(str(local_filename))

