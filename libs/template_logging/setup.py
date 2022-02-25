# -*- coding: UTF-8 -*-


from setuptools import setup

SHORT = u'template_logging'
__version__ = "1.0.1"
__author__ = '1995chen'
__email__ = 'chenl2448365088@gmail.com'
# 依赖的库
__install_requires__ = []

setup(
    name='template_logging',
    version=__version__,
    packages=["template_logging"],
    install_requires=__install_requires__,
    url='',
    author=__author__,
    author_email=__email__,
    python_requires='>=3.5.0',
    include_package_data=True,
    package_data={'': ['*.py', '*.pyc'], 'template_logging': ['*.ini']},
    zip_safe=False,
    platforms='any',
    description=SHORT,
    long_description=__doc__,
)
