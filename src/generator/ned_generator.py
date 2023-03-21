
ned_header = "package inet.tutorials.demo_test;\n"
ned_header += "import inet.networks.base.TsnNetworkBase;\n"
ned_header += "import inet.node.ethernet.EthernetLink;\n"
ned_header += "import inet.node.tsn.TsnDevice;\n"
ned_header += "import inet.node.tsn.TsnSwitch;\n"
ned_header += "\n"
ned_header += "module LocalTsnSwitch extends TsnSwitch\n"
ned_header += "{\n"
ned_header += "\t@defaultStatistic(\"gateStateChanged:vector\"; module=\"eth[0].macLayer.queue.gate[0]\");\n"
ned_header += "}\n"
ned_header += "network TSN_multipath extends TsnNetworkBase\n"
ned_header += "{\n"


class Tsn_Device():
    def __init__(self, name="", switch_name = ""):
        # There always is a switch for amy device (host)
        self.name = name 
        self.switch_name = switch_name
        self.host_gates_bitrate = []
        self.switch_gates_bitrate = []


class Link():
    def __init__(self, src, dst, cap):
        self.src = src
        self.dst = dst
        self.cap = cap
        
class Topology():
    def __init__(self):
        self.input_file = ""
        self.output_file = ""

        self.host_num = 0
        self.edge_num = 0
        self.hosts = []
        self.edges = []

        self.type1_num = 0
        self.type2_num = 0
        self.type1 = []
        self.type2 = []

        self.trans_num = 0
        

    def fromFile(self, file_name):
        self.input_file = file_name
        with open(file_name, "r") as input_file:
            # parse number of vertex
            self.host_num = int(input_file.readline().strip())

            # parse graph
            for i in range(self.host_num):
                self.hosts.append(Tsn_Device("host" + str(i), "switch" + str(i)))

                src, capcity = input_file.readline().strip().split(",")
                capcity = capcity.split(" ")
                for dst, cap in zip(capcity[0::2], capcity[1::2]):
                    self.edges.append(Link(int(src), int(dst), float(cap)))

            # parse input to be routed: type1
            self.type1_num = int(input_file.readline().strip())
            for _ in range(self.type1_num):
                src, dst, util = input_file.readline().strip().split(" ")
                self.type1.append((int(src), int(dst), float(util)))

            # parse expected utilizations: type2 (util, edge constraint)
            self.type2_num = int(input_file.readline().strip())
            for _ in range(self.type2_num):
                src, dst, util, edge_constraint = input_file.readline().strip().split(" ")
                self.type2.append((int(src), int(dst), float(util), int(edge_constraint)))

            # parse constraint 2: max number of transfer
            self.trans_num = int(input_file.readline().strip())

    def genNed(self, file_name):
        # if file_name were not specified, output the result to stdout
        with open(file_name, "w") as out_f:
            # header
            print(ned_header, file=out_f)

            # submodule (host & switch)
            print("\tsubmodules:\n", file=out_f)
            for device in self.hosts:
                submodule = "\t\t{}".format(device.name)
                submodule += ": TsnDevice {\n"
                submodule += "\t\t\t@display(\"p=300,200\");\n"
                submodule += "\t\t}\n"
                submodule += "\t\t{}".format(device.switch_name)
                submodule += ": LocalTsnSwitch {\n"
                submodule += "\t\t\t@display(\"p=300,200\");\n" 
                submodule += "\t\t}\n"
                print(submodule, file=out_f)

            # connection (edge)
            print("\tconnections:\n", file=out_f)
            for device in self.hosts:
                print("\t\t{}.ethg++ <--> EthernetLink <--> {}.ethg++;".format(device.name, device.switch_name), file=out_f)
                device.host_gates_bitrate.append(10)
                device.switch_gates_bitrate.append(10)

            for edge in self.edges:
                print("\t\t{}.ethg++ <--> EthernetLink <--> {}.ethg++;".format(self.hosts[edge.src].switch_name, self.hosts[edge.dst].switch_name), file=out_f)
                self.hosts[edge.src].switch_gates_bitrate.append(edge.cap)
                self.hosts[edge.dst].switch_gates_bitrate.append(edge.cap)

            # end
            print("}", file=out_f)

if __name__ == "__main__":
    T = Topology()
    import sys
    T.fromFile(sys.argv[1])
    T.genNed(sys.argv[2])
