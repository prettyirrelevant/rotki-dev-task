import os
import unittest

from src.utils import delete_database, initialise_database


class TestUtils(unittest.TestCase):
    def setUp(self) -> None:
        self.db_name = "a.db"

    def test_initialise_database(self):
        initialise_database(self.db_name)

        self.assertTrue(os.path.exists(self.db_name))
        self.assertTrue(os.path.isfile(self.db_name))
        self.assertFalse(os.path.isdir(self.db_name))

    def test_delete_database(self):
        initialise_database(self.db_name)
        delete_database(self.db_name)

        self.assertFalse(os.path.exists(self.db_name))
        self.assertFalse(os.path.isfile(self.db_name))
        self.assertFalse(os.path.isdir(self.db_name))

    def tearDown(self) -> None:
        delete_database(self.db_name)
