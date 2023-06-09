import copy
import numpy as np
import sys


def delete_same_cycle(cycles):
    # convert to string
    cycles = ["".join(map(str, c)) for c in cycles]

    # remove dulplicates & rotate
    cycles = sorted((set(cycles)))  # list

    for c in cycles:
        for shift in range(1, len(c)):
            if c[shift:] + c[:shift] in cycles:
                cycles.remove(c[shift:] + c[:shift])

    cycles = [list(map(int, list(c))) for c in cycles]
    return cycles


def merge_two_cycles(cycle1, cycle2):
    if cycle1 == cycle2:
        return []
    if len(set(cycle1) & set(cycle2)) == 0:
        # no transfer
        return []

    m = []
    for transfer_vertex in list(set(cycle1) & set(cycle2)):

        # cut cycle2 at intersection
        for i in list(np.where(np.array(cycle2) == transfer_vertex)[0]):
            # no need add intersection
            cut_cycle2 = cycle2[i:] + cycle2[:i]

            # cut cycle1 at intersection
            for j in list(np.where(np.array(cycle1) == transfer_vertex)[0]):
                new_cycle = copy.deepcopy(cycle1)
                new_cycle[j:j] = cut_cycle2
                # pop one intersection
                # a = [0, 1, 2]
                # b = [4, 5, 6]
                # a[0:0] = b
                # print(a) #[4, 5, 6, 0, 1, 2]

                m.append(new_cycle)

    m = delete_same_cycle(m)
    return m


def generate_transfer_cycle(cycles, num_transfer):
    original_cycles = copy.deepcopy(cycles)

    # init
    to_be_merged = copy.deepcopy(cycles)

    # transfer : merge = 1 : 1
    for _ in range(num_transfer):
        merged_cycles = []
        for cycle1 in to_be_merged:
            for cycle2 in original_cycles:
                merged_cycles.extend(merge_two_cycles(cycle1, cycle2))

        merged_cycles = delete_same_cycle(merged_cycles)
        cycles.extend(merged_cycles)
        to_be_merged = merged_cycles

    cycles = delete_same_cycle(cycles)
    return cycles
