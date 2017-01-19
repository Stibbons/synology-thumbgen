import setuptools
import sys

if not sys.version_info[0] == 3:
    sys.exit("Sorry, only Python 3 is supported.")

setuptools.setup(
    setup_requires=['pbr'],
    pbr=True)
