from setuptools import setup, find_packages

long_description = '''openaps predict plugin
==============================
This package is a vendor plugin for openaps that provides tools for predicting glucose trends.
'''

requires = ['openaps', 'python-dateutil', 'scipy']

__version__ = None
exec(open('openapscontrib/predict/version.py').read())

setup(
    name='openapscontrib.predict',
    version=__version__,
    url='https://github.com/loudnate/openaps-predict',
    download_url='http://pypi.python.org/pypi/openapscontrib.predict',
    license='MIT',
    author='Nathan Racklyeft',
    author_email='loudnate+pypi@gmail.com',
    description='openaps predict plugin',
    long_description=long_description,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['openapscontrib'],
    test_suite='tests'
)
