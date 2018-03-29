import requests
import shutil
import schedule
import datetime
import time

def download():
    params = {"secret-key": "mySecretKey"}
    url = "http://104.198.76.143:8080/dictionary/downloadDictionary"
    local_filename = url.split('/')[-1] + ".txt"
    r = requests.get(url, headers=params, stream=True)
    with open(local_filename, 'wb+') as f:
        shutil.copyfileobj(r.raw, f)


def cleanup():

    file = open("downloadDictionary.txt","r")
    output_file = open("petrarch2/data/dictionaries/online.actors.txt", "w+")
    synonyms =  []
    roles = []
    first_actor = True
    for line in file:
        if line.startswith("+"):
            synonyms.append(line[1:].replace(" ","_").upper())
        elif line.startswith(" "):
            if len(line.strip().split(" "))==2:
                role = line.strip()
                if "-" not in line.strip().split(" ")[1]:
                    role = line.strip().split(" ")[0]+" >"+line.strip().split(" ")[1]
                roles.append(role)
        elif len(line.strip())==0:
            continue
        else:
            if not first_actor:
               if len(roles) > 0 and "TEST1" not in current_actor and "SAYEED2122" not in current_actor:
                   output_file.write(current_actor)
                   for s in synonyms:
                       output_file.write("+"+s+"\n")
                   for r in roles:
                       output_file.write("        "+r+"\n")
               synonyms = []
               roles = []
            first_actor = False
            current_actor = line.upper().replace(" ","_")

    if len(roles) > 0 and "TEST1" not in current_actor:
        output_file.write(current_actor)
        for s in synonyms:
            output_file.write("+" + s+"\n")
        for r in roles:
            output_file.write("        " + r"\n")
    synonyms = []
    roles = []

    file.close()
    output_file.close()

def task():
    print "Updating Dictionary on ", str(datetime.datetime.now()),
    download()
    cleanup()

schedule.every(15).minutes.do(task)

while True:
    schedule.run_pending()
    time.sleep(1)