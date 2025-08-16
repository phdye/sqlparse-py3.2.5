import importlib
from sqlparse import plugins


def test_autodiscovery_without_explicit_import():
    importlib.reload(plugins)
    assert plugins.get_plugin('blocks') is not None


def test_disable_plugin_via_env(monkeypatch):
    monkeypatch.setenv('SQLPARSE_DISABLED_PLUGINS', 'blocks')
    importlib.reload(plugins)
    try:
        assert plugins.get_plugin('blocks') is None
    finally:
        monkeypatch.delenv('SQLPARSE_DISABLED_PLUGINS', raising=False)
        importlib.reload(plugins)

