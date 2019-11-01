from setuptools import setup

readme = open('README.rst').read()
# history = open('CHANGES.rst').read().replace('.. :changelog:', '')
history = ''

setup(
    name='board',
    version='1.0',
    description='Standard Board mechanism for Dojo tasks',
    long_description=readme + '\n\n' + history,
    author='Tim Golden',
    author_email='mail@timgolden.me.uk',
    maintainer='Tim Golden',
    maintainer_email='mail@timgolden.me.uk',
    license="unlicensed",
    url='https://github.com/tjguk/dojo-board',
    py_modules=['board'],
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
    ],
)
