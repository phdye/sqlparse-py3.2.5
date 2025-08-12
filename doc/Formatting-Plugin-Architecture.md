# Formatting Plugin Architecture

To enable multiple developers to work on configuration options in parallel,
sqlparse provides a lightweight plugin registry located at
`sqlparse/plugins/__init__.py`. Each formatter enhancement can live in its own
module and register itself with the registry without modifying shared code.

## Writing a plugin

1. Create a module inside `sqlparse/plugins/`.
2. Implement a class with a `format(self, stream, options)` method.
3. Register the class:

```python
from sqlparse import plugins

@plugins.register_plugin('custom_option')
class CustomOption(object):
    def format(self, stream, options):
        # mutate or yield tokens
        return stream
```

4. Add tests demonstrating the plugin behaviour.

## Development guidelines

- Plugins should avoid side effects outside their module.
- Configuration parsing should map options to plugin names so that new plugins
  can be developed independently.
- Because each plugin is contained within its own file and registered by name,
  separate teams can work on different plugins or phases without touching the
  same code paths.

This architecture allows concurrent sessions to contribute new formatting
features with minimal risk of merge conflicts.
