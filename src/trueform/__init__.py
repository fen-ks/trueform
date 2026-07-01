"""trueform — an open-source, self-hostable text humanizer.

Public API:
    from trueform import humanize, Humanizer, HumanizeConfig
"""

from trueform.config import HumanizeConfig
from trueform.pipeline.humanizer import Humanizer, humanize

__version__ = "0.1.0"

__all__ = ["humanize", "Humanizer", "HumanizeConfig", "__version__"]
