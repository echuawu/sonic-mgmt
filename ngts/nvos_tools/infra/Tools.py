from .PollingTool import PollingTool
from .RandomizationTool import RandomizationTool
from .SendCommandTool import SendCommandTool
from .OutputParsingTool import OutputParsingTool
from .TrafficGeneratorTool import TrafficGeneratorTool
from .ValidationTool import ValidationTool
from .IpTool import IpTool
from .ConfigTool import ConfigTool
from .SonicMgmtContainer import SonicMgmtContainer
from .HostMethods import HostMethods
from .RedisTool import RedisTool


class Tools:
    PollingTool = PollingTool()
    RandomizationTool = RandomizationTool()
    SendCommandTool = SendCommandTool()
    OutputParsingTool = OutputParsingTool()
    TrafficGeneratorTool = TrafficGeneratorTool()
    ValidationTool = ValidationTool()
    IpTool = IpTool()
    ConfigTool = ConfigTool()
    SonicMgmtContainer = SonicMgmtContainer()
    HostMethods = HostMethods()
    RedisTool = RedisTool()
