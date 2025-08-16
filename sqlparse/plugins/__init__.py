"""Plugin registry for formatter extensions.

This lightweight registry allows formatter features to be developed as
standalone plugins. Each plugin registers itself with a unique name so that
multiple teams can work on separate features concurrently without touching
shared state.  Registration happens automatically through a discovery
mechanism so that new plugins can be added without modifying this file.
"""

import importlib
import os
import pkgutil

try:  # pragma: no cover - dependency optional on old Pythons
    from importlib import metadata as importlib_metadata
except Exception:  # pragma: no cover
    try:  # type: ignore
        import importlib_metadata as importlib_metadata
    except Exception:  # pragma: no cover
        importlib_metadata = None  # type: ignore

_registry = {}
_discovered = False


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


def _should_load(name, enabled, disabled):
    if name.startswith('_'):
        return False
    if enabled and name not in enabled:
        return False
    if name in disabled:
        return False
    return True


def _discover_bundled(enabled, disabled):
    for mod in pkgutil.iter_modules(__path__):
        name = mod.name
        if not _should_load(name, enabled, disabled):
            continue
        try:
            importlib.import_module('%s.%s' % (__name__, name))
        except Exception:
            continue


def _discover_entry_points(enabled, disabled):
    if importlib_metadata is None:  # pragma: no cover
        return
    try:
        eps = importlib_metadata.entry_points()
        if hasattr(eps, 'select'):
            eps = eps.select(group='sqlparse.plugins')
        else:  # pragma: no cover - older importlib_metadata API
            eps = eps.get('sqlparse.plugins', [])
    except Exception:  # pragma: no cover
        return
    for ep in eps:
        name = ep.name
        if not _should_load(name, enabled, disabled):
            continue
        try:
            plugin = ep.load()
        except Exception:
            continue
        register_plugin(name, plugin)


def _ensure_plugins_loaded():
    global _discovered
    if _discovered:
        return
    _discovered = True
    enabled = set(filter(None, os.environ.get('SQLPARSE_ENABLED_PLUGINS', '').split(',')))
    disabled = set(filter(None, os.environ.get('SQLPARSE_DISABLED_PLUGINS', '').split(',')))
    _discover_bundled(enabled, disabled)
    _discover_entry_points(enabled, disabled)


def get_plugin(name):
    """Return the plugin class registered under *name* or *None*.

    Parameters are intentionally simple for compatibility with Python 3.2.5.
    """
    _ensure_plugins_loaded()
    cls = _registry.get(name)
    if cls is None:
        try:
            importlib.import_module('sqlparse.plugins.{0}'.format(name))
        except Exception:
            return None
        cls = _registry.get(name)
    return cls


def available_plugins():
    """Return an iterable of registered plugin names."""
    _ensure_plugins_loaded()
    return _registry.keys()
