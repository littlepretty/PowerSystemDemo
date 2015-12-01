# Copyright (C) 2016 Jiaqi Yan, IIT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
IEEE 30 Bus Power Network's Self-heal Controller
Based on an OpenFlow 1.0 L2 learning switch implementation.
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import ipv4, icmp
from ryu.topology import event
from ryu.topology.api import get_all_switch, get_all_link, get_all_host

class SelfHealController(app_manager.RyuApp):
    "SelfHeal controller based on ryu's simple switch"
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        """
        Create controller object

        Attributes:
            topology_api_app: monitor the topology changes by
                "ryu-manager --observe-links"
            switches(list of int): store every sw's dpid
            links(2-level dict): store the port number from 
                src sw[level-1 key, (int)dpid] to 
                dst(sw or host)[level-2 key, str(dpid or IP)]
        """
        super(SelfHealController, self).__init__(*args, **kwargs)

        self.topology_api_app = self

        self.dpset = {}
        self.links = {}
        self.sw_addr = {}
        self.h_addr = {}

        # init path from edge sw to PDCs
        for i in range(1, 17):
            self.links[i] = {'10.0.0.%d' % i : 1}
        # initial path from edge sw to PMUs
        self.links[1]['10.0.0.17'] = 2
        self.links[1]['10.0.0.18'] = 3
        self.links[1]['10.0.0.20'] = 4
        self.links[2]['10.0.0.19'] = 2
        self.links[3]['10.0.0.21'] = 2
        self.links[3]['10.0.0.23'] = 3
        self.links[4]['10.0.0.22'] = 2
        self.links[4]['10.0.0.24'] = 3
        self.links[5]['10.0.0.25'] = 2
        self.links[5]['10.0.0.27'] = 3
        self.links[6]['10.0.0.26'] = 2
        self.links[6]['10.0.0.33'] = 3
        self.links[6]['10.0.0.36'] = 4
        self.links[6]['10.0.0.37'] = 5
        self.links[7]['10.0.0.28'] = 2
        self.links[7]['10.0.0.29'] = 3
        self.links[7]['10.0.0.30'] = 4
        self.links[8]['10.0.0.31'] = 2
        self.links[8]['10.0.0.34'] = 3
        self.links[8]['10.0.0.39'] = 4
        self.links[9]['10.0.0.32'] = 2
        self.links[10]['10.0.0.35'] = 2
        self.links[11]['10.0.0.38'] = 2
        self.links[12]['10.0.0.40'] = 2
        self.links[13]['10.0.0.41'] = 2
        self.links[13]['10.0.0.42'] = 3
        self.links[14]['10.0.0.43'] = 2
        self.links[14]['10.0.0.46'] = 3
        self.links[15]['10.0.0.44'] = 2
        self.links[16]['10.0.0.45'] = 2
        self.links[17] = {}
        self.links[18] = {}
        self.links[19] = {}
        self.links[20] = {}

    @set_ev_cls(event.EventSwitchEnter)
    def _handle_switch_enter(self, ev):
        """Automatically create global view"""

        sw_list = get_all_switch(self.topology_api_app)
        host_list = get_all_host(self.topology_api_app)
        link_list = get_all_link(self.topology_api_app)

        # create dpid to datapath mapping        
        for sw in sw_list:
            if sw.dp.id not in self.dpset:
                print 'Enter sw %d' % sw.dp.id
                self.dpset[sw.dp.id] = sw.dp
                for port in sw.ports:
                    print port.hw_addr
        
        for host in host_list:
            print host.ipv4, host.mac

        for link in link_list:
            if link.src.dpid not in self.links:
                self.links[link.src.dpid] = {}
            self.links[link.src.dpid][link.dst.dpid] = link.src.port_no

    def add_path(self, sw_dpid_list, dst, prev_addr_list, next_addr_list):
        """Add rules on sw in sw_dpid_list to create a flow path"""
        for idx, sw_dpid in enumerate(sw_dpid_list):
            datapath = self.dpset[sw_dpid]
            prev_addr = prev_addr_list[idx]
            next_addr = next_addr_list[idx]
            in_port = self.links[sw_dpid][prev_addr]
            out_port = self.links[sw_dpid][next_addr]
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            self.add_flow(datapath, in_port, 'nw_dst', dst, actions, 1)
            self.logger.info('install rule to forward pkt in port_%d on sw%d to port_%d', in_port, datapath.id, out_port)

    @set_ev_cls(event.EventPortModify)
    def _link_delete_handler(self, ev):
        """React to link down event

        @ev: from which we can extract Port object
        """
        port = ev.port
        dpid = port.dpid
        # port_no = port.port_no
        # event_name = port.name

        if port.is_down() and dpid == 13:
            raw_input("Start self-healing by press Enter...")
            # path for pmu15(10.0.0.31) to pdc5(10.0.0.5)
            sw_dpid_list = [8, 18, 5]
            dst = '10.0.0.5'
            prev_addr_list = ['10.0.0.31', '8', '18']
            next_addr_list = ['18', '5', '10.0.0.5']
            self.add_path(sw_dpid_list, dst, prev_addr_list, next_addr_list)

            sw_dpid_list = [5, 18, 8]
            dst = '10.0.0.31'
            prev_addr_list = ['10.0.0.5', '5', '18']
            next_addr_list = ['18', '8', '10.0.0.31']
            self.add_path(sw_dpid_list, dst, prev_addr_list, next_addr_list)

            # path for pmu23(10.0.0.39) to pdc5(10.0.0.5)
            # self.links[5]['10.0.0.39'] = self.links[5][18]
            # self.links[18]['10.0.0.39'] = self.links[18][8]
            # self.links[8]['10.0.0.5'] = self.links[8][18]
            # self.links[18]['10.0.0.5'] = self.links[18][5]

            # # path for pmu25(10.0.0.41) to pdc5(10.0.0.5)
            # self.links[5]['10.0.0.41'] = self.links[5][18]
            # self.links[18]['10.0.0.41'] = self.links[18][20]
            # self.links[20]['10.0.0.41'] = self.links[20][13]
            # self.links[13]['10.0.0.5'] = self.links[13][20]
            # self.links[20]['10.0.0.5'] = self.links[20][18]
            # self.links[18]['10.0.0.5'] = self.links[18][5]

    def add_flow(self, datapath, in_port, dst_type, dst, actions, priority):
        """Issue FlowMod message to switch @datapath

        tell it that pkt to @dst should be send to @in_port.
        @actions: list of PacketOutput actions(usually just one element)
        """
        ofproto = datapath.ofproto
        
        match = None
        if dst_type == 'nw_dst':
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port, nw_dst=dst)
        elif dst_type == 'dl_dst':
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port, dl_dst=haddr_to_bin(dst))
        if not match:
            mod = datapath.ofproto_parser.OFPFlowMod(
                datapath=datapath, match=match, cookie=0,
                command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
                priority=ofproto.priority,
                flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
            datapath.send_msg(mod)
    
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """Ping(ICMP) packet handler"""
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        dpid = datapath.id

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        eth_dst = pkt_eth.dst
        eth_src = pkt_eth.src
        # ignore lldp packet
        if pkt_eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        self.logger.info("packet in %s(port_%s) from %s to %s", dpid, msg.in_port, eth_src, eth_dst)

        pkt_icmp = pkt.get_protocol(icmp.icmp)
        if pkt_icmp:
            pkt_ip = pkt.get_protocol(ipv4.ipv4)
            ip_src = str(pkt_ip.src)
            ip_dst = str(pkt_ip.dst)
            self.logger.info('pkt in sw%s(port_%s) from %s to %s', dpid, msg.in_port, ip_src, ip_dst)
            # find path to dst host
            if ip_dst in self.links[dpid].keys():
                out_port = self.links[dpid][ip_dst]
                self.logger.info("forward to port %s", out_port)
                # install a flow to avoid packet_in next time
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, msg.in_port, 'dl_dst', eth_dst, actions, 0)
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = datapath.ofproto_parser.OFPPacketOut( \
                                datapath=datapath, buffer_id=msg.buffer_id, \
                                in_port=msg.in_port, actions=actions, data=data)
                datapath.send_msg(out)
 
    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        """More general than EventPortModify?"""
        msg = ev.msg
        reason = msg.reason
        port_no = msg.desc.port_no

        ofproto = msg.datapath.ofproto
        if reason == ofproto.OFPPR_ADD:
            self.logger.info("port added %s", port_no)
        elif reason == ofproto.OFPPR_DELETE:
            self.logger.info("port deleted %s", port_no)
        elif reason == ofproto.OFPPR_MODIFY:
            self.logger.info("port modified %s", port_no)
        else:
            self.logger.info("Illeagal port state %s %s", port_no, reason)
