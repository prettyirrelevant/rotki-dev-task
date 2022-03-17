import decimal
import json
import os
import re
import sqlite3
from typing import Any, Dict, List, Tuple

import requests
from eth_utils.address import to_normalized_address
from web3 import HTTPProvider, Web3, exceptions

w3 = Web3(HTTPProvider("https://mainnet.infura.io/v3/1f533c3627fa490cb739d9176e4eb2f5"))
r = requests.Session()


DB_NAME = "rotki-dev-task.db"


def initialise_database() -> None:
    """Sets up the database by first clearing the present if it exists."""
    delete_database()

    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE eth_transaction (
            id INTEGER PRIMARY KEY,
            txnHash TEXT,
            fromAddr TEXT,
            toAddr TEXT,
            txnType TEXT,
            value TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE address (
            id INTEGER PRIMARY KEY,
            address TEXT,
            chain TEXT
        )
        """
    )
    connection.commit()
    cursor.close()


def delete_database() -> None:
    """Deletes an already existing database."""
    if os.path.isfile(DB_NAME):
        os.remove(DB_NAME)


def add_eth_transaction(payload: Dict[str, str]) -> None:
    """Adds an ethereum transaction to the table `eth_transaction`."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO eth_transaction (id, txnHash, fromAddr, toAddr, txnType, value)
        VALUES (NULL, ?, ?, ?, ?, ?)
        """,
        (payload["hash"], payload["from"], payload["to"], payload["tx_type"], payload["value"]),
    )
    connection.commit()
    cursor.close()


def add_address(payload: Dict[str, str]) -> None:
    """Stores an address(either BTC or ETH) to database."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO address (id, address, chain)
        VALUES (NULL, ?, ?)
        """,
        (payload["address"], payload["chain"]),
    )
    connection.commit()
    cursor.close()


def get_addresses_by_chain(chain: str) -> list:
    """Queries the DB to get all addresses based on the blockhain."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    return cursor.execute(
        """
        SELECT * FROM  address
        WHERE chain = ?
        """,
        (chain,),
    ).fetchall()


def fetch_eth_transactions(address: str) -> List[Tuple[Any]]:
    """This function tries to get the transactions from db, otherwise queries Etherscan."""
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    address = to_normalized_address(address)
    result = cursor.execute(
        """
        SELECT * FROM eth_transaction
        WHERE fromAddr = ? OR toAddr = ?
        """,
        (address, address),
    ).fetchall()

    if len(result) == 0:
        transactions = get_eth_txns(address)
        for txn in transactions:
            add_eth_transaction(txn)

        result = cursor.execute(
            """
            SELECT * FROM eth_transaction
            WHERE fromAddr = ? OR toAddr = ?
            """,
            (address, address),
        ).fetchall()

    connection.commit()
    cursor.close()

    return result


def is_valid_btc_address(address: str) -> bool:
    """This function performs a regex check on provided BTC address to check validity"""

    # Note: This is far from a thorough check as the checksum of the address isn't validated.
    pattern = "^(?:[13]{1}[a-km-zA-HJ-NP-Z1-9]{26,33}|bc1[a-z0-9]{39,59})$"

    return True if re.match(pattern, address) else False


def humanize_hash_or_addr(tx_hash) -> str:
    """Turns an address/hash into the format 0x33...7d3a"""
    return f"{tx_hash[:4]}...{tx_hash[-4:]}"


def get_eth_balance(address: str) -> decimal.Decimal:
    """This function returns the current Ether balance of the given address."""
    balance = w3.eth.get_balance(address)
    formatted_balance = w3.fromWei(balance, "ether")

    return formatted_balance


def get_btc_balance(address: str) -> decimal.Decimal:
    """This function returns the Bitcoin balance of the given address."""
    response_data = r.post(
        "https://www.blockonomics.co/api/balance",
        headers={"Authorization": "Bearer sgNWOodbscezo53zHr8tpuHEgm8Ll4xL9B7jqgLAJU0"},
        json={"addr": address},
    )
    if response_data.status_code == 200:
        balance = response_data.json()["response"][0]["confirmed"]
        formatted_balance = str(balance / 100_000_000)

        return decimal.Decimal(formatted_balance)


def get_eth_token_balances(address: str) -> Dict[str, str]:
    """This function returns all the balances of tokens of the specified address in the `assets.json`."""
    tokens = json.load(open("assets.json"))

    balances = []

    for token in tokens:
        erc20_abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"}]'

        contract_addr = token["address"]
        try:
            balance = (
                w3.eth.contract(
                    address=Web3.toChecksumAddress(contract_addr),
                    abi=erc20_abi,
                )
                .functions.balanceOf(address)
                .call()
            )
            if balance != 0:
                balances.append(
                    {"name": token.get("symbol"), "amount": balance / (10 ** token["decimals"])}
                )
        except exceptions.BadFunctionCallOutput:
            pass

    return balances


def get_eth_txns(address: str) -> List[Dict[str, str]]:
    """This function return the recent 25 transactions of a given address on the Ethereum blockchain."""
    response_data = r.get(
        f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&page=1&sort=desc&apikey=NEUACC949RWW9SFV4WXUU6E85MNGVPEQJB",
    )
    if response_data.status_code == 200:
        # storing only the last 25
        result = response_data.json()["result"][:25]
        result_with_txn_types = list(map(decode_eth_txn_input, result))

        return result_with_txn_types


def decode_eth_txn_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """This function decodes the transaction input received from Etherscan to determine the type of transaction."""
    # Normal transactions have their `input` field to be 0x from EtherScan API
    input_ = data["input"]
    cleaned_input_data = input_.removeprefix("0x")

    if cleaned_input_data == "":
        data["tx_type"] = "NORMAL"
        return data

    response_data = r.get(
        f"https://www.4byte.directory/api/v1/signatures/?hex_signature={cleaned_input_data[:8]}"
    )
    if response_data.status_code == 200:
        try:
            results = response_data.json()["results"]
            signature_type = results[-1]["text_signature"].split("(")[0]
            if signature_type == "swapETHForExactTokens":
                data["tx_type"] = "SWAP"
                return data
            elif signature_type == "transfer":
                data["tx_type"] = "TRANSFER"
                return data
            else:
                data["tx_type"] = "UNKNOWN"
                return data
        except IndexError:
            data["tx_type"] = "UNKNOWN"
            return data
    else:
        data["tx_type"] = "UNKNOWN"
        return data


def fetch_currency_price(chain: str, currency: str, amount: str) -> float:
    """This function converts a cryptocurrency's quantity into its fiat equivalent."""
    response_data = r.get(f"https://api.coincap.io/v2/assets?search={chain}&limit=1")
    if response_data.status_code == 200:
        chain_usd_price = response_data.json()["data"][0]["priceUsd"]
        if currency == "USD":
            return float(chain_usd_price) * float(amount)

        response = r.get("https://api.coincap.io/v2/rates")
        if response.status_code == 200:
            rates = response.json()["data"]
            currency_price = (
                float(chain_usd_price)
                * float(amount)
                / float(list(filter(lambda rate: rate["symbol"] == currency, rates))[0]["rateUsd"])
            )

            return currency_price
