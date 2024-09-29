from setuptools import setup, find_packages, find_namespace_packages
import codecs
import os
from jtag_axi.version import __version__

DESCRIPTION = "JTAG to AXI bridge python I/F"
LONG_DESCRIPTION = "Small class to handle JTAG to AXI requests"

long_description = "\n"
here = os.path.abspath(os.path.dirname(__file__))
with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

# Setting up
setup(
    name="jtag_axi",
    packages=find_packages(),
    version=__version__,
    author="aignacio (Anderson Ignacio)",
    author_email="<anderson@aignacio.com>",
    license="MIT",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/aignacio/jtag_axi",
    project_urls={
        "Source Code": "https://github.com/aignacio/jtag_axi",
    },
    include_package_data=False,
    python_requires=">=3.6",
    install_requires=["pyftdi"],
    extras_require={
        "test": [
            "pytest",
            "pyftdi"
        ],
    },
    keywords=["soc", "vip", "hdl", "verilog", "systemverilog", "jtag"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
