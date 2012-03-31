import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "dogbutler",
    version = "0.0.1",
    author = "The Sirisanthana Team",
    author_email = "vsirisanthana@gmail.com",
    description = "Make HTTP/HTTPS requests with cache, cookie, and redirect support",
    long_description = read('README.txt'),
    license = "GPL-3.0",
    keywords = "HTTP HTTPS request python cache cookie redirect",
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License (GPL)"
    ],
    packages = ['dogbutler'],
    install_requires = ['dummycache', 'requests'],
)
