from setuptools import setup, Extension
import pybind11
import os

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
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='A simple C++ Python library for block device operations',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    license='MIT',
    license_files=['COPYING.md'],
    url='https://github.com/Omena0/blockdevice',
    ext_modules=[blockdevice_module],
    packages=['blockdevice'],
    python_requires='>=3.6',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Operating System :: OS Independent',
        'Topic :: System :: Filesystems',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)