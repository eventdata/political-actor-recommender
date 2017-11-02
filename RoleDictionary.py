import re

from ClusterSImilarity import FuzzyClusterSimilarity
import pprint

class RoleDictionary:

    file_part_name = ""
    actor_filenames= ['Phoenix.Countries.actors'+file_part_name+'.txt',
                      'Phoenix.International.actors'+file_part_name+'.txt',
                      'Phoenix.MilNonState.actors'+file_part_name+'.txt']
    folder = '../petrarch2/data/dictionaries'



    actor_roles = {}

    similarityMeasure = FuzzyClusterSimilarity()

    def actors(self):
        return self.actor_roles.keys()

    def __init__(self, similarityMeasure=FuzzyClusterSimilarity()):
        self.similarityMeasure = similarityMeasure
        for filename in self.actor_filenames:
            fs = open(self.folder + "/" + filename)
            current_roles = set()
            current_actors = []
            for line in fs:
                line = line.strip()
                if line.startswith('#') or len(line.strip()) == 0:  # if it is a comment
                    continue
                line = line.split('#')[0]
                words = line.strip().split("\t")
                for i in range(0, len(words)):
                    w = words[i].strip()
                    if not w.startswith('+') and not w.strip().startswith('['):
                        #print "NEW ACTOR ", current_actors
                        for actor in current_actors:
                            if actor in self.actor_roles:
                                self.actor_roles[actor].union(current_roles)
                            else:
                                self.actor_roles[actor] = current_roles
                            #self.actor_roles[actor] = current_roles
                        current_actors = []
                        current_roles = set()
                        current_actors.append(w.replace('_',' ').strip())
                    elif w.startswith('+'):
                        #line.replace()
                        current_actors.append(w.replace('+','').replace("_"," ").strip())
                    else:
                        matched = re.match(r'\[[^\]]*\]',w)
                        role_with_date = matched.group(0)
                        current_roles.add(role_with_date[1:len(role_with_date)-1].split(' ')[0])
                        #print current_roles

            fs.close()

            #pprint.pprint( self.actor_roles)

    def roles(self, actorname):
        temp = actorname.replace('_',' ').strip()
        # maxKey = None
        # maxMatch = 100
        # for key in self.actor_roles:
        #     match = self.similarityMeasure.measure(key, temp)
        #     if match > maxMatch:
        #         maxKey = key
        #         maxMatch = match

        return {actorname: self.actor_roles.get(temp)}

print 'Running'

roleDict = RoleDictionary()

print "initialized"

#roleDict.contains('test')

print roleDict.roles('BARACK_OBAMA')


# country_codes = set()
#
# cc_file = open("country_codes.txt", "r")
#
# for line in cc_file:
#     country_codes.add(line.strip())
#
# organizational_roles = set()
#
# for actor in roleDict.actors():
#     roles = roleDict.roles(actor)
#     for role in roles[actor]:
#         if role[:3] in country_codes:
#             organizational_roles.add(role[3:])
#         else:
#             organizational_roles.add(role)
#
#
# print organizational_roles
#
# print len(organizational_roles)



