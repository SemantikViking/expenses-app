"""
Setup script for Receipt Processing Application.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path) as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]
else:
    requirements = [
        "pydantic>=2.5.0",
        "pydantic-ai>=0.0.13", 
        "pydantic-settings>=2.1.0",
        "click>=8.1.0",
        "loguru>=0.7.0",
        "watchdog>=3.0.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
    ]

setup(
    name="receipt-processor",
    version="0.1.0",
    description="AI-powered receipt processing application for macOS",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Receipt Processor Team",
    author_email="support@receipt-processor.com",
    url="https://github.com/username/receipt-processor",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    python_requires=">=3.9",
    install_requires=requirements,
    
    entry_points={
        "console_scripts": [
            "receipt-processor=receipt_processor.main:main",
            "rp=receipt_processor.main:main",  # Short alias
        ],
    },
    
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Multimedia :: Graphics :: Capture :: Scanners",
        "Environment :: Console",
    ],
    
    keywords="receipt processing ai vision ocr macos automation",
    
    project_urls={
        "Bug Reports": "https://github.com/username/receipt-processor/issues",
        "Source": "https://github.com/username/receipt-processor",
        "Documentation": "https://github.com/username/receipt-processor/wiki",
    },
    
    include_package_data=True,
    package_data={
        "receipt_processor": [
            "config/*.env",
            "templates/*.txt",
        ],
    },
)
