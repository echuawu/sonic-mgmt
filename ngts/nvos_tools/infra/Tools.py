from .PollingTool import PollingTool
from .RandomizationTool import RandomizationTool
from .SendCommandTool import SendCommandTool
from .OutputParsingTool import OutputParsingTool
from .TrafficGeneratorTool import TrafficGeneratorTool
from .ValidationTool import ValidationTool
from .IpTool import IpTool
from .ConfigTool import ConfigTool
from .SonicMgmtContainer import SonicMgmtContainer
from .ClockTestTools import ClockTestTools


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
    ClockTestTools = ClockTestTools()
