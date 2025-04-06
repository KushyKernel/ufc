from setuptools import setup, find_packages

setup(
    name="fd_ufc_scraper",
    version="1.0.0",
    description="A Python package to scrape UFC events and fighter data",
    author="Tife Kusimo",
    author_email="tife.kusimo@gmail.com",
    url="https://github.com/KushyKernel/UFC",  # Repository URL
    packages=find_packages(),
    install_requires=[
        "requests",
        "lxml",
        "googlesearch-python",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # adjust if needed
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
