from setuptools import setup

setup(
    name='OilOps',
    version = '0.0.2',
    url='https://github.com/ruckerk/OilOps',
    author='W Kurt Rucker',
    author_email='william.rucker@gmail.com',
    packages=['OilOps'],
    install_requires=['adjustText', 
                      'bs4', 
                      'easygui', 
                      'futures3',
                      'matplotlib', 
                      'multiprocess', 
                      'numpy', 
                      'pandas ', 
                      'psutil',
                      'pyproj ',
                      'pyshp',
                      'requests',
                      'scipy',
                      'selenium', 
                      'shapely',
                      'sklearn',
                      'sqlalchemy', 
                      'tabula-py', 
                      'urllib3',
                      'xlrd', 
                      'openpyxl'],
    license='GPL',
    description='Oilfield Operations Tools',
    long_description=open('README.txt').read()
)
