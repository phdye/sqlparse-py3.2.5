"""Plugin registry for formatter extensions.

This lightweight registry allows formatter features to be developed as
standalone plugins. Each plugin registers itself with a unique name so that
multiple teams can work on separate features concurrently without touching
shared state.
"""

_registry = {}


def register_plugin(name):
    """Decorator to register *plugin_cls* under *name*."""

    def _inner(plugin_cls):
        _registry[name] = plugin_cls
        return plugin_cls

    return _inner


def get_plugin(name):
    """Return the plugin class registered under *name* or *None*.

    Parameters are intentionally simple for compatibility with Python 3.2.5.
    """
    return _registry.get(name)


def available_plugins():
    """Return an iterable of registered plugin names."""
    return _registry.keys()


# Import bundled plugins
try:
    from . import dialect_strictness  # noqa: F401
except Exception:
    pass
