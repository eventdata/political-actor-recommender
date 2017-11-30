import json
from ActorUpdate import ActorUpdate


new_actor_file = open("SampleOutput.txt", "r")
data_uploader = ActorUpdate()

for line in new_actor_file:

    actor_name = line.split(":")[0].strip()
    roles_list =
    roles = line.split(":")[1].strip()

    roles_sorted = sorted(roles.items(), key= lambda x: x[1])[-4:]


    role_list = [x[0] for x in roles_sorted]

    print actor_name, role_list


    #res = data_uploader.actorUpload(actor_name, [], role_list )

    #print res







