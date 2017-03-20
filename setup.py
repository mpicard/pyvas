"""
pyvas
=====================
An OpenVAS Managment Protocol (OMP) client for Python
"""

from setuptools import setup, find_packages


setup(
    name="pyvas",
    version="0.0.1.dev1",
    description="An OpenVAS Managment Protocol (OMP) client for Python",
    url="https://github.com/cloudcix/pyvas",
    author="Martin Picard",
    author_email="martin8768@gmail.com",
    license="MIT",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords="openvas omp client",
    packages=find_packages(),
    install_requires=['lxml'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-cov', 'coverage', 'tox'],
    extras_require={'test': ['pytest', 'pytest-cov', 'coverage', 'tox']}
)
