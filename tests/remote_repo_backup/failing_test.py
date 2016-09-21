import unittest


class FailureTest(unittest.TestCase):

    def test_destined_to_fail(self):
        self.assertTrue(False)
