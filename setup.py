from setuptools import setup, find_packages

setup(
    name='keyvalues3',
    version='0.1',

    author='kristiker',
    author_email='kristik06@outlook.com',
    url='https://github.com/kristiker/keyvalues3',

    description='A parser for Valve\'s KeyValues3 format',
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type='text/markdown',

    packages=find_packages(),
    python_requires='>=3.11',
    classifiers=[
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Typing :: Typed',
    ],
)
