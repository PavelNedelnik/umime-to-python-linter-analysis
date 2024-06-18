"""Tests the modules related to generating the linter messages."""

import unittest

from src.code_processing import *


class CodeProcessingTest(unittest.TestCase):
    """Tests the code processing module."""

    def test_sanity(self):
        """Basic sanity test."""
        code = "ZGVmIGltcG9zZV9maW5lKGFnZSwgYmVlcik6CiAgICByZXR1cm4gRmFsc2UK"
        self.assertEqual(decode_code_string(code), "def impose_fine(age, beer):\n    return False")
