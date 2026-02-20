"""Centralised configuration with local override support.

Loading order
-------------
1. Import every UPPERCASE attribute from ``boe_tracker.defaults``
2. Try ``from local.boe_config import *`` -- for each UPPERCASE name:
   - **dict** values are *merged* (local keys add to / replace defaults)
   - **scalar** values (str, int, float, list, tuple) *replace* the default
3. Expose the final values as module-level constants.

Fork users create ``local/boe_config.py`` to customise thresholds, weights,
URLs, etc. without editing any upstream file.

This module deliberately has **zero imports from other boe_tracker
modules** so it can be imported first without circular-dependency risk.
"""

import importlib
import logging

from boe_tracker import defaults as _defaults

logger = logging.getLogger(__name__)

# -- Step 1: seed this module's namespace from defaults ----------------------

_this = importlib.import_module(__name__)

for _attr in dir(_defaults):
    if _attr.isupper():
        setattr(_this, _attr, getattr(_defaults, _attr))

# -- Step 2: merge local overrides (if present) ------------------------------

try:
    from local import boe_config as _local_cfg  # type: ignore[import-not-found]

    for _attr in dir(_local_cfg):
        if not _attr.isupper():
            continue
        _local_val = getattr(_local_cfg, _attr)
        _default_val = getattr(_this, _attr, None)

        if isinstance(_default_val, dict) and isinstance(_local_val, dict):
            merged = {**_default_val, **_local_val}
            setattr(_this, _attr, merged)
        else:
            setattr(_this, _attr, _local_val)

    logger.info("Loaded local BOE config overrides from local/boe_config.py")
except ImportError:
    pass  # No local/boe_config.py -- use defaults only


# -- Convenience helpers -----------------------------------------------------

def score_label(score: float) -> str:
    """Convert a numeric score to 'Hawkish', 'Dovish', or 'Neutral'."""
    if score > _this.HAWKISH_THRESHOLD:
        return "Hawkish"
    if score < _this.DOVISH_THRESHOLD:
        return "Dovish"
    return "Neutral"


def score_color(score: float) -> str:
    """Return the UI color string for a given score."""
    colors = _this.COLORS
    if score > _this.HAWKISH_THRESHOLD:
        return colors["hawk"]
    if score < _this.DOVISH_THRESHOLD:
        return colors["dove"]
    return colors["neutral"]
