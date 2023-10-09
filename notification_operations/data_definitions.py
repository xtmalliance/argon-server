from dataclasses import dataclass
from enum import Enum


class NotificationLevel(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class NotificationMessage:
    """This object will hold messages that will go to the operational Notifications"""

    body: str
    level: NotificationLevel
    timestamp: str
    
    def to_dict(self):
        # Convert the Enum to its string representation
        return {
            "body": self.body,
            "level": self.level.value,
            "timestamp": self.timestamp,
        }
