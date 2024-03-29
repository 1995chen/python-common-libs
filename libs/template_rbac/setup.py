# -*- coding: UTF-8 -*-


from setuptools import setup

SHORT = u'template_rbac'
__version__ = "1.1.2"
__author__ = '1995chen'
__email__ = 'chenl2448365088@gmail.com'
# 依赖的库
__install_requires__ = [
    "inject >= 4.3.1", "PyJWT >= 1.7.1,<=2.0.1", "requests >= 2.26.0",
    "flask >= 2.0.1", "flask_restful >= 0.3.9",
    "template_exception >= 1.0.0", "template_json_encoder >= 1.0.0"
]

setup(
    name='template_rbac',
    version=__version__,
    packages=["template_rbac"],
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
