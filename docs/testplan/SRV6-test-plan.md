## Overview
Segment Routing IPv6 (SRv6) is a next-generation IP bearer protocol that combines Segment Routing (SR) and IPv6. 
Utilizing existing IPv6 forwarding technology, SRv6 implements network programming through flexible IPv6 extension 
headers. SRv6 reduces the number of required protocol types, offers great extensibility and programmability, 
and meets the diversified requirements of more new services.

In SRv6 networks the packet format is a standard IPv6 packet format with additional options inside. SRv6 networks have 4 different types of the nodes: <br>
__originating node__ - a node that converts standard IP packet to SRv6 packet by doing IPinIP encapsulation when external IP is according SRv6 format <br>
__consumption node__ - last node in SRv6 chain. This node decapsulates the packet and forwards decapsulated packet as a standard IP packet or consumes it locally <br>
__SRv6 aware node__ - a node that identifies external IP encapsulation as SRv6 encapsulation and can process it according SRv6 rules <br>
__traditional IPv6 node__ - a node that identifies SRv6 encapsulated packet as a standard IPv6 packet and does standard LPM based IPv6 routing <br>

## Definition/Abbreviation
### Table 1: Abbreviations

| ****Term**** | ****Meaning**** |
| -------- | ----------------------------------------- |
| SRv6 | Segment Routing IPv6  |
| SID  | Segment Identifier  |
| SRH  | Segment Routing Header  |
| uSID | Micro Segment |
| uN   | SRv6 instantiation of a prefix SID |
| USD | Ultimate Segment Decapsulation |


### Scope
The test is to verify the functions in SRv6 phase I and II.

### Scale
Max number of MY_SID entries is 10, it would be covered in this test plan.

### CLI command
No SRv6 configure CLI command involved in this test plan. The SRv6 static configuration method had been described in https://github.com/sonic-net/SONiC/pull/1860. <br>
There are SRv6 counter and CRM commands supported.
| ****Command**** | ****Detail**** |
| -------- | ----------------------------------------- |
| counterpoll srv6 enable | Enable SRv6 counter query |
| counterpoll srv6 disable | Disable SRv6 counter query |
| counterpoll srv6 interval 100 ~ 30000 | Set SRv6 counter query interval, the unit is milliseconds |
| sonic-clear srv6counters | Clear srv6 counter |
| show srv6 stats | show srv6 counter |
| crm show resources srv6-my-sid-entry | show srv6 used and avaiable sid resource |

### Supported Topology
The test will be supported on t0 and t1 topology.

## Test Cases
### Test Case # 1 SRv6 dataplane full function test
1. Configure SRV6_MY_SIDS with uN action at the same time for different SIDs <br>
  a. Configure all of the SRV6_MY_SIDS as __pipe__ mode <br>
2. Validate correct SRv6 CRM resource items had been used
3. Clear srv6 counter <br>
4. Send IPv6 packets from downstream to upstream neighbors <br>
  a. Including IPv6 packets with reduced SRH(no SRH header) for uN action <br>
  b. Including IPv6 packets with 1 uSID container in SRH for uN action <br>
  c. Including IPv6 packets with 2 uSID container in SRH for uN action <br>
  d. Including IPinIPv6 packets with reduced SRH(no SRH header) and uSID container in SRH for USD flavor<br>
  e. Including IPv6inIPv6 packets with reduced SRH(no SRH header) and uSID container in SRH for USD flavor <br>
5. All types of IPv6 packets should be handled correctly <br>
  a. For uN action, DIP shift/ uSID container copy to DIP/ segment left decrement should happen <br>
  b. For uN action USD flavor, IP tunnel decap should happen <br>
  c. For each SID, the SRv6 counter for packet number and size should be updated correctly
6. Randomly choose one action from cold reboot/config reload and do it
7. Resend the all types of IPv6 packets
8. All types of IPv6 packets should be handled correctly <br>
  a. For uN action, DIP shift/ uSID container copy to DIP/ segment left decrement should happen <br>
  b. For uN action USD flavor, IP tunnel decap should happen <br>
  c. For each SID, the SRv6 counter for packet number and size should be updated correctly
9. Remove all the configured SRV6_MY_SIDS <br>
10. Check all the SRv6 CRM resource had been released <br>

### Test Case # 2 SRv6 configuration in techsupport
1. Configure SRV6_MY_SIDS with uN action at the same time for different SIDs <br>
  a. Configure all of the SRV6_MY_SIDS as __pipe__ mode <br>
2. Collect techsupport dump files
3. SRv6 related configuration should be revealed in dump files
