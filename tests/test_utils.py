import decimal
import os
import unittest

from eth_utils import to_normalized_address

from src.utils import (
    add_address,
    add_eth_transaction,
    delete_database,
    fetch_eth_transactions,
    get_addresses_by_chain,
    get_btc_balance,
    get_eth_balance,
    get_eth_txns,
    humanize_hash_or_addr,
    initialise_database,
    is_valid_btc_address,
)


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.db_name = "rotki-dev-task.db"
        initialise_database()

    def test_initialise_database(self):
        self.assertTrue(os.path.exists(self.db_name))
        self.assertTrue(os.path.isfile(self.db_name))
        self.assertFalse(os.path.isdir(self.db_name))

    def test_delete_database(self):
        delete_database()

        self.assertFalse(os.path.exists(self.db_name))
        self.assertFalse(os.path.isfile(self.db_name))
        self.assertFalse(os.path.isdir(self.db_name))

    def test_is_valid_btc_address(self):
        self.assertTrue(is_valid_btc_address("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo"))
        self.assertTrue(
            is_valid_btc_address("bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97")
        )
        self.assertTrue(is_valid_btc_address("1FeexV6bAHb8ybZjqQMjJrcCrHGW9sb6uF"))
        self.assertTrue(is_valid_btc_address("bc1qazcm763858nkj2dj986etajv6wquslv8uxwczt"))
        self.assertTrue(is_valid_btc_address("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo"))
        self.assertFalse(is_valid_btc_address("3gtdmotoimp4vRoCGJym3xR7yCVPFHoCNxv4Twseo"))
        self.assertFalse(is_valid_btc_address("3LQUu4v9z6KNchfenkvn71j7kbj8GPeAGUo1FW6a"))

    def test_humanize_addr_or_hash(self):
        self.assertEqual(
            humanize_hash_or_addr("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo"), "34xp...wseo"
        )
        self.assertEqual(
            humanize_hash_or_addr("0xD428B66C27bF3f0e2567139ac4930303Ad11fAe4"), "0xD4...fAe4"
        )
        self.assertEqual(
            humanize_hash_or_addr("0x6dE701678d2a55ef22FAabd666a82459046b44dF"), "0x6d...44dF"
        )

        self.assertNotEqual(
            humanize_hash_or_addr("0x6dE701678d2a55ef22FAabd666a82459046b44dF"), "0x6...44dF"
        )

    def test_get_eth_balance(self):
        self.assertEqual(
            get_eth_balance("0x6dE701678d2a55ef22FAabd666a82459046b44dF"),
            decimal.Decimal("0.092223602755262143"),
        )
        self.assertNotEqual(
            get_eth_balance("0x6dE701678d2a55ef22FAabd666a82459046b44dF"),
            decimal.Decimal("10"),
        )

    def test_get_btc_balance(self):
        self.assertEqual(
            get_btc_balance("12ib7dApVFvg82TXKycWBNpN8kFyiAN1dr"),
            decimal.Decimal("31000.07042388"),
        )

        self.assertEqual(
            get_btc_balance("198aMn6ZYAczwrE5NvNTUMyJ5qkfy4g3Hi"), decimal.Decimal("8000.00344573")
        )

    def test_add_address(self):
        total_changes = add_address(
            {"address": "198aMn6ZYAczwrE5NvNTUMyJ5qkfy4g3Hi", "chain": "btc"}
        )
        self.assertEqual(total_changes, 1)

    def test_add_eth_txn(self):
        total_changes = add_eth_transaction(
            {"hash": "0xnnrne", "from": "0xqqqq", "to": "0xdttt", "tx_type": "SWAP", "value": "0"}
        )
        self.assertEqual(total_changes, 1)

    def test_get_addresses_by_chain(self):
        add_address({"address": "198aMn6ZYAczwrE5NvNTUMyJ5qkfy4g3Hi", "chain": "btc"})
        add_address({"address": "198aMn6ZYAczwrE5NvNTUMyJ5qkfy4g3Hi", "chain": "btc"})
        add_address({"address": "198aMn6ZYAczwrE5NvNTUMyJ5qkfy4g3Hi", "chain": "btc"})

        result = get_addresses_by_chain("btc")
        self.assertEqual(len(result), 3)

    def test_fetch_eth_transactions(self):
        add_eth_transaction(
            {
                "hash": "0xnnrne",
                "from": to_normalized_address("0x6dE701678d2a55ef22FAabd666a82459046b44dF"),
                "to": "0xD428B66C27bF3f0e2567139ac4930303Ad11fAe4",
                "tx_type": "SWAP",
                "value": "0",
            }
        )
        add_eth_transaction(
            {
                "hash": "0xnnrne",
                "from": to_normalized_address("0x6dE701678d2a55ef22FAabd666a82459046b44dF"),
                "to": "0xD428B66C27bF3f0e2567139ac4930303Ad11fAe4",
                "tx_type": "SWAP",
                "value": "0",
            }
        )

        result = fetch_eth_transactions("0x6dE701678d2a55ef22FAabd666a82459046b44dF")
        self.assertEqual(len(result), 2)

    def test_get_eth_txns(self):
        result = get_eth_txns("0x0B7b93Ebb893a7B8E61419263DCB2e09903c2638")
        self.assertLessEqual(len(result), 25)

    def tearDown(self) -> None:
        delete_database()
