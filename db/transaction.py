import datetime
from typing import Any, List, Dict

from beanie import Document
from pydantic import Field


class Transaction(Document):
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    hash: str
    fees: int
    confirmed: datetime.datetime
    inputs: List[Dict[str, Any]] = Field(default_factory=list)
    outputs: List[Dict[str, Any]] = Field(default_factory=list)

    class Settings:
        name = "transactions"
