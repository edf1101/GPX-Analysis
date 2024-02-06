import setuptools

with open("README.md", "r") as fh:
    readme = fh.read()

setuptools.setup(
    name="gpx_analysis-edf1101",
    version="1.6",
    author="edf1101",
    author_email="blank@blank.com",
    description="GPX Analysis Program",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/edf1101/Rowing-GPX-Analysis",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=["matplotlib", "numpy", "appdirs"]
)
