# DSCP TC mapping Test Plan
## 1. Overview
NetScan is used Microsoft for link monitoring and integrity, as well as device health. NetScan runs every second, and if there is a problem with a link (or device), a report is generated.
The NetScan topology includes a probing point (Vantage point on the diagram below), which is a critical infrastructure machine sending out a packet to check if links and end devices are in good health

The Ventage server sends the IPnIP encapsulated packet to the T0 switch which should terminate a packet, decapsulate and then this packet will be sent back to the Vantage server (inner header is already prepared for that)

The DSCP → Traffic Class (or SP - Switch Prio in SDK) is done on ingress and by default not changed after decapsulation

There are 2 modes relevant to DSCP upon IPnIP decapsulation:

- UNIFORM: the outter DSCP is copied into inner DSCP and the Traffic Class obtained on ingress is still relevant and used in the pipeline
- PIPE: the inner DSCP is kept "as is" after decapsulation + a new mapping (inner DSCP → TC) is used for choosing an egress Queue

So far, NV SAI has implemented the PIPE mode without remapping of TC according to the inner DSCP
Microsoft requests to remap the Traffic Class for PIPE mode since they test uses DSCP → TC → Queue for testing different Queues. So, different inner DSCP values set by Vantage server will cause packets to be sent via different TX Queues so testing relevant parameters such as queue lenght, latency, jitter, drops and more
Therefore, this feature shall configure the ASIC to perform the requested remapping

## 2. Assumptions/restrictions
1. This feature is generic and shall be supported for all SKUs
2. Supported on SPC1+
3. Remapping is relevant for IPinIP only and for PIPE DSCP mode only
4. Warm-boot/ISSU shall be supported

## 3. Scope
The test is to verify the outer DSCP(uniform mode) and inner DSCP(pipe mode) mapping to the correct tc and egress queue.
- The DSCP to egress queue mapping is based on the combination of dscp_to_tc_map and tc_to_queue_map
- The validation result is based on the egress queue counter

### 3.1 Scale / Performance
No scale or performance test related.

### 3.2 CLI commands
No dedicate command for this feature, the DSCP to tc mapping relationship should based on "AZURE", it means the PORT_QOS_MAP["global"]["dscp_to_tc_map"] in the config db should be "AZURE".

### 3.3 Supported topology
The test should support t0 and t1 topologies.

## 4. Test cases

| **No.** | **Test Case** | **Test Purpose** |
|----------|-------------------|----------|
| 1 | test_dscp_to_queue_mapping[uniform] | Verify all the outer DSCP mapping to correct egress queue in IPinIP decap.|
| 2 | test_dscp_to_queue_mapping[pipe] | Verify all the inner DSCP mapping to correct egress queue in IPinIP decap.|

### Test case # 1 - test_dscp_to_queue_mapping[uniform]
1. Config DSCP decap mode as __uniform__ at DUT
2. Config IPinIP tunnel as DUT
3. Config global dscp_to_tc_map to __AZURE__
4. Get the dscp_to_tc_map and tc_to_queue_map and generate the map from __outer DSCP__ to egress queue
5. Send a number of ipinip packets with __rotating outer DSCP__
6. Validate all the packets would be received at the correct __egress queue__
7. Make sure the DSCP value would be rotated from 0 to 63
8. Teardown the IPinIP tunnel and recover the DSCP decap mode and global dscp_to_tc_map

### Test case # 2 - test_dscp_to_queue_mapping[pipe]
1. Config DSCP decap mode as __pipe__ at DUT
2. Config IPinIP tunnel as DUT
3. Config global dscp_to_tc_map to __AZURE__
4. Get the dscp_to_tc_map and tc_to_queue_map and generate the map from __inner DSCP__ to egress queue
5. Send a number of ipinip packets with __rotating inner DSCP__
6. Validate all the packets would be received at the correct __egress queue__
7. Make sure the DSCP value would be rotated from 0 to 63
8. Teardown the IPinIP tunnel and recover the DSCP decap mode and global dscp_to_tc_map
