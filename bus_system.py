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

import time
import argparse
import subprocess
import os

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
            h = self.addHost('PMU%d' % i)
            self.pmus.append(h)

        # pdc switches
        for i in range(1, self.num_pdcs + 1):
            h = self.addHost('PDC%d' % i)
            self.pdcs.append(h)
        for i in range(1, self.num_switches + 1):
            sw = self.addSwitch('s%d' % i)
            if i < 17:
                self.edge_switches.append(sw)
                # link pdc to edge switches
                self.addLink('PDC%i' % i, 's%i' % i)
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
        self.addLink('s1', 'PMU1')
        self.addLink('s1', 'PMU2')
        self.addLink('s1', 'PMU4')
        self.addLink('s2', 'PMU3')
        self.addLink('s3', 'PMU5')
        self.addLink('s3', 'PMU7')
        self.addLink('s4', 'PMU6')
        self.addLink('s4', 'PMU8')
        self.addLink('s5', 'PMU9')
        self.addLink('s5', 'PMU11')
        self.addLink('s6', 'PMU10')
        self.addLink('s6', 'PMU17')
        self.addLink('s6', 'PMU20')
        self.addLink('s6', 'PMU21')
        self.addLink('s7', 'PMU12')
        self.addLink('s7', 'PMU13')
        self.addLink('s7', 'PMU14')
        self.addLink('s8', 'PMU15')
        self.addLink('s8', 'PMU18')
        self.addLink('s8', 'PMU23')
        self.addLink('s9', 'PMU16')
        self.addLink('s10', 'PMU19')
        self.addLink('s11', 'PMU22')
        self.addLink('s12', 'PMU24')
        self.addLink('s13', 'PMU25')
        self.addLink('s13', 'PMU26')
        self.addLink('s14', 'PMU27')
        self.addLink('s14', 'PMU30')
        self.addLink('s15', 'PMU28')
        self.addLink('s16', 'PMU29')

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
    time.sleep(5)

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
    time.sleep(5)

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


def PMUPingPDC(net, pmu, pdc, timeout):
    time.sleep(5)
    pmu_host = net.getNodeByName(pmu)
    pdc_host = net.getNodeByName(pdc)
    output('%s(%s) ping -c1 %s(%s)' % (pmu, pmu_host.IP(), pdc, pdc_host.IP()))
    result = pmu_host.cmd('ping -W %d -c1 %s' % (timeout, pdc_host.IP()))
    output(result)

def DumpRule(net, sw_name):
    sw = net.getNodeByName(sw_name)
    info('Dump OpenFlow rules on %s\n' % sw)
    os.system("ovs-ofctl dump-flows %s" % sw_name)
    time.sleep(5)

def IEEE30BusNetwork():
    """Kickoff the network"""
    topo = IEEE30BusTopology()
    net = Mininet(topo=topo, host=Host, switch=OVSKernelSwitch, \
            controller=RemoteController, autoStaticArp=True, waitConnected=True)
    net.start()
    changed_sw = ['s5', 's8', 's13', 's18', 's20']

    if args.short:
        # test connectivity
        info('****** Quick test for connectivity between PMU and PDC ******\n')
        info('*** PING Test from PMU15 PMU23 and PMU25 ***\n')
        # PMUPingPDC(net, 'PMU15', 'PDC8', 1)
        # PMUPingPDC(net, 'PMU9', 'PDC5', 1)
        PMUPingAllPDC(net, 'PMU15', timeout=1)
        PMUPingAllPDC(net, 'PMU23', timeout=1) 
        PMUPingAllPDC(net, 'PMU25', timeout=1)
    else:
        AllPMUPingAllPDC(net, 1)
   
    info('\n****** Show rules on critical switches ******\n')
    for sw in changed_sw:
        DumpRule(net, sw)
    
    # remove 2 pdcs by tear down link
    # info("\n****** Tear down link between PDC8 and Switch 8 ******\n")
    # info("****** Tear down link between PDC13 and Switch 13 ******\n")
    net.configLinkStatus('PDC8', 's8', 'down')
    net.configLinkStatus('PDC13', 's13', 'down')

    # old pdc should be unreachable
    info('\n****** PDC8 is isolated after being compromised ******\n')
    info('*** PING Test from PMU15 PMU23 ***\n') 
    # PMUPingPDC(net, 'PMU15', 'PDC8', 1)
    PMUPingAllPDC(net, 'PMU15', 1)
    PMUPingAllPDC(net, 'PMU23', 1)
    info('\n****** PDC13 is isolated after being compromised ******\n')
    info('*** PING Test from PMU25 ***\n')
    PMUPingAllPDC(net, 'PMU25', 1)

    raw_input("\n****** Self-heal controller installed new rules to reconnect PMUs ******\n")
    # test newly installed rules 
    info('*** Test rules installed to connect PMU15 to PDC5 ***\n')
    # PMUPingPDC(net, 'PMU15', 'PDC5', 1)
    PMUPingAllPDC(net, 'PMU15', timeout=1)
    info('*** Test rules installed to connect PMU23 to PDC5 ***\n')
    PMUPingAllPDC(net, 'PMU23', timeout=1)
    info('*** Test rules installed to connect PMU25 to PDC5 ***\n')
    PMUPingAllPDC(net, 'PMU25', timeout=1)
    
    info('\n****** Show rules on critical switches ******\n')
    for sw in changed_sw:
        DumpRule(net, sw)

    if not args.short:
        AllPMUPingAllPDC(net, 1)

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

