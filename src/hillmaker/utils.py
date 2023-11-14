from typing import Dict, Optional
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import pandas as pd

from hillmaker import Scenario



