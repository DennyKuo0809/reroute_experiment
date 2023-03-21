# import enum
# import ned_generator
# import sys
import pickle

header = "[General]\n"
header += "network = TSN_multipath\n"
header += "sim-time-limit = 2ms\n"
#############################################################
#   disable automatic MAC forwarding table configuration    #
#############################################################
header += "\n"
header += "# disable automatic MAC forwarding table configuration\n"
header += "*.macForwardingTableConfigurator.typename = \"\"\n"

#################################################
#   enable frame replication and elimination    #
#################################################
header += "\n"
header += "# enable frame replication and elimination\n"
header += "*.*.hasStreamRedundancy = true\n"

#########################################
#   enable stream policing in layer 2   #
#########################################
header += "\n"
header += "# enable stream policing in layer 2\n"
header += "*.*.bridging.streamRelay.typename = \"StreamRelayLayer\"\n"
header += "*.*.bridging.streamCoder.typename = \"StreamCoderLayer\"\n"

#####################################################
#   enable automatic stream redundancy configurator #
#####################################################
header += "\n"
header += "# enable automatic stream redundancy configurator\n"
header += "*.streamRedundancyConfigurator.typename = \"StreamRedundancyConfigurator\"\n"

#################
#   visualizer  #
#################
header += "\n"
header += "# visualizer\n"
header += "*.visualizer.streamRedundancyConfigurationVisualizer.displayTrees = true\n"
header += "*.visualizer.streamRedundancyConfigurationVisualizer.lineColor = \"black\"\n"

#####################################
#   bitrate  of network interface   #
#####################################
header += "\n"
# header += "*.*.eth[*].bitrate = 100Mbps\n"

import math
from enum import Enum
import random

class Stream_switch():
    def __init__(self, Lambda=0.5, period=100):
        self.Lambda = Lambda
        self.period = period

    def poisson_reverse(self, probability):
        return -math.log(1 - probability) / self.Lambda

    def on_off_schedule(self, sim_time=2000):
        t = 0
        on = False
        schedule = []

        index = 0

        while t < sim_time // self.period:
            r = random.random()
            if on:
                if r <= self.Lambda:
                    ### Turn off
                    on = False
                    schedule[index][1] = t
                    index += 1
                    # print(f"Turn off on time {t}")
                    # print(schedule, "\n")
                else:
                    ### Keep on
                    t += 1
            else: # off
                interval = max(int(self.poisson_reverse(r)), 0)
                if t + interval >= sim_time // self.period:
                    break
                if interval > 0 or len(schedule) == 0:
                    schedule.append([t + interval, -1])
                else:
                    index -= 1

                # print("poisson result ", self.poisson_reverse(r), " \n")
                # print(f"Turn on on time {t + interval}")
                # print(schedule, "\n")
                t = t + interval + 1
                on = True
        if on:
            schedule[index][1] = sim_time // self.period
        return schedule
    
class Route():
    def __init__(self, T):
        self.topology = T
        self.app = [[] for _ in range(T.host_num)]
        self.port = [1000 for _ in range(T.host_num)]
        self.type1_route = []
        self.type2_route = []

        self.poisson = Stream_switch()

    def parseStream(self):
        for id, (src, dst, util) in enumerate(self.topology.type1):
            new_src_app = {
                "role": "send", 
                "destport": self.port[dst],
                "dst": self.topology.hosts[dst].name,
                "util": util,
                "type": int(1),
                "flow-id" : int(id),
            }
            self.app[src].append(new_src_app)

            new_dst_app = {
                "role": "recv", 
                "localport": self.port[dst],
                "type": int(1),
                "flow-id" : int(id),
            }
            self.port[dst] += 1
            self.app[dst].append(new_dst_app)

        for id, (src, dst, util, _) in enumerate(self.topology.type2):
            poisson_schedule = self.poisson.on_off_schedule()
            for interval in poisson_schedule:
                new_src_app = {
                    "role": "send", 
                    "destport": self.port[dst],
                    "dst": self.topology.hosts[dst].name,
                    "util": util,
                    "type": int(2),
                    "flow-id" : int(id),
                    "start": interval[0] * 100,
                    "stop": interval[1] * 100
                }
                self.app[src].append(new_src_app)
            new_dst_app = {
                "role": "recv", 
                "localport": self.port[dst],
                "type": int(2),
                "flow-id" : int(id),
            }
            self.port[dst] += 1
            self.app[dst].append(new_dst_app)

    def parseRouting(self, type1_route, type2_cycle):
        self.type1_route = [r[0] for r in type1_route]
        
        for (src, dst, _, _) in self.topology.type2:
            ls = [i for i, n in enumerate(type2_cycle) if n == src]
            ld = [i for i, n in enumerate(type2_cycle) if n == dst]
            
            min_dis = self.topology.host_num * 2
            s_idx = -1
            d_idx = -1
            for i in ld:
                for j in ls:
                    if j < i:
                        if i - j < min_dis:
                            min_dis = i - j
                            s_idx = j
                            d_idx = i
                    elif j > i:
                        if i + len(type2_cycle) - j - 1 < min_dis:
                            min_dis = i + len(type2_cycle) - j - 1
                            s_idx = j
                            d_idx = i
            if d_idx > s_idx:
                self.type2_route.append(type2_cycle[s_idx:d_idx+1])
            else:
                self.type2_route.append(type2_cycle[s_idx:] + type2_cycle[1: d_idx+1])

        return 
    def genINI(self, outFile, mapping_file):
        mapping_buf = ""
        with open(outFile, "w") as out_f:
            #############
            #   Header  #
            #############
            print(header, end="", file=out_f)

            ###############
            #   Bit rate  #
            ###############
            # *.*.eth[*].bitrate = 100Mbps\n
            for device in self.topology.hosts:
                for i, br in enumerate(device.host_gates_bitrate):
                    print(f"*.{device.name}.eth[{i}].bitrate = {int(10 * br)}Mbps", file=out_f)
                for i, br in enumerate(device.switch_gates_bitrate):
                    print(f"*.{device.switch_name}.eth[{i}].bitrate = {int(10 * br)}Mbps", file=out_f)
            #####################################
            #   Source App  & Destination App   #
            #####################################
            print("# apps", end="", file=out_f)
            for i in range(self.topology.host_num):
                name = self.topology.hosts[i].name
                num = len(self.app[i])
                print(f"\n*.{name}.numApps = {num}\n", end="", file=out_f)

                for j, app in enumerate(self.app[i]):
                    buf = "\n"
                    if app['role'] == "send":
                        if app['type'] == 1:
                            buf += f"*.{name}.app[{j}].typename = \"UdpSourceApp\"\n"
                            buf += f"*.{name}.app[{j}].destAddresses = \"{app['dst']}\"\n"
                            buf += f"*.{name}.app[{j}].source.packetNameFormat = \"%M-%m-%c\"\n"
                            buf += f"*.{name}.app[{j}].source.displayStringTextFormat = \"sent %p pk (%l)\"\n"
                            buf += f"*.{name}.app[{j}].source.packetLength = {int(500*app['util'])}B\n"
                            buf += f"*.{name}.app[{j}].source.productionInterval = 100us\n"
                            buf += f"*.{name}.app[{j}].display-name = \"type{app['type']}_{app['flow-id']}\"\n"
                            buf += f"*.{name}.app[{j}].io.destPort = {app['destport']}\n"
                        elif app['type'] == 2:
                            buf += f"*.{name}.app[{j}].typename = \"UdpBasicApp\"\n"
                            buf += f"*.{name}.app[{j}].destAddresses = \"{app['dst']}\"\n"
                            buf += f"*.{name}.app[{j}].source.packetNameFormat = \"%M-%m-%c\"\n"
                            buf += f"*.{name}.app[{j}].source.displayStringTextFormat = \"sent %p pk (%l)\"\n"
                            buf += f"*.{name}.app[{j}].messageLength = {int(500*app['util'])}B\n"
                            buf += f"*.{name}.app[{j}].sendInterval = 100us\n"
                            buf += f"*.{name}.app[{j}].startTime = {app['start']}us\n"
                            buf += f"*.{name}.app[{j}].stopTime = {app['stop']}us\n"
                            buf += f"*.{name}.app[{j}].display-name = \"type{app['type']}_{app['flow-id']}\"\n"
                            buf += f"*.{name}.app[{j}].destPort = {app['destport']}\n"
                    else:
                        buf += f"*.{name}.app[{j}].typename = \"UdpSinkApp\"\n"
                        buf += f"*.{name}.app[{j}].io.localPort = {app['localport']}\n"

                        mapping_buf += f"\'{name}.app[{j}]\' : \'type{app['type']}-flow{app['flow-id']}\',\n"
                    print(buf, end="", file=out_f)

            #####################
            #   Routing Path    #
            #####################

            print("\n# seamless stream redundancy configuration", file=out_f)
            print("*.streamRedundancyConfigurator.configuration = [\n", end="", file=out_f)
            for i, p in enumerate(self.type1_route):
                buf = "\t{"
                buf += f"name: \"S1-{i}\", packetFilter: \"*-type1_{i}-*\", source: \"{self.topology.hosts[p[0]].name}\", destination: \"{self.topology.hosts[p[-1]].name}\","
                buf += f"trees: [[[\"{self.topology.hosts[p[0]].name}\", \"{self.topology.hosts[p[0]].switch_name}\""
                for j in p[1:-1]:
                    buf += f", \"{self.topology.hosts[j].switch_name}\""
                buf += f", \"{self.topology.hosts[p[-1]].switch_name}\", \"{self.topology.hosts[p[-1]].name}\"]]]"
                buf += "},"
                print(buf, file=out_f)
            for i, p in enumerate(self.type2_route):
                buf = "\t{"
                buf += f"name: \"S2-{i}\", packetFilter: \"*-type2_{i}-*\", source: \"{self.topology.hosts[p[0]].name}\", destination: \"{self.topology.hosts[p[-1]].name}\","
                buf += f"trees: [[[\"{self.topology.hosts[p[0]].name}\", \"{self.topology.hosts[p[0]].switch_name}\""
                for j in p[1:-1]:
                    buf += f", \"{self.topology.hosts[j].switch_name}\""
                buf += f",\"{self.topology.hosts[p[-1]].switch_name}\" ,\"{self.topology.hosts[p[-1]].name}\"]]]"
                if i == len(self.type2_route)-1:
                    buf += "}]"
                else:
                    buf += "},"
                print(buf, file=out_f)

            with open(mapping_file, 'w') as map_f:
                print(mapping_buf, end="", file=map_f)
            '''
            *.streamRedundancyConfigurator.configuration = [{name: "S1", packetFilter: "*-app1-*", source: "source", destination: "destination",
                                                    trees: [[["source", "s1", "s2a", "s3a", "destination"]]]},
            {name: "S2", packetFilter: "*-app0-*", source: "source", destination: "destination",
                                                    trees: [[["source", "s1", "s2b", "s3b", "destination"]]]}]
            '''


