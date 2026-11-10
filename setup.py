from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "blockdevice._blockdevice",
        sources=["src/blockdevice.cpp", "src/blockdevice_class.cpp"],
        include_dirs=["include"],
    ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
