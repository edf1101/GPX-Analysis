# Rowing-GPX-Analysis
## Introduction
_GPX Analysis for rowing written in Python with a tkinter matplotlib interface_
#### Why?
I couldn't find the code for the old GPX analysis tool I wrote, so I'm taking the
opportunity to build a better/ more robust one.

## Prerequisites
#### Python Requirements
- Python 3.10 (or later)
- Numpy ```pip install numpy```
- Matplotlib ```pip install matplotlib```
- Pillow (should already be installed with mpl) ```pip install pillow```
- On mac there are tkinter glitches **It must be run from an interpreter with tkinter v8.6.12+** this comes preinstalled
with python 3.11

_Given it downloads map images from online it requires an internet connection to run._

## Installation
- For Standard users go to the GitHub page and download from releases
- For Developers you can clone the repository, install the requirements and run as you wish.
- It can also be installed with ```pip install gpx-analysis-edf1101``` and run from command line with ```python -m gpx_analysis.main``` 
## Getting Started
For instructions on how to use please view the [Getting started page](Getting_started.md) on the project's GitHub


## Details
The project is hosted online at https://github.com/edf1101/Rowing-GPX-Analysis

### License & Policies
- This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
- The only exception to this is the example data, which should not be used elsewhere.
- Code in graph_handler.py to fetch images from tile servers should be used with caution to make sure you comply with the
terms of service of the tile server you are using.