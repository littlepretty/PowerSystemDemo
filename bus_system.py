#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel, info, output
from mininet.link import TCLink, Intf
from subprocess import call
import time
import argparse

class IEEE30BusTopology(Topo):
    """IEEE 39 Bus Power System's communication network topology"""
    def build(self):
        """Overridden to create topology"""
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

def AllPDCPingAllPMU(net, timeout):
    """Ping only from PDC to PMU"""
    output('****** Ping: testing PDC to PMU connectivity ******\n')
    for pdc in net.topo.pdcs:
        PDCPingAllPMU(net, pdc, timeout)

def PDCPingAllPMU(net, pdc, timeout):
    pdc_host = net.getNodeByName(pdc)
    output(' %s -> ' % pdc)
    for pmu in net.topo.pmus:
        pmu_host = net.getNodeByName(pmu)
        opt = '-W %s' % timeout
        result = pdc_host.cmd('ping -c1 %s %s' % (opt,
            pmu_host.IP()))
        outputs = net._parsePingFull(result)
        send, received, rttmin, rttavg, rttmax, rttdev = outputs
        output(('%s ' % pmu) if received else 'X ') 
    output('\n')    

def AllPMUPingAllPDC(net, timeout):
    """Ping only from PMU to PDC"""
    output('****** Ping: testing PMU to PDC connectivity ******\n')
    for pmu in net.topo.pmus:
        PMUPingAllPDC(net, pmu, timeout)

def PMUPingAllPDC(net, pmu, timeout):
    pmu_host = net.getNodeByName(pmu)
    output(' %s -> ' % pmu)
    for pdc in net.topo.pdcs:
        opt = '-c1 -W %s' % timeout
        pdc_host = net.getNodeByName(pdc)
        result = pmu_host.cmd('ping %s %s' % (opt, pdc_host.IP()))
        outputs = net._parsePingFull(result)
        send, received, rttmin, rttavg, rttmax, rttdev = outputs
        output(('%s ' % pdc) if received else 'X ')
    output('\n')    

def IEEE30BusNetwork():
    """Kickoff the network"""
    topo = IEEE30BusTopology()
    net = Mininet(topo=topo, host=Host, switch=OVSKernelSwitch, \
            controller=RemoteController, autoStaticArp=True, waitConnected=True)
    net.start()

    if args.short:
        # test connectivity
        info('****** Quick test for connectivity between PMU and PDC ******\n')
        info('*** Test connection to PDC8 ***\n')
        PMUPingAllPDC(net, 'pmu15', timeout=1)
        # PMUPingAllPDC(net, 'pmu23', timeout=1)
        # info('*** Test connection to PDC13 ***\n)')
        # PMUPingAllPDC(net, 'pmu25', timeout=1)
    else:
        AllPMUPingAllPDC(net, 1)

    # remove 2 pdcs by tear down link
    info("\n****** Tear down link between PDC8 and Switch 8 ******\n")
    info("****** Tear down link between PDC13 and Switch 13 ******\n")
    net.configLinkStatus('pdc8', 's8', 'down')
    net.configLinkStatus('pdc13', 's13', 'down')

    # old pdc should be unreachable
    info('\n****** PDC8 is isolated after being compromised ******\n')
    info('*** Test connection to compromised PDC8 ***\n')
    PMUPingAllPDC(net, 'pmu15', 1)
    # PMUPingAllPDC(net, 'pmu23', 1)
    # info('\n****** PDC13 is isolated after being compromised ******\n')
    # info('*** Test connection to compromised PDC13 ***\n')
    # PMUPingAllPDC(net, 'pmu25', 1)

    raw_input("Press Enter to continue...")
    # test newly installed rules
    time.sleep(3)
    info('\n****** Self-healing controller installed new rules for PMUs ******\n')
    info('*** Test rules installed to connect PMU15 to PDC5 ***\n')
    PMUPingAllPDC(net, 'pmu15', timeout=1)
    info('\n')
    # info('*** Test rules installed to connect PMU23 to PDC5 ***\n')
    # PMUPingAllPDC(net, 'pmu23', timeout=1)
    # info('*** Test rules installed to connect PMU25 to PDC5 ***\n')
    # PMUPingAllPDC(net, 'pmu25', timeout=1)

    CLI(net)
    net.stop()

if __name__ == '__main__':
    """Driver for main"""
    setLogLevel('info')
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--short', action="store_true", \
            default=False, help='Run full ping tests')
    args = parser.parse_args()

    IEEE30BusNetwork()

