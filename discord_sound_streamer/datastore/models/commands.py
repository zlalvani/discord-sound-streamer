from dataclasses import dataclass
from datetime import datetime

from hikari import Snowflake


@dataclass
class LastCommandValue:
    executed_at: datetime
    channel_id: Snowflake
