import pickle
import ast
import sys

with open(sys.argv[1], "r") as in_f:
    l = in_f.readlines()
    route = ast.literal_eval(l[1].split(":")[1][1:-1])

    with open(sys.argv[2], "wb") as out_f:
        pickle.dump(route, out_f)
