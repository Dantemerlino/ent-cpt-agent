from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="ent-cpt-agent",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An AI-powered assistant for ENT CPT code selection and validation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-organization/ent-cpt-agent",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ent-cpt-agent=main:main",
        ],
    },
)
