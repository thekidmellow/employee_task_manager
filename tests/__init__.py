# tests/__init__.py
import sys
import importlib

def _alias(pkg: str, target: str):
    """Map legacy package name -> real package under apps.* so tests can import."""
    try:
        sys.modules[pkg] = importlib.import_module(target)
    except ModuleNotFoundError:
        return
    # Common submodules some tests import directly
    for sub in ("models", "views", "forms", "urls", "admin"):
        try:
            sys.modules[f"{pkg}.{sub}"] = importlib.import_module(f"{target}.{sub}")
        except ModuleNotFoundError:
            pass

_alias("accounts", "apps.accounts")
_alias("tasks",    "apps.tasks")
_alias("core",     "apps.core")
