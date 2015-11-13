#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

class IEEE30BusTopology(Topo):
    def build(self):
        self.pmus = []
        self.pdcs = []
        self.edge_switches = []
        self.core_switches = []
        self.num_pmus = 30
        self.num_switches = 20
        self.num_pdcs = 16

        # pmu hosts
        for i in range(1, self.num_pmus + 1):
            h = self.addHost('pmu%d' % i)
            self.pmus.append(h)

        # pdc switches
        for i in range(1, self.num_pdcs + 1):
            h = self.addHost('pdc%d' % i)
            self.pdcs.append(h)
        for i in range(1, self.num_switches + 1):
            sw = self.addSwitch('s%d' % i)
            if i < 17:
                self.edge_switches.append(sw)
                # link pdc to edge switches
                self.addLink('pdc%i' % i, 's%i' % i)
            else:
                self.core_switches.append(sw)
        # link core switches together
        self.addLink('s17', 's18')
        self.addLink('s17', 's19')
        self.addLink('s17', 's20')
        self.addLink('s18', 's19')
        self.addLink('s18', 's20')
        self.addLink('s19', 's20')

        # link pmu to edge switches
        self.addLink('s1', 'pmu1')
        self.addLink('s1', 'pmu2')
        self.addLink('s1', 'pmu4')
        self.addLink('s2', 'pmu3')
        self.addLink('s3', 'pmu5')
        self.addLink('s3', 'pmu7')
        self.addLink('s4', 'pmu6')
        self.addLink('s4', 'pmu8')
        self.addLink('s5', 'pmu9')
        self.addLink('s5', 'pmu11')
        self.addLink('s6', 'pmu10')
        self.addLink('s6', 'pmu17')
        self.addLink('s6', 'pmu20')
        self.addLink('s6', 'pmu21')
        self.addLink('s7', 'pmu12')
        self.addLink('s7', 'pmu13')
        self.addLink('s7', 'pmu14')
        self.addLink('s8', 'pmu15')
        self.addLink('s8', 'pmu18')
        self.addLink('s8', 'pmu23')
        self.addLink('s9', 'pmu16')
        self.addLink('s10', 'pmu19')
        self.addLink('s11', 'pmu22')
        self.addLink('s12', 'pmu24')
        self.addLink('s13', 'pmu25')
        self.addLink('s13', 'pmu26')
        self.addLink('s14', 'pmu27')
        self.addLink('s14', 'pmu30')
        self.addLink('s15', 'pmu28')
        self.addLink('s16', 'pmu29')

        # link core to edge switches
        for i in range(1, 5):
            self.addLink('s%d' % i, 's17')
        for i in range(5, 9):
            self.addLink('s%d' % i, 's18')
        for i in range(9, 13):
            self.addLink('s%d' % i, 's19')
        for i in range(13, 17):
            self.addLink('s%d' % i, 's20') 

def IEEE30BusNetwork():
    topo = IEEE30BusTopology()
    net = Mininet(topo=topo, host=Host, switch=OVSKernelSwitch, controller=RemoteController, autoStaticArp=True, waitConnected=True)

    net.start()

    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    IEEE30BusNetwork()

