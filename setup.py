from setuptools import setup, find_packages

setup(
    name="geopytec",
    version="0.1.0",
    description="Biblioteca para processamento de ensaios de cisalhamento direto",
    author="André Monteiro Klen",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "matplotlib",
        "scipy",
        "openpyxl"
    ],
)
