import json
from ActorUpdate import ActorUpdate


new_actor_file = open("SampleOutput.txt", "r")
data_uploader = ActorUpdate()

for line in new_actor_file:

    actor_name = line.split(":")[0].strip()
    roles = eval(line.split(":")[1].strip())

    role_list = []
    for role, count in roles:
        role_list.append(role)

    print actor_name, role_list


    res = data_uploader.actorUpload(actor_name, [], role_list )

    print res







