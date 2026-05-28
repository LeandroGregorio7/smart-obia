"""
Setup script for Smart OBIA Plugin
Install with: python setup.py install
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="smart-obia",
    version="0.3.0",
    author="Leandro da Silva Gregorio",
    author_email="leangeosmart@gmail.com",
    description="Advanced Object-Based Image Analysis plugin for QGIS with Machine Learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/smart_obia",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Image Processing",
    ],
    python_requires=">=3.6",
    install_requires=[
        "numpy>=1.19.0",
        "scipy>=1.5.0",
        "scikit-image>=0.17.0",
        "scikit-learn>=0.24.0",
        "catboost>=1.0.0",  # <- NOVA DEPENDÊNCIA
        "Pillow>=8.0.0",
    ],
    entry_points={
        "qgis.plugins": [
            "smart_obia = smart_obia:classFactory",
        ],
    },
    include_package_data=True,
    package_data={
        "smart_obia": ["icon.png", "icon.jpg", "metadata.txt"],
    },
)