import sys

import pytest


@pytest.fixture(autouse=True)
def reset_app_runtime_transient_state():
    app_module = sys.modules.get("app")
    request_runtime = getattr(app_module, "request_runtime", None) if app_module else None
    if request_runtime is not None and hasattr(request_runtime, "reset_transient_state"):
        request_runtime.reset_transient_state()
    limiter = getattr(app_module, "limiter", None) if app_module else None
    limiter_storage = getattr(limiter, "storage", None) if limiter else None
    if limiter_storage is not None and hasattr(limiter_storage, "reset"):
        limiter_storage.reset()
    yield
