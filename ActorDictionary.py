import re

from ClusterSImilarity import FuzzyClusterSimilarity

from petrarch2 import  PETRglobals
class ActorDictionary:

    file_part_name = ""
    actor_filenames= ['Phoenix.Countries.actors'+file_part_name+'.txt',
                      'Phoenix.International.actors'+file_part_name+'.txt',
                      'Phoenix.MilNonState.actors'+file_part_name+'.txt']
    folder = 'data/dictionaries'

    actor_set = set()

    actor_map = {}


    fcs = FuzzyClusterSimilarity()

    THERSHOLD = 0.75

    def __init__(self):
        for filename in self.actor_filenames:
            fs = open(self.folder + "/" + filename)
            root_name = ""
            update = False

            for line in fs:
                line = line.strip()
                if line.startswith('#') or len(line) == 0:  # if it is a comment
                    continue
                line = line.split('#')[0]
                if not line.startswith('+'):
                    update = True
                line = re.sub(r'\[[^\]]*\]', '', line).replace('_', ' ').replace('+', '').strip()
                #print line
                if len(line) > 1:
                    self.actor_set.add(line)
                    if update:
                        update = False
                        root_name = line
                        self.actor_map[line] = line
                    else:
                        self.actor_map[line] = root_name
            fs.close()

    def contains(self, actorname):
        test = actorname.replace('_',' ').strip()
        return test in self.actor_set


    def getRootName(self, other_name=""):
        return self.actor_map[other_name]





