# -*- coding: UTF-8 -*-

from setuptools import setup

SHORT = u'template_cache'
__version__ = "1.0.0"
__author__ = '1995chen'
__email__ = 'chenl2448365088@gmail.com'
# 依赖的库
__install_requires__ = [
    "template_exception >= 1.0.0"
]

setup(
    name='template_cache',
    version=__version__,
    packages=["template_cache"],
    install_requires=__install_requires__,
    url='',
    author=__author__,
    author_email=__email__,
    python_requires='>=3.5.0',
    include_package_data=True,
    package_data={'': ['*.py', '*.pyc']},
    zip_safe=False,
    platforms='any',
    description=SHORT,
    long_description=__doc__,
)
