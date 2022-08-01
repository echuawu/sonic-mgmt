from .PollingTool import PollingTool
from .RandomizationTool import RandomizationTool
from .SendCommandTool import SendCommandTool
from .OutputParsingTool import OutputParsingTool
from .TrafficGeneratorTool import TrafficGeneratorTool
from .ValidationTool import ValidationTool
from .IpTool import IpTool
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool


class Tools:
    PollingTool = PollingTool()
    RandomizationTool = RandomizationTool()
    SendCommandTool = SendCommandTool()
    OutputParsingTool = OutputParsingTool()
    TrafficGeneratorTool = TrafficGeneratorTool()
    ValidationTool = ValidationTool()
    IpTool = IpTool()
    OpenSmTool = OpenSmTool()
