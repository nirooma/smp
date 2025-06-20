import datetime
import re
from typing import Any

from beanie import Document
from pydantic import Field

BTC_ADDRESS_RE: re.Pattern[str] = re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$")


class Address(Document):
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    address: str
    balance: int
    transaction_count: int

    class Settings:
        name = "addresses"

    @staticmethod
    async def count_address_transactions(transactions: list[dict[str, Any]], confirmed_transactions=True) -> int:
        if len(transactions) == 0:
            return 0

        if not confirmed_transactions:
            return len(transactions)

        counter = 0
        for transaction in transactions:
            if transaction.get("confirmed"):
                counter += 1

        return counter

    @staticmethod
    async def btc_address_is_valid(btc_address: str) -> bool:
        return True if BTC_ADDRESS_RE.fullmatch(btc_address) else False

