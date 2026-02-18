"""Auto-discover and import extension modules from the ``local/`` directory.

Calling ``load_extensions()`` imports every ``.py`` file in ``local/``
(except ``__init__.py`` and ``config.py``, which are handled by
``fomc_tracker.config``).  This triggers side-effects such as
``@data_source`` decorator registrations.

Safe to call multiple times — subsequent calls are no-ops.
"""

import importlib
import logging
import os

logger = logging.getLogger(__name__)

_loaded = False


def load_extensions() -> None:
    """Import all extension modules from ``local/``.  No-op after first call."""
    global _loaded
    if _loaded:
        return

    _loaded = True

    # local/ sits at project root, next to fomc_tracker/
    local_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "local")
    if not os.path.isdir(local_dir):
        return  # No local/ directory — nothing to load

    skip = {"__init__.py", "config.py"}

    for filename in sorted(os.listdir(local_dir)):
        if not filename.endswith(".py") or filename in skip:
            continue
        module_name = f"local.{filename[:-3]}"
        try:
            importlib.import_module(module_name)
            logger.info(f"Loaded extension: {module_name}")
        except Exception as e:
            logger.warning(f"Failed to load extension {module_name}: {e}")
