from __future__ import unicode_literals

import json
import pprint
import re
import sys
import os

import time
import operator

from ClusterManager import ActorResolver
from ClusterSImilarityOLd import FuzzyClusterSimilarity
from Graph import Graph
from LabelPropagation import LabelPropagation
from RoleDictionary import RoleDictionary
from UnionFind import UnionFind
from petrarch2 import PETRglobals
from ActorDictionary import ActorDictionary
reload(sys)
sys.setdefaultencoding('utf8')


graph = Graph()
role_dict = RoleDictionary()

interaction_graph = None
with open('../output/interaction_graph.txt', 'r') as inf:
    interaction_graph = eval(inf.read())
    inf.close()

for name in interaction_graph:
    neighbours = interaction_graph[name]
    
    for n in neighbours:
        graph.add_edge(name, n, neighbours[n])


print "Number of Actors: ", graph.get_numVertices()
print "Number of Interactions: ", graph.get_numEdges()

label_prop = LabelPropagation(graph, num_iters=100)

initial_roles = {}

for v in graph.get_vertices():
    if role_dict.roles(v).get(v) is None:
        continue
    print role_dict.roles(v).get(v)
    initial_roles[v] = list(role_dict.roles(v).get(v))

print '========================='

calculated_roles = label_prop.propagate(initial_roles)

temp_file = open('../output/List_Excluded_Actors')

for line in temp_file:
    if line.strip() in calculated_roles:
        print line.strip(), calculated_roles[line.strip()]
    else:
        print 'No Key for ', line.strip()


with open('../output/interaction_graph_roles.txt', 'w+') as outfile:
    json.dump(calculated_roles, outfile)
    outfile.close()



print "Number of Actors: ", graph.get_numVertices()
print "Number of Interactions: ", graph.get_numEdges()