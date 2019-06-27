'''

  setup.py for subrip module

  2019-06-19    Done.

'''

import setuptools

with open('README.md', 'r') as readme:
    long_description = readme.read()

setuptools.setup(name='srthandler',
                 version='1.0',
                 description='.srt subtitle handling',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='http://github.com/Legisign/srthandler',
                 author='Legisign.org',
                 author_email='software@legisign.org',
                 license='GPLv3',
                 packages=setuptools.find_packages())
