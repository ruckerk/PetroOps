import sys
from setuptools import setup
from OilOps import __version__

setup(
    name='OilOps',
    version = __version__,
    url='https://github.com/ruckerk/OilOps',
    author='W Kurt Rucker',
    author_email='william.rucker@gmail.com',
    packages=['OilOps'],
    install_requires=['adjustText',
                      'beautifulsoup4',
                      'datetime',
                      'easygui',
                      'futures3',
                      'lasio',
                      'python-libmagic',
                      'matplotlib',
                      'multiprocess',
                      'numpy',
                      'openpyxl',
                      'pandas',
                      'psutil',
                      'pycrs',
                      'pyproj',
                      'pyshp',
                      'python-dateutil',
                      'python-magic-bin; sys.platform == "win32"',
                      'requests',
                      'scipy',
                      'selenium',
                      'scikit-learn',
                      'sqlalchemy',
                      'tabula-py',
                      'textract',
                      'urllib3',
                      'wget',
                      'xlrd'],
    license='GPL',
    description='Oilfield Operations Tools',
    long_description=open('README.txt').read()
)

if sys.platform == "linux":
    print('python magic not installed but required')
    print('visit https://pypi.org/project/python-magic/ for installation detail')
    print('sudo apt-get install libmagic1')
     
