from __future__ import annotations

import importlib
import sys
import warnings


def test_import_has_no_on_event_deprecation_warning() -> None:
    if "app.main" in sys.modules:
        del sys.modules["app.main"]

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.import_module("app.main")

    assert not any("on_event is deprecated" in str(item.message) for item in caught)
