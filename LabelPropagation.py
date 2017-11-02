from Graph import Graph

from random import shuffle

class LabelPropagation:

    num_iters = 20
    graph = None
    num_roles = 3


    def __init__(self, graph, num_iters=20, num_roles=3):
        if not isinstance(graph, Graph):
            raise ValueError("graph should be an instane of Graph class")
        self.graph = graph
        self.num_iters = num_iters
        self.num_roles = num_roles


    def propagate(self, initial_labels={}):

        calculated_labels = {}
        vertices = self.graph.get_vertices()
        for v in vertices:
            calculated_labels[v] = initial_labels.get(v)

        for i in range(0, self.num_iters):
            shuffle(vertices)

            for j in range(0, len(vertices)):
                if vertices[j] in initial_labels: #vertices with FIXED labels
                    continue
                else:
                    neighbours = self.graph.get_neighbours(vertices[j])
                    label_map = {}
                    for neighbour in neighbours:
                        if calculated_labels[neighbour] is None:
                            continue
                        print "Labels Calculated ", calculated_labels[neighbour]
                        for role in calculated_labels[neighbour]:
                            if role in label_map:
                                label_map[role] += neighbours[neighbour]
                            else:
                                label_map[role] = neighbours[neighbour]

                    if label_map:
                        print label_map
                        sorted_label = sorted(label_map.items(), key=lambda x: (-x[1], x[0]))
                        print sorted_label
                        sorted_label = sorted_label[ :self.num_roles]


                        possible_label_list = []
                        for pair in sorted_label:
                            print pair
                            possible_label_list.append(pair[0])

                        calculated_labels[vertices[j]] = possible_label_list


        return calculated_labels
