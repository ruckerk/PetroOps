from setuptools import setup

setup(
    name='PetroOps',
    version = '0.0.1',
    url='https://github.com/ruckerk/PetroOps',
    author='W Kurt Rucker',
    author_email='william.rucker@gmail.com',
    packages=['PetroOps'],
    install_requires=['numpy', 're'],
    python_requires='>3.6.2',
    license='MIT',
    description='Oilfield Operations Tools',
    long_description=open('README.txt').read()
)
