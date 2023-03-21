import sys
sys.path.append("/home/ubuntu/Desktop/reroute_experiment/src/")
from route.Graph import Graph

from collections import defaultdict
from copy import copy
import enum
from platform import node
import sys
import copy
from typing import List
import pickle
from argparse import ArgumentParser, Namespace
import os

total_cycle_length = 0

def subGraph(G: Graph, nodeList: List[int]) -> Graph:
    g = Graph(G.num_vertex)
    g.capacity = copy.deepcopy(G.capacity)

    for u in nodeList:
        for v in nodeList:
            if u != v and G.capacity[(u, v)] > 0:
                g.add_edge(u, v, G.capacity[(u, v)])
    return g

#=======================================#
#   Below are for tarjan scc finding    #
#=======================================#
class SCC():
    def __init__(self, graph: Graph):
        self.graph = graph
        
        self.Time = 0
        self.low_val = [-1] * graph.num_vertex
        self.discover_time = [-1] * graph.num_vertex
        self.stack = []
        
        # output
        self.SCCs = []

        self.tarjan()
        
    def dfs(self, node):
        self.low_val[node] = node
        self.discover_time[node] = self.Time
        self.Time += 1
        self.stack.append(node)
        
        for neighbor in self.graph.edges[node]:
            if self.discover_time[neighbor] < 0:
                self.dfs(neighbor)
                self.low_val[node] = min(self.low_val[node], self.low_val[neighbor])
            elif neighbor in self.stack: # neighbor is the ancestor of node
                self.low_val[node] = min(self.low_val[node], self.discover_time[neighbor])
        
        if self.low_val[node] == self.discover_time[node]: # Found SCC which contains {node}
            scc = []
            v = -1
            while v != node:
                v = self.stack.pop()
                scc.append(v)
            self.SCCs.append(sorted(scc))
        
    def tarjan(self):
        for node in list(self.graph.edges.keys()):
            if self.discover_time[node] < 0:
                self.dfs(node)
            
#===================================#
#   Below are for circuit finding   #
#===================================#
class Johnson():
    def __init__(self, graph: Graph, constant: float, reserve: float, streams=None, warmup=False):
        self.ori_graph = graph
        self.graph = graph
        self.reduceConstant = constant
        self.reservation = reserve
        self.streams = streams
        
        
        self.S = 0
        self.V = graph.num_vertex
        self.stack = []
        self.blocked = [False] * self.graph.num_vertex
        self.B = [[] for i in range(self.graph.num_vertex)]
        self.count = 0
        self.allCircuits = []
        self.included = [False] * self.graph.num_vertex

        self.FOUND = False
        
        # Find the circuits
        if warmup:
            self.warmupProcedure()
        self.circuitFinding()
        
    def output(self, INFO="Nan", reduceConst=0):
        global total_cycle_length
        # print("[Circuit No.{}]".format(self.count))
        # print("circuit length : {}".format((self.stack)))
        self.count += 1
        self.allCircuits.append(copy.deepcopy(self.stack))
        self.allCircuits[-1].append(self.stack[0])

        circuitLen = len(self.stack)
        total_cycle_length += circuitLen
        print(f"[{INFO}] ", end="")
        for i in range(circuitLen):
            print("{} -->".format(self.stack[i]), end="")
            self.included[self.stack[i]] = True
            self.graph.capacity[(self.stack[i], self.stack[(i+1)%circuitLen])] -= reduceConst
        print(self.stack[0])

    def unblock(self, u):
        self.blocked[u] = False
        while len(self.B[u]) > 0:
            w = self.B[u].pop()
            if self.blocked[w]:
                self.unblock(w)
        return 
        
    def circuit(self, v):
        # print(" circuit : ",c v, self.blocked, self.stack)
        f = False
        self.stack.append(v)
        self.blocked[v] = True

        for w in self.graph.edges[v]:
            if self.FOUND:
                return True
            if self.graph.capacity[(v, w)] >= self.reduceConstant + self.reservation:
                if w == self.S:
                    if self.stack + [self.stack[0]] not in self.allCircuits:
                        self.output(INFO="circuit", reduceConst=self.reduceConstant)
                        self.FOUND = True
                    f = True
                elif not self.blocked[w]:
                    if self.circuit(w):
                        f = True
        
        if f:
            self.unblock(v)
        else:
            for w in self.graph.edges[v]:
                if v not in self.B[w]:
                    self.B[w].append(v)
        
        self.stack.pop()
        return f

    def Normalcircuit(self, v):
        f = False
        self.stack.append(v)
        self.blocked[v] = True

        for w in self.graph.edges[v]:
            if self.graph.capacity[(v, w)] >= self.reduceConstant +  self.reservation:
                if w == self.S:
                    self.output(INFO="normal")
                    f = True
                elif not self.blocked[w]:
                    if self.Normalcircuit(w):
                        f = True
        
        if f:
            self.unblock(v)
        else:
            for w in self.graph.edges[v]:
                if v not in self.B[w]:
                    self.B[w].append(v)
        
        self.stack.pop()
        return f


    def circuitFinding(self):
        print("circuitFINDING!!!!!!!!!!!!!!!")
        nodeList = [node for node in range(self.graph.num_vertex)]
        
        while self.S < self.V :
            self.graph = subGraph(self.ori_graph, nodeList)
            sccs = SCC(self.graph).SCCs
            # print(f"sccs : {sccs}")

            if len(sccs) > 0:
                self.S = min(sccs[0])

                if self.reduceConstant == 0:
                    self.stack = []
                    for i in range(self.S, self.V):
                        self.blocked[i] = False
                        self.B[i] = []
                    dummy = self.Normalcircuit(self.S)
                else:
                    self.FOUND = True
                    while self.FOUND:
                        self.FOUND = False
                        self.stack = []
                        for i in range(self.S, self.V):
                            self.blocked[i] = False
                            self.B[i] = []
                        dummy = self.circuit(self.S)
                self.S += 1
                nodeList = nodeList[self.S:]
            else:
                self.S = self.V
        return 
    
    def warmupProcedure(self):
        if self.streams is None:
            print("[Error] warmup need the information of type2 streams.")
            os.exit()

        self.S = 0
        self.stack = []
        for i in range(self.S, self.V):
            self.blocked[i] = False
            self.B[i] = []
        dummy = self.Normalcircuit(0)
        if len(self.allCircuits) > 0: # Exist cycle with source self.S
            # sort all circuit by the length
            self.allCircuits = sorted(self.allCircuits, key=lambda c: len(c), reverse=True)
            if len(self.allCircuits[0]) > len(self.allCircuits[1]): # Single Maximum
                self.stack = copy.deepcopy(self.allCircuits[0][:-1])
            elif len(self.allCircuits[0]) == self.V: # multiple maximum and Exist at least one cycle covering all nodes
                # select the one that has minimum sum of shortest path for type2 stream
                min_sum_shortest_path = self.V * len(self.streams)
                min_idx = 0
                for i, c in enumerate(self.allCircuits):
                    if len(c) < self.V:
                        break
                    sum_shortest_path = 0
                    for s in self.streams:
                        s_id = c.index(s[0])
                        d_id = c.index(s[1])
                        dis = self.V + d_id - s_id if s_id > d_id else d_id - s_id
                        sum_shortest_path += dis
                    if sum_shortest_path < min_sum_shortest_path:
                        min_sum_shortest_path = sum_shortest_path
                        min_idx = i
                self.stack = copy.deepcopy(self.allCircuits[min_idx][:-1])
            else: # multiple maximum and all cycles with source self.S fail to cover all nodes
                max_num_cover_stream = 0
                min_sum_shortest_path = self.V * len(self.streams)
                best_idx = 0 
                for i, c in enumerate(self.allCircuits):
                    num_cover_stream = 0
                    sum_shortest_path = 0
                    for s in self.streams:
                        if s[0] in c and s[1] in c:
                            num_cover_stream += 1
                            s_id = c.index(s[0])
                            d_id = c.index(s[1])
                            dis = len(c) - 1 + d_id - s_id if s_id > d_id else d_id - s_id
                            sum_shortest_path += dis
                    if num_cover_stream > max_num_cover_stream:
                        max_num_cover_stream = num_cover_stream
                        min_sum_shortest_path = sum_shortest_path
                        best_idx = i
                    elif num_cover_stream == max_num_cover_stream and sum_shortest_path < min_sum_shortest_path:
                        min_sum_shortest_path = sum_shortest_path
                        best_idx = i
                self.stack = copy.deepcopy(self.allCircuits[best_idx][:-1])
            self.allCircuits = []
            self.output(INFO="warmup", reduceConst=self.reduceConstant)
        return
    
def cycleSelection(vertex_num: int, cycles: List[List[int]]):
    result = cycles[0]
    unCover = set([v for v in range(vertex_num) if v not in result])
    selected = set([0])

    while unCover and len(list(selected)) < vertex_num:
        print(unCover)
        coverMost_idx = -1
        coverMost_num = -1
        for i, c in enumerate(cycles):
            if i == 0 or i in selected:
                continue
            num_cover = len(list(unCover & set(c)))
            print(f"{unCover} & {c} num : {num_cover}")
            if num_cover >= coverMost_num:
                coverMost_idx = i
                coverMost_num = num_cover
        if coverMost_num <= 0:
            break
        common_node = list(set(cycles[coverMost_idx]) & set(result))[0]
        unCover = unCover - set(cycles[coverMost_idx])
        selected.update([coverMost_idx])
        # print(common_node)
        print(result, "\n", cycles[coverMost_idx])
        print(f"{result[:result.index(common_node)]} {cycles[coverMost_idx][cycles[coverMost_idx].index(common_node):]} {cycles[coverMost_idx][1:cycles[coverMost_idx].index(common_node)]} {result[result.index(common_node) : ]}")
        
        result_ = result[:-1]
        select_cycle = cycles[coverMost_idx][:-1]
        result = result_[:result_.index(common_node) + 1] + \
            select_cycle[select_cycle.index(common_node)+1:] + \
                select_cycle[1:select_cycle.index(common_node)] + \
                    result_[result_.index(common_node) : ] + [result[0]]
        # print(result)
    return result

'''
This is the entry function of type2.
'''
def type2_johnson(graph: Graph, type2: List[tuple], type1_route: List[tuple], reserve: float, trim: float) -> List[int]:
    ### Take away the capacity occupied by type1 streams
    for r in type1_route:
        for i in range(len(r[0]) - 1):
            graph.capacity[(r[0][i], r[0][i+1])] -= float(-r[1]/2)

    ### Start routing
    johnson_result = Johnson(graph, trim, reserve, streams=type2, warmup=True)
    cycles = sorted(johnson_result.allCircuits, key=lambda c: len(c), reverse=True)
    route = cycleSelection(graph.num_vertex, cycles)

    return route
    
