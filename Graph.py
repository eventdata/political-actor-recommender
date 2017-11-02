

class Graph:

    adj_list = {}

    num_edges = 0

    num_vertices = 0




    def add_edge(self, u, v, weight=1):
        self.add_vertex(u)
        self.add_vertex(v)

        self.adj_list[u][v] = weight
        self.adj_list[v][u] = weight
        self.num_edges += 1


    def add_vertex(self, u):
        if u not in self.adj_list:
            self.adj_list[u] = {}
            self.num_vertices += 1
            return True
        return False

    def get_vertices(self):
        return self.adj_list.keys()

    def get_neighbours(self, u):
        if u in self.adj_list:
            return self.adj_list[u]
        else:
            raise ValueError("The vertex is not in the graph")

    def get_numVertices(self):
        return self.num_vertices

    def get_numEdges(self):
        return self.num_edges

    def __str__(self):
        return str(self.adj_list)

    # def __repr__(self):
    #     return self.__str__()


