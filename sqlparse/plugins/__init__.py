"""Plugin registry for formatter extensions.

This lightweight registry allows formatter features to be developed as
standalone plugins. Each plugin registers itself with a unique name so that
multiple teams can work on separate features concurrently without touching
shared state.
"""

_registry = {}


def register_plugin(name):
    """Return a decorator that registers *plugin_cls* under *name*."""

    def _decorator(plugin_cls):
        _registry[name] = plugin_cls
        return plugin_cls

    return _decorator


def get_plugin(name):
    """Return the plugin class registered under *name* or *None*.

    Parameters are intentionally simple for compatibility with Python 3.2.5.
    """
    return _registry.get(name)


def available_plugins():
    """Return an iterable of registered plugin names."""
    return _registry.keys()


# Import bundled plugins so that they register themselves with the registry.
# Each plugin uses the register_plugin decorator at import time.
try:  # pragma: no cover - import side effects are tested elsewhere
    from . import cte  # noqa: F401
except Exception:
    # If the plugin fails to import we simply skip registration to keep
    # compatibility with minimal environments.
    pass
