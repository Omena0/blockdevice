from scripts.get_version import get_blockdevice_version
from setuptools import setup, Extension
import pybind11

# Define the extension module
blockdevice_module = Extension(
    'blockdevice._blockdevice',
    sources=[
        'src/blockdevice.cpp',
        'src/blockdevice_class.cpp'
    ],
    include_dirs=[
        pybind11.get_include(),
        'include'
    ],
    language='c++',
    cxx_std=14,
)

setup(
    name='blockdevice',
    version=get_blockdevice_version(),
    author='Omena0',
    author_email='omena0mc@gmail.com',
    description='A simple C++ Python library for block device operations',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license_files=['COPYING.md'],
    url='https://github.com/Omena0/blockdevice',
    ext_modules=[blockdevice_module],
    packages=['blockdevice'],
    python_requires='>=3.13',
    install_requires=[
        'pybind11>=2.6.0',
    ],
    setup_requires=[
        'pybind11>=2.6.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.13',
        'Topic :: System :: Filesystems',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)