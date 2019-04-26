import json
from ActorUpdate import ActorUpdate

folder = "parallel_output_r20_d15/"

new_actor_list = json.load(open(folder+"new_actor_final.txt", "r"))

new_actors_role = json.load(open(folder+"new_actor_role.txt", "r"))



new_actor_list = sorted(new_actor_list, key= lambda x: -x[1])

data_uploader = ActorUpdate()

for (actor_name, window_count) in new_actor_list:

    if window_count < 4:
        break

    roles = new_actors_role[actor_name]

    roles_sorted = sorted(roles.items(), key= lambda x: x[1])[-4:]


    role_list = [x[0] for x in roles_sorted]

    print actor_name, role_list


    res = data_uploader.actorUpload(actor_name, [], role_list )

    print res







