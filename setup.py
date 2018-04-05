import pathlib
import re
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class BuildFailed(Exception):
    pass


here = pathlib.Path(__file__).parent

txt = (here / 'cloud_img' / '__init__.py').read_text('utf-8')
try:
    version = re.findall(r"^__version__ = '([^']+)'\r?$", txt, re.M)[0]
except IndexError:
    raise RuntimeError('Unable to determine version.')

install_requires = [
    line.split()[0]
    for line in (here / 'requirements.txt').read_text('utf-8').splitlines()
]


def read(f):
    return (here / f).read_text('utf-8').strip()


class PyTest(TestCommand):
    user_options = []

    def run(self):
        import subprocess
        errno = subprocess.call([sys.executable, '-m', 'pytest', 'tests'])
        raise SystemExit(errno)


tests_require = install_requires + ['pytest', 'pytest-aiohttp']

setup(
    name='cloud_img',
    version=version,
    description='managing the web image',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 5 - Production/Stable',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Internet :: WWW/HTTP',
        'Framework :: AsyncIO',
    ],
    author='Wei Lin',
    author_email='linw1995@icloud.com',
    maintainer='Wei Lin <linw1995@icloud.com>',
    url='https://github.com/linw1995/cloud_img/',
    license='GPLv3',
    packages=['cloud_img'],
    python_requires='>=3.6.0',
    install_requires=install_requires,
    tests_require=tests_require,
    include_package_data=True)
