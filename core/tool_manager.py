from enum import Enum, auto


class Tool(Enum):
    NONE = auto()
    PAN = auto()
    SAM = auto()
    MANUAL = auto()
    CALIBRATION = auto()


class ToolManager:

    def __init__(self):

        self.current_tool = Tool.NONE
        self.previous_tool = Tool.NONE

    def activate(self, tool):

        self.previous_tool = self.current_tool
        self.current_tool = tool

    def temporary_pan(self):

        if self.current_tool != Tool.PAN:
            self.previous_tool = self.current_tool

        self.current_tool = Tool.PAN

    def restore_previous(self):

        self.current_tool = self.previous_tool
