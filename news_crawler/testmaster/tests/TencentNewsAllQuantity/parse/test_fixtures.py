# THIS IS A GENERATED FILE
# Generated by: scrapy crawl TencentNewsAllQuantity  # noqa: E501
# Request URL: https://www.qq.com/?pgv_ref=404  # noqa: E501
import os
import unittest
from scrapy_testmaster.utils import generate_test


class TestMaster(unittest.TestCase):
    def test__TencentNewsAllQuantity__parse(self):
        files = os.listdir(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )
        files = [f for f in files if f.endswith('.bin')]
        self.maxDiff = None
        for f in files:
            file_path = os.path.join(os.path.dirname(__file__), f)
            print("Testing fixture '%s' in location: %s" % (f, file_path))
            test = generate_test(os.path.abspath(file_path))
            test(self)


if __name__ == '__main__':
    unittest.main()
