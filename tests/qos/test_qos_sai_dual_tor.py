from test_qos_sai import *


class TestQosSaiDualTor(TestQosSai):
    """TestQosSaiDualTor derives from TestQosSai and contains collection of QoS SAI test cases.

    Note:
        This test file is used as a wrapper to run the dual tor qos test for the 'Mellanox-SN4600C-C64'
        testQosSaiPfcXoffLimit, testQosSaiPfcXonLimit, testQosSaiHeadroomPoolSize and testQosSaiDscpQueueMapping will
        be executed for the Dual tor qos test. to run these tests, need to specify the --qos_dual_tor=True in pytest cmd
    """
