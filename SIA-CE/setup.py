from setuptools import setup, find_packages
import os

# Získání absolutní cesty k tomuto souboru
here = os.path.abspath(os.path.dirname(__file__))

# Čtení README pro dlouhý popis (volitelné)
readme_path = os.path.join(here, 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = ""

setup(
    name="sia-ce-control",
    version="0.1.0",
    author="Richard Maršala",
    author_email="risaniusl@gmail.com",  # Nahraďte vaším emailem
    description="Combined API for ChemStation CE and SIA control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Xixaus/sia-ce",  # Nahraďte vaší URL
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "pyserial>=3.5",
        "tqdm>=4.60.0",
        "pandas>=1.2.0",
        "pywin32>=300; platform_system=='Windows'",
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.10',
            'black>=21.0',
            'flake8>=3.9',
        ]
    },
    package_data={
        'ChemstationAPI': [
            'controllers/macros/*.mac',
            'core/*.mac',
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
)