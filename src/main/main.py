from argparse import ArgumentParser, Namespace
import sys
sys.path.append("/home/ubuntu/Desktop/reroute_experiment/src/")
from route.Graph import Graph, Grpah_util
from route.Type1 import Type1
from route.johnson import type2_johnson
from generator.ini_generator import Route
from generator.ned_generator import Topology


def parse_args() -> Namespace:
    parser = ArgumentParser()

    ### Input arguments
    # 1. network scenario and streams file
    # 2. simulation times (unit: ms)
    # 3. type1 method
    # 4. type2 reservation ratio
    # 5. type2 subtraction constant
    # 6. lambda (for poisson distribution)
    parser.add_argument(
        "--scenario",
        type=str,
        help="(Type: string) Path to file contains network scenario and metadata of streams.",
        required=True
    )
    parser.add_argument(
        "--sim_time",
        type=int,
        help="(Type: int) Simulation times in INET/Omnetpp, in the unit of microsecond.",
        default=2,
    )
    parser.add_argument(
        "--type1_method",
        type=str,
        help="(Type: string) Type1 methods. Choose one of the following methods.\n\t* shortest_path\n\t* least_used_capacity_percentage\n\t* min_max_percentage\n\t* least_conflict_value",
        required=True
    )
    parser.add_argument(
        "--reservation",
        type=float,
        help="(Type: float) Reserve partial of capacity for all edge to avoid run out of bandwidth of network.",
        default=0.0,
    )
    parser.add_argument(
        "--trim",
        type=float,
        help="(Type: float) When ther any new-found cycle, take this constant away from the capacity of all edges in the cycle.\n \
                Default: 0.0, which means the cycle finding alrorithm will return all cycles in the graph.",
        default=0.0,
    )
    parser.add_argument(
        "--lambda",
        type=int,
        help="(Type: float) The lambda in Poisson distribution of the on/off of streams",
        default=0.5,
    )

    ### Output arguments
    # 1. output directory(?)
    # 2. path to ini file
    # 3. path to ned file
    # 4. type1 route(?)
    # 5. type2 route(?)
    parser.add_argument(
        "--ini_file",
        type=str,
        help="(Type: string) Path to the ini generated result.",
        required=True
    )
    parser.add_argument(
        "--ned_file",
        type=str,
        help="(Type: string) Path to the ned generated result.",
        required=True
    )
    parser.add_argument(
        "--map_file",
        type=str,
        help="",
        required=True
    )

    args = parser.parse_args()
    return args

def parse_input_file(input_file_path):
    with open(input_file_path) as input_file:
        # parse number of vertex
        num_vertex = int(input_file.readline().strip())

        # parse graph
        graph = Graph(num_vertex)
        for i in range(num_vertex):
            start_vertex, neighbor_util = input_file.readline().strip().split(",")
            neighbor_util = neighbor_util.split(" ")
            for end_vertex, util in zip(neighbor_util[0::2], neighbor_util[1::2]):
                graph.add_edge(int(start_vertex), int(end_vertex), float(util))

        # parse input to be routed: type1
        M = int(input_file.readline().strip())
        type1 = {}
        for _ in range(M):
            src, des, util = input_file.readline().strip().split(" ")
            type1[int(src), int(des)] = float(util)

        # parse expected utilizations: type2 (util, edge constraint)
        N = int(input_file.readline().strip())
        type2 = {}
        for _ in range(N):
            src, des, util, edge_constraint = input_file.readline().strip().split(" ")
            type2[int(src), int(des)] = (float(util), int(edge_constraint))

        # parse constraint 2: max number of transfer
        num_transfer = int(input_file.readline().strip())

        # init graph visualization
        graph_util = Grpah_util(graph)
        graph_util.initVisualization()

        return graph_util, type1, type2, num_transfer


def main(args):
    ### Parse input file
    graph, type1, type2, num_transfer = parse_input_file(
        args.scenario
    )

    ### Deal with type1
    '''
    # Input:
    #   1. graph            (Graph_util)
    #   2. type1            (List[tuple])
    #   3. type2            (List[tuple])
    # Output:
    #   1. type1_route      (List[tuple])
    '''
    arguments = [args.type1_method]
    if args.type1_method == "least_conflict_value":
        arguments.append(type2)

    type1_route = Type1(graph, type1).solution(*arguments)

    ### Deal with type2
    '''
    # Input:
    #   1. graph            (Graph_util)
    #   2. type1_route      (List[tuple])
    #   3. type2            (List[tuple])
    #   4. trim             (float)
    #   5. reserve          (float)
    # Output:
    #   1. type2_route      (List[int])
    '''
    type2_route = type2_johnson(graph.graph, type2, type1_route, args.reservation, args.trim)

    # Generate input of omnetpp
    '''
    # Input:
    #   1. graph            (Graph_util)
    #   2. type1            (List[tuple])
    #   3. type2            (List[tuple])
    #   4. type1_route      (List[tuple])
    #   5. type2_route      (List[int])
    #   6. sim_time         (int)
    #   7. lambda           (float)
    #   8. ini_file         (string)
    #   9. ned_file         (string)
    # Output:
    #   1. ini content
    #   2. ned content
    '''
    
    T = Topology()
    T.fromFile(args.scenario)
    T.genNed(args.ned_file)

    R = Route(T)
    R.parseRouting(type1_route, type2_route)
    # print(f"type1 routing : \n{R.type1_route}\ntype2 routing: \n{R.type2_route}")
    R.parseStream()
    R.genINI(args.ini_file, args.map_file)
    

if __name__ == "__main__":
    args = parse_args()
    main(args)
