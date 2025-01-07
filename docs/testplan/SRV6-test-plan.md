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
| uDT46 | Endpoint decapsulation and specific IP lookup |

### Scope
The test is to verify the functions in SRv6 phase I.

### Scale
Max number of MY_SID entries is 10, it would be covered in this test plan.

### CLI command
No SRv6 CLI command involved in this test plan.

### Supported Topology
The test will be supported on t0 and t1 topology.

## Test Cases
### Test Case # 1 SRv6 function test
1. Configure SRV6_MY_SIDS with uN and uDT46 action at the same time for different SIDs <br>
  a. Configure half of SRV6_MY_SIDS for uDT46 as __uniform__ mode <br>
  b. Configure the other half of SRV6_MY_SIDS for uDT46 as __pipe__ mode <br>
3. Send IPv6 packets from downstream to upstream neighbors <br>
  a. Including IPv6 packets with reduced SRH(no SRH header) for uN action <br>
  b. Including IPv6 packets with 1 uSID container in SRH for uN action <br>
  c. Including IPv6 packets with 2 uSID container in SRH for uN action <br>
  d. Including IPinIPv6 packets with uSIDs container in SRH for uDT46 action <br>
  e. Including IPv6inIPv6 packets with uSID container in SRH for uDT46 action <br>
4. All types of IPv6 packets should be handled correctly <br>
  a. For uN action, DIP shift/ uSID container copy to DIP/ segment left decrement should happen <br>
  b. For uDT46 action, IP tunnel decap should happen <br>
6. Randomly choose one action from warm-reboot/fast-reboot/cold reboot/config reload and do it
7. Resend the all types of IPv6 packets
8. All types of IPv6 packets should be handled correctly <br>
  a. For uN action, DIP shift/ uSID container copy to DIP/ segment left decrement should happen <br>
  b. For uDT46 action, IP tunnel decap should happen <br>

### Test Case # 2 SRv6 function with lag member operation
1. Configure SRV6_MY_SIDS with uN and uDT46 action at the same time for different SIDs <br>
  a. Configure half of SRV6_MY_SIDS for uDT46 as __uniform__ mode <br>
  b. Configure the other half of SRV6_MY_SIDS for uDT46 as __pipe__ mode <br>
2. Send IPv6 packets from downstream to upstream neighbors <br>
  a. Including IPv6 packets with reduced SRH(no SRH header) for uN action <br>
  b. Including IPv6 packets with 1 uSID container in SRH for uN action <br>
  c. Including IPv6 packets with 2 uSID container in SRH for uN action <br>
  d. Including IPinIPv6 packets with uSIDs container in SRH for uDT46 action <br>
  e. Including IPv6inIPv6 packets with uSID container in SRH for uDT46 action <br>
4. All types of IPv6 packets should be handled correctly <br>
  a. For uN action, DIP shift/ uSID container copy to DIP/ segment left decrement should happen <br>
  b. For uDT46 action, IP tunnel decap should happen <br>
5. Delete lag member and add lag member back
6. Resend the all types of IPv6 packets
7. All types of IPv6 packets should be handled correctly <br>
  a. For uN action, DIP shift/ uSID container copy to DIP/ segment left decrement should happen <br>
  b. For uDT46 action, IP tunnel decap should happen <br>
8. Flap lag member
9. Resend the all types of IPv6 packets
10. All types of IPv6 packets should be handled correctly <br>
  a. For uN action, DIP shift/ uSID container copy to DIP/ segment left decrement should happen <br>
  b. For uDT46 action, IP tunnel decap should happen <br>

### Test Case # 3 SRv6 configuration in techsupport
1. Configure SRV6_MY_SIDS with uN and uDT46 action at the same time for different SIDs <br>
  a. Configure half of SRV6_MY_SIDS for uDT46 as __uniform__ mode <br>
  b. Configure the other half of SRV6_MY_SIDS for uDT46 as __pipe__ mode <br>
2. Collect techsupport dump files
3. SRv6 related configuration should be revealed in dump files
