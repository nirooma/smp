import datetime

from blockcypher import get_transaction_details, get_address_full
from fastapi import APIRouter, status, Request, HTTPException
from loguru import logger
from starlette.responses import JSONResponse

from core.settings import settings
from db.address import Address
from db.redis import is_rate_limited
from db.transaction import Transaction

router = APIRouter()


@router.get("/ping")
async def health_check():
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "environment": settings.environment,
        "mongodb_uri": settings.MONGODB_URI,
        "redis_uri": settings.REDIS_URI,
    }


@router.get("/address/{bitcoin_address}", status_code=status.HTTP_200_OK, response_model=Address)
async def index(bitcoin_address: str, req: Request):
    """
    Retrieve current balance and confirmed-transaction count for a Bitcoin address.

    ## Request:
    - Path parameter **`bitcoin_address`** – a legacy (P2PKH/P2SH) or Bech32 address
      (26-42 characters).
      If the format fails a basic regex check, the endpoint immediately returns
      **`400 Bad Request`**.

    ## Behavior:
    - Validate the address format.
    - **Cache lookup** in MongoDB (Beanie):
        - If a record exists and the external API call later fails,
          the cached document is returned (graceful degradation).
    - **External fetch** (`get_address_full`) to obtain live data:
        - On network/API error → fall back to the cached record (if any).
        - If neither the API nor the DB has data → return **`404 Not Found`**.
    - When the external fetch succeeds:
        - Count confirmed transactions in the payload.
        - If the address already exists in the DB and the confirmed-transaction
          count has increased, update the cached document in-place; otherwise
          insert a new record.
        - Return the up-to-date `Address` document.

    ## Responses:
    - `200 OK`: `Address` data (cached or freshly updated).
    - `400 Bad Request`: Invalid address format.
    - `404 Not Found`: Address not found in either the external source or the DB.
    """

    # Validate Bitcoin address format using a static utility method from Address class.
    # If invalid, return a 400 error immediately.
    if not await Address.btc_address_is_valid(bitcoin_address):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid Bitcoin address format"},
        )

    # Attempt to find a cached Address document in MongoDB
    address: Address | None = await Address.find_one(
        Address.address == bitcoin_address
    )

    try:
        if await is_rate_limited(req.url.path):
            logger.error("rate limiter hits - request aborted")

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "too many requests"}
            )
        # Attempt to fetch the latest data from the external blockchain API
        payload = get_address_full(address=bitcoin_address)
    except Exception as e:
        # If the API call fails, log the full traceback for debugging
        logger.error(f"failed to fetch data from api - rolling back to db. Returning the latest record \n\n ({e})")

        # Fallback to DB cache if available
        if address:
            return address

        # If not found in DB either, return 404 error
        logger.warning(f"Record not found in db - address record {bitcoin_address!r} not found")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Address {bitcoin_address!r} not found in DB or external source"}
        )

    # Log how many transactions were returned by the external API
    logger.info(f"Found {len(payload.get('txs'))} total transaction for address {bitcoin_address!r}")

    # Count only the confirmed transactions in the payload
    payload_transactions_count: int = await Address.count_address_transactions(
        payload.get('txs', []),
        confirmed_transactions=True
    )

    # If the address already exists in the DB...
    if address:
        # ...and the confirmed transaction count has increased
        if address.transaction_count < payload_transactions_count:
            logger.info(
                f"Updating the address record {bitcoin_address!r} with {payload_transactions_count} total transactions")

            # Update the existing DB record with the new balance and tx count
            await address.set(
                {
                    Address.balance: payload.get("balance", -1),
                    Address.transaction_count: payload_transactions_count,
                }
            )
            # Re-fetch the updated document to ensure consistency
            address = await Address.get(address.id)

        # Return the cached or updated document
        logger.info("Returning cached address record")
        return address

    # If the address is not in the DB, create a new Address document
    address = Address(
        address=bitcoin_address,
        balance=payload.get("balance"),
        transaction_count=payload_transactions_count
    )
    logger.info(f"Inserting new address record {bitcoin_address!r}")

    # Insert the new address into MongoDB
    await address.insert()

    # Return the newly inserted document
    return address


@router.get("/transaction/{transaction_hash}", status_code=status.HTTP_200_OK, response_model=Transaction)
async def index(transaction_hash: str, req: Request):
    """
    Retrieve a blockchain transaction by hash.

    ## Request:
    - Expect a `TransactionRequest` with a `transaction_hash` field (64-character string).

    ## Behavior:
    - If the hash is not exactly 64 characters, returns `400 Bad Request`.
    - If the transaction already exists in the database (cache hit), returns it.
    - If the transaction does not exist (cache miss):
        - Calls an external API (`get_transaction_details`) to fetch transaction data.
        - If an error is returned from the API, returns `400 Bad Request`.
        - If successful, stores the transaction in the database and returns it.

    ## Responses:
    - `200 OK`: Transaction data (from cache or API).
    - `400 Bad Request`: Invalid hash or API error.
    """

    # Validate hash length
    if len(transaction_hash) != 64:
        logger.error(f"hash {transaction_hash!r} is invalid - needs to be 64 chars")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "hash length not valid - accepting only 64 chars as hash"}
        )

    # Try to find the transaction in DB
    transaction = await Transaction.find_one(Transaction.hash == transaction_hash)

    if transaction:
        logger.info("Cache hits - fetching transaction from db")
        return transaction

    if await is_rate_limited(req.url.path):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": "too many requests"}
        )

    logger.info("Cache miss - calling api to fetch data")

    try:
        # Fetch from an external source
        payload = get_transaction_details(transaction_hash)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": str(e)}
        )

    # Handle errors from the external API
    if e := payload.get("error"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": e}
        )

    # Create a new transaction document and insert it
    transaction = Transaction(**payload)
    await transaction.insert()

    return transaction
