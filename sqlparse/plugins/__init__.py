"""Plugin registry for formatter extensions.

This lightweight registry allows formatter features to be developed as
standalone plugins. Each plugin registers itself with a unique name so that
multiple teams can work on separate features concurrently without touching
shared state.
"""

_registry = {}


def register_plugin(name, plugin_cls=None):
    """Register *plugin_cls* under *name*.

    Can be used as ``register_plugin('name', cls)`` or as a decorator::

        @register_plugin('name')
        class MyPlugin(object):
            ...

    If a plugin with *name* already exists it will be replaced.
    """
    if plugin_cls is None:
        def decorator(cls):
            _registry[name] = cls
            return cls
        return decorator
    _registry[name] = plugin_cls
    return plugin_cls


def get_plugin(name):
    """Return the plugin class registered under *name* or *None*.

    Parameters are intentionally simple for compatibility with Python 3.2.5.
    """
    cls = _registry.get(name)
    if cls is None:
        try:
            __import__('sqlparse.plugins.{0}'.format(name))
        except Exception:
            return None
        cls = _registry.get(name)
    return cls


def available_plugins():
    """Return an iterable of registered plugin names."""
    return _registry.keys()


# Import bundled plugins so that they register themselves with the registry.
# Each plugin uses the register_plugin decorator at import time.
try:  # pragma: no cover - import side effects are tested elsewhere
    from . import cte  # noqa: F401
    from . import dialect_strictness  # noqa: F401
except Exception:
    # If the plugin fails to import we simply skip registration to keep
    # compatibility with minimal environments.
