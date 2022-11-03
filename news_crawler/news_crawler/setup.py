'''
Configure crawler startup command
'''

from setuptools import setup

setup(name='scrapy-mymodule',
      entry_points={
          'scrapy.commands': [
              'crawlall=news_crawler.commands:crawlall',
          ],
      },
      )
