"""
Library for multi temporal, multi sensor earth observation data integration and analysis.

"""

import importlib

__version__ = importlib.metadata.version("fusets")

from .whittaker import whittaker, WhittakerTransformer
from .mogpr import mogpr, MOGPRTransformer
from .peakvalley import peakvalley