import sys

import pytest


@pytest.fixture(autouse=True)
def reset_app_runtime_transient_state():
    app_module = sys.modules.get("app")
    request_runtime = getattr(app_module, "request_runtime", None) if app_module else None
    if request_runtime is not None and hasattr(request_runtime, "reset_transient_state"):
        request_runtime.reset_transient_state()
    yield
