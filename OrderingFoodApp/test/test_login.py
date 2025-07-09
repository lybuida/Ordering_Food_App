import unittest
from OrderingFoodApp import dao1

class TestLogin(unittest.TestCase):
    def test_1(self):
        self.assertTrue(dao1.auth_user("user", 123))
    def test_1(self):
        self.assertTrue(dao1.auth_user("admin", 456))
    # def test_1(self):
    #     self.assertTrue(dao1.auth_user("user3", 123))

if __name__== "__main__":
    unittest.main()
