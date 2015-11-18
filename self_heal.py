# Copyright (C) 2016 IIT
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
from ryu.lib.packet import ipv4, icmp, arp
from ryu.topology import event
from ryu.topology.api import get_switch, get_link

class SelfHealController(app_manager.RyuApp):
    """
    SelfHeal controller based on ryu's simple switch
    """
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SelfHealController, self).__init__(*args, **kwargs)
        
        # monitor the topology changes
        self.topology_api_app = self

        #store sw's dpid(int)
        self.switches = []

        # store the port number from sw to sw
        self.links = {}

        # store the port number from sw to host
        self.sw_to_host = {}
        for i in range(1, 17):
            self.sw_to_host[i] = {'10.0.0.%d' % i : 1}
        # initial path for edge switches
        self.sw_to_host[1]['10.0.0.17'] = 2
        self.sw_to_host[1]['10.0.0.18'] = 3
        self.sw_to_host[1]['10.0.0.20'] = 4
        self.sw_to_host[2]['10.0.0.19'] = 2
        self.sw_to_host[3]['10.0.0.21'] = 2
        self.sw_to_host[3]['10.0.0.23'] = 3
        self.sw_to_host[4]['10.0.0.22'] = 2
        self.sw_to_host[4]['10.0.0.24'] = 3
        self.sw_to_host[5]['10.0.0.25'] = 2
        self.sw_to_host[5]['10.0.0.27'] = 3
        self.sw_to_host[6]['10.0.0.26'] = 2
        self.sw_to_host[6]['10.0.0.33'] = 3
        self.sw_to_host[6]['10.0.0.36'] = 4
        self.sw_to_host[6]['10.0.0.37'] = 5
        self.sw_to_host[7]['10.0.0.28'] = 2
        self.sw_to_host[7]['10.0.0.29'] = 3
        self.sw_to_host[7]['10.0.0.30'] = 4
        self.sw_to_host[8]['10.0.0.31'] = 2
        self.sw_to_host[8]['10.0.0.34'] = 3
        self.sw_to_host[8]['10.0.0.39'] = 4
        self.sw_to_host[9]['10.0.0.32'] = 2
        self.sw_to_host[10]['10.0.0.35'] = 2
        self.sw_to_host[11]['10.0.0.38'] = 2
        self.sw_to_host[12]['10.0.0.40'] = 2
        self.sw_to_host[13]['10.0.0.41'] = 2
        self.sw_to_host[13]['10.0.0.42'] = 3
        self.sw_to_host[14]['10.0.0.43'] = 2
        self.sw_to_host[14]['10.0.0.46'] = 3
        self.sw_to_host[15]['10.0.0.44'] = 2
        self.sw_to_host[16]['10.0.0.45'] = 2
        self.sw_to_host[17] = {}
        self.sw_to_host[18] = {}
        self.sw_to_host[19] = {}
        self.sw_to_host[20] = {}

    def add_flow(self, datapath, in_port, dst, actions):
        """
        Issue FlowMod message to switch @datapath, tell it that
        pkt to @dst should be send to @in_port. @actions should
        be list of PacketOutput actions(usually just one element)
        """
        ofproto = datapath.ofproto

        match = datapath.ofproto_parser.OFPMatch(
                in_port=in_port, dl_dst=haddr_to_bin(dst))

        mod = datapath.ofproto_parser.OFPFlowMod(
            datapath=datapath, match=match, cookie=0,
            command=ofproto.OFPFC_ADD, idle_timeout=0, hard_timeout=0,
            priority=ofproto.OFP_DEFAULT_PRIORITY,
            flags=ofproto.OFPFF_SEND_FLOW_REM, actions=actions)
        datapath.send_msg(mod)

    @set_ev_cls(event.EventSwitchEnter)
    def _get_topology_data(self, ev):
        """
        Automatically create sw to sw port table
        e.g. @self.links. Notice that @ev is not used at all
        """
        self.logger.info("Updating port map between switches")
        switch_list = get_switch(self.topology_api_app, None)
        for sw in switch_list:
            if sw.dp.id not in self.switches:
                self.switches.append(sw.dp.id)

        link_list = get_link(self.topology_api_app, None)
        for link in link_list:
            if link.src.dpid not in self.links.keys():
                self.links[link.src.dpid] = {}
            self.links[link.src.dpid][link.dst.dpid] = link.src.port_no
        print self.links

    @set_ev_cls(event.EventPortModify)
    def _link_delete_handler(self, ev):
        """
        React to link down event
        """
        port = ev.port
        dpid = port.dpid
        # port_no = port.port_no
        # event_name = port.name
        print "Self-healing port event of s%d" % dpid
        
        # make sure controller has global view
        self._get_topology_data(None)

        if port.is_down() and dpid == 8:
            # path for pmu15(10.0.0.31) to pdc5(10.0.0.5)
            self.sw_to_host[5]['10.0.0.31'] = self.links[5][18]
            self.sw_to_host[18]['10.0.0.31'] = self.links[18][8]
            self.sw_to_host[8]['10.0.0.5'] = self.links[8][18]
            self.sw_to_host[18]['10.0.0.5'] = self.links[18][5]
            # path for pmu23(10.0.0.39) to pdc5(10.0.0.5)
            self.sw_to_host[5]['10.0.0.39'] = self.links[5][18]
            self.sw_to_host[18]['10.0.0.39'] = self.links[18][8]
            self.sw_to_host[8]['10.0.0.5'] = self.links[8][18]
            self.sw_to_host[18]['10.0.0.5'] = self.links[18][5]
        if port.is_down() and dpid == 13:
            # path for pmu25(10.0.0.41) to pdc5(10.0.0.5)
            self.sw_to_host[5]['10.0.0.41'] = self.links[5][18]
            self.sw_to_host[18]['10.0.0.41'] = self.links[18][20]
            self.sw_to_host[20]['10.0.0.41'] = self.links[20][13]
            self.sw_to_host[13]['10.0.0.5'] = self.links[13][20]
            self.sw_to_host[20]['10.0.0.5'] = self.links[20][18]
            self.sw_to_host[18]['10.0.0.5'] = self.links[18][5]

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Ping(ICMP) packet handler
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        dpid = datapath.id

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        
        # ignore lldp packet
        if pkt_eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        pkt_icmp = pkt.get_protocol(icmp.icmp)
        eth_dst = pkt_eth.dst
        eth_src = pkt_eth.src
        self.logger.info("packet in %s(port_%s) from %s to %s", dpid, msg.in_port, eth_src, eth_dst)
        
        if pkt_icmp:
            pkt_ip = pkt.get_protocol(ipv4.ipv4)
            # ip_src = str(pkt_ip.src)
            ip_dst = str(pkt_ip.dst)
            # find path to dst host
            if ip_dst in self.sw_to_host[dpid].keys():
                out_port = self.sw_to_host[dpid][ip_dst]
                self.logger.info("forward to port %s", out_port)
                # install a flow to avoid packet_in next time
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, msg.in_port, eth_dst, actions)
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                out = datapath.ofproto_parser.OFPPacketOut(
                    datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port,
                    actions=actions, data=data)
                datapath.send_msg(out)
        else:
            pkt_arp = pkt.get_protocol(arp.arp)
            if pkt_arp:
                self.logger.info("should flood ARP pkt")
            else:
                self.logger.info("Unknown type of packet")

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def _port_status_handler(self, ev):
        """
        More general than EventPortModify?
        """
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
