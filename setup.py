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
                      'libmagic1; sys_platform == 'linux'
                      'python-magic-bin; sys_platform == 'win32'
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
