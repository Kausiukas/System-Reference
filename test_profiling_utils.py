import unittest
import os
from profiling_utils import profile_function, profile_block
import time

def slow_function(x):
    s = 0
    for i in range(10000):
        s += (i * x) % 7
    return s

class TestProfilingUtils(unittest.TestCase):
    def test_profile_function_decorator(self):
        @profile_function(output_file="test_profile_func.txt")
        def test_func():
            time.sleep(0.05)
            return 42
        result = test_func()
        self.assertEqual(result, 42)
        self.assertTrue(os.path.exists("test_profile_func.txt"))
        print("profile_function decorator output:", open("test_profile_func.txt").readlines()[:3])
        os.remove("test_profile_func.txt")

    def test_profile_block(self):
        with profile_block(output_file="test_profile_block.txt"):
            time.sleep(0.05)
        self.assertTrue(os.path.exists("test_profile_block.txt"))
        print("profile_block output:", open("test_profile_block.txt").readlines()[:3])
        os.remove("test_profile_block.txt")

if __name__ == "__main__":
    unittest.main() 