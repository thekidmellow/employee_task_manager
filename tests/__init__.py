import sys
import importlib


def _alias(pkg: str, target: str):

    try:
        sys.modules[pkg] = importlib.import_module(target)
    except ModuleNotFoundError:
        return

    for sub in ("models", "views", "forms", "urls", "admin"):
        try:
            sys.modules[f"{pkg}.{sub}"] = importlib.import_module(
                f"{target}.{sub}")
        except ModuleNotFoundError:
            pass


_alias("accounts", "apps.accounts")
_alias("tasks",    "apps.tasks")
_alias("core",     "apps.core")
