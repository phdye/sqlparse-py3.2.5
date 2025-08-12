"""Plugin registry for formatter extensions.

This lightweight registry allows formatter features to be developed as
standalone plugins. Each plugin registers itself with a unique name so that
multiple teams can work on separate features concurrently without touching
shared state.
"""

_registry = {}


def register_plugin(name, plugin_cls):
    """Register *plugin_cls* under *name*.

    If a plugin with *name* already exists it will be replaced.
    The function returns the class to allow usage as a decorator.
    """
    _registry[name] = plugin_cls
    return plugin_cls


def get_plugin(name):
    """Return the plugin class registered under *name* or *None*.

    Parameters are intentionally simple for compatibility with Python 3.2.5.
    """
    return _registry.get(name)


def available_plugins():
    """Return an iterable of registered plugin names."""
    return _registry.keys()
