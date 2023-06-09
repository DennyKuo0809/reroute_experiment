import collections
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from . import utils


class Graph():
    def __init__(self, num_vertex):
        self.num_vertex = num_vertex
        self.vertices = list(range(num_vertex))  # [0, 1, ... ]
        self.edges = collections.defaultdict(list)  # default dict of []
        self.capacity = collections.defaultdict(float)  # edges[(u, v)] = 0

    def add_edge(self, u, v, c):
        self.edges[u].append(v)
        self.capacity[(u, v)] = c
        return

class Grpah_util():
    def __init__(self, graph):
        self.graph = graph

    def initVisualization(self):
        self.nxG = nx.DiGraph()
        self.nxG.add_nodes_from(self.graph.vertices)
        self.nxG.add_weighted_edges_from([(*n, w)
                                          for n, w in list(self.graph.capacity.items())])
        self.pos = nx.spring_layout(self.nxG)  # pos variable

    def visualizeCycle(self, fig_name, cycle):
        # cycle path needed to be converted into the form: [(2, 1), (1, 2)]
        path = [(u, v) for u, v in zip(cycle, cycle[1:])]

        #nx.draw(self.nxG, pos=self.pos, with_labels=True, edgelist=path)
        nx.draw_networkx_nodes(self.nxG, pos=self.pos, alpha=0.3)
        nx.draw_networkx_edges(self.nxG, pos=self.pos, edgelist=path)

        # print all edges' weights
        # edge_weights = nx.get_edge_attributes(self.nxG, 'weight')
        # nx.draw_networkx_edge_labels(
        #     self.nxG, self.pos, edge_labels=edge_weights)
        plt.savefig(fig_name+".pdf")
        plt.clf()
        return

    def printGraph(self):
        for u in self.graph.vertices:
            for v in self.graph.edges[u]:
                print(f"({u} —> {v}, {self.graph.capacity[(u,v)]})", end=' ')
            print()
        return

    def bfs(self, src, des):
        current = [[src]]
        while current:
            path = current.pop(0)
            for neighbor in self.graph.edges[path[-1]]:
                if neighbor == des:
                    yield path+[neighbor]

                if neighbor in path:
                    # no more loop
                    continue
                else:
                    current.append(path+[neighbor])

    def dfs(self, src, des):
        current = [[src]]
        while current:
            path = current.pop()
            for neighbor in self.graph.edges[path[-1]]:
                if neighbor == des:
                    yield path+[neighbor]

                if neighbor in path:
                    # no more loop
                    continue
                else:
                    current.append(path+[neighbor])

    def check_path_enough_capacity(self, path, util):
        for u, v in zip(path, path[1:]):
            if self.graph.capacity[(u, v)] < util:
                return False
        return True

    def take_path(self, path, U):
        for u, v in zip(path, path[1:]):
            self.graph.capacity[(u, v)] = round(self.graph.capacity[(u, v)] - U, 1)
            if self.graph.capacity[(u, v)] == 0:
                self.graph.edges[u].remove(v)
                self.graph.capacity.pop((u, v), None)
        return

    def get_unique_cycles(self):
        # find small cycles
        cycles = [path for node in range(len(self.graph.vertices))
                  for path in self.bfs(node, node)]
        # pop last duplicate vertex
        for c in cycles:
            c.pop()
        cycles = utils.delete_same_cycle(cycles)
        return cycles

    def get_big_cycles(self):
        big_cycles = [path for path in self.bfs(
            0, 0) if len(path) == len(self.graph.vertices)]
        # pop last duplicate vertex
        for c in big_cycles:
            c.pop()
        return big_cycles

    def find_max_cycle_capacity(self, cycle):
        max_capacity = float("inf")
        for u, v in zip(cycle, cycle[1:] + cycle[:1]):
            if self.graph.capacity[(u, v)] < max_capacity:
                max_capacity = self.graph.capacity[(u, v)]
        return max_capacity
