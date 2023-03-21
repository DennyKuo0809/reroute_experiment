import ned_generator
import ini_generator

from argparse import ArgumentParser, Namespace
import pickle

def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--scenario",
        type=str,
        help="Path to input data."
    )
    parser.add_argument(
        "--type1_route",
        type=str,
        help="Path to the pickle file which stores the route of type1 streams",
        default=0.0
    )
    parser.add_argument(
        "--type2_route",
        type=str,
        help="Path to the pickle file which stores the route of type2 streams",
        default=0.0
    )
    parser.add_argument(
        "--ned_output",
        type=str,
        help="Path to the ned generated result.",
        default=0.0
    )
    parser.add_argument(
        "--ini_output",
        type=str,
        help="Path to the ini generated result.",
        default=0.0
    )
    args = parser.parse_args()
    return args

def main(args):
    T = ned_generator.Topology()
    T.fromFile(args.scenario)
    T.genNed(args.ned_output)
    R = ini_generator.Route(T)
    R.parseRouting(args.type1_route, args.type2_route)
    # print(f"type1 routing : \n{R.type1_route}\ntype2 routing: \n{R.type2_route}")
    R.parseStream()
    R.genINI(args.ini_output)

if __name__ == "__main__":
    args = parse_args()
    main(args)