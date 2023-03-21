package inet.tutorials.demo_test;
import inet.networks.base.TsnNetworkBase;
import inet.node.ethernet.EthernetLink;
import inet.node.tsn.TsnDevice;
import inet.node.tsn.TsnSwitch;

module LocalTsnSwitch extends TsnSwitch
{
	@defaultStatistic("gateStateChanged:vector"; module="eth[0].macLayer.queue.gate[0]");
}
network TSN_multipath extends TsnNetworkBase
{

	submodules:

		host0: TsnDevice {
			@display("p=300,200");
		}
		switch0: LocalTsnSwitch {
			@display("p=300,200");
		}

		host1: TsnDevice {
			@display("p=300,200");
		}
		switch1: LocalTsnSwitch {
			@display("p=300,200");
		}

		host2: TsnDevice {
			@display("p=300,200");
		}
		switch2: LocalTsnSwitch {
			@display("p=300,200");
		}

		host3: TsnDevice {
			@display("p=300,200");
		}
		switch3: LocalTsnSwitch {
			@display("p=300,200");
		}

		host4: TsnDevice {
			@display("p=300,200");
		}
		switch4: LocalTsnSwitch {
			@display("p=300,200");
		}

	connections:

		host0.ethg++ <--> EthernetLink <--> switch0.ethg++;
		host1.ethg++ <--> EthernetLink <--> switch1.ethg++;
		host2.ethg++ <--> EthernetLink <--> switch2.ethg++;
		host3.ethg++ <--> EthernetLink <--> switch3.ethg++;
		host4.ethg++ <--> EthernetLink <--> switch4.ethg++;
		switch0.ethg++ <--> EthernetLink <--> switch1.ethg++;
		switch0.ethg++ <--> EthernetLink <--> switch2.ethg++;
		switch0.ethg++ <--> EthernetLink <--> switch4.ethg++;
		switch1.ethg++ <--> EthernetLink <--> switch0.ethg++;
		switch1.ethg++ <--> EthernetLink <--> switch3.ethg++;
		switch2.ethg++ <--> EthernetLink <--> switch0.ethg++;
		switch2.ethg++ <--> EthernetLink <--> switch1.ethg++;
		switch3.ethg++ <--> EthernetLink <--> switch1.ethg++;
		switch3.ethg++ <--> EthernetLink <--> switch2.ethg++;
		switch4.ethg++ <--> EthernetLink <--> switch1.ethg++;
		switch4.ethg++ <--> EthernetLink <--> switch3.ethg++;
}
