# Plugin Developer Guide

This guide explains how to build formatter plugins for sqlparse.  It assumes only
basic Python knowledge and is aimed at developers with less than a year of
experience.  Each section walks through the concepts with examples taken from
the existing code base.

## 1. How plugins are discovered

sqlparse keeps plugins in the `sqlparse.plugins` package and loads them through a
small registry.  The registry exposes `register_plugin` for modules to add
themselves and can search for third-party entry points at runtime.  Discovery is
lazily triggered when `get_plugin` or `available_plugins` is called, which keeps
startup costs low.

Plugins can be enabled or disabled via the `SQLPARSE_ENABLED_PLUGINS` or
`SQLPARSE_DISABLED_PLUGINS` environment variables.  These variables contain
comma-separated plugin names and are evaluated before bundled modules and entry
points are scanned.

## 2. Anatomy of a plugin

Every plugin lives in its own module inside `sqlparse/plugins`.  A plugin is a
class with a single `format(self, stream, options)` method.  The `stream`
parameter may be either a string of SQL or an iterable of tokens depending on
where the plugin is placed in the formatter pipeline.  The `options` argument is
a dictionary of configuration values; each plugin reads only the keys it
understands.

Registration is usually done with the `@plugins.register_plugin('name')`
decorator but the registry also accepts explicit calls:

```python
from sqlparse import plugins

@plugins.register_plugin('upper_keywords')
class UpperKeywords(object):
    def format(self, stream, options):
        if isinstance(stream, (list, tuple)):
            text = ''.join(stream)
        else:
            text = stream
        return text.upper()
```

Plugins should always return the same type they receive.  The example above
returns an upper-cased string because the input `stream` is a string.  When a
plugin receives a token stream it should yield tokens back to the caller instead
of joining them into a string.

## 3. Plugin varieties

Although every plugin shares the same interface, they can operate at different
levels of abstraction.

### 3.1 Text based formatters

Some plugins work purely on raw SQL strings.  `BlocksPlugin` is a good example.
It rewrites procedural blocks and declaration sections using regular
expressions and string manipulation:

```python
if block_opts.get('begin_same_line'):
    text = re.sub(r'\n([ \t]*)BEGIN', r' BEGIN', text, flags=re.IGNORECASE)

if block_opts.get('end_own_line'):
    text = re.sub(r'\s*END', r'\nEND', text, flags=re.IGNORECASE)
```

These snippets align `BEGIN` tokens with their preceding line and ensure `END`
appears on its own line.  Additional helpers handle label alignment and
multi-line `DECLARE` blocks.

### 3.2 Token stream processors

Other plugins expect a tokenized statement and yield tokens back to the
formatter.  `DialectStrictness` demonstrates this dual behaviour.  When given an
iterator of `(ttype, value)` pairs the plugin rewrites unknown keywords to
`Name` tokens so that invalid dialect keywords are not upper-cased later on.
For statement objects the plugin adjusts continuation indentation by inspecting
and modifying whitespace tokens.

### 3.3 Hybrid formatters

Some modules use both strategies.  `JoinPlugin` formats join clauses by first
running `sqlparse.format` to get a normalized layout and then manipulating the
resulting lines.  It can insert a newline before an `ON` clause or merge it with
the preceding `JOIN` depending on configuration.  The plugin also emits a
`UserWarning` when it detects comma joins if `prefer_explicit` is enabled.

## 4. Step-by-step: creating your own plugin

1. **Create a module** in `sqlparse/plugins/` with a meaningful name.
2. **Define a class** containing a `format` method.  Keep logic inside the class
   and avoid side effects at import time.
3. **Register the class** using `@plugins.register_plugin('your_name')` or by
   calling `plugins.register_plugin('your_name', YourClass)`.
4. **Parse configuration options** from the provided `options` dictionary.  Use
   `options.get('section', {}).get('key')` patterns to keep defaults simple.
5. **Return the modified stream** while preserving the input type.

### Example: indentation normalizer

```python
from sqlparse import plugins

@plugins.register_plugin('indent_normalizer')
class IndentNormalizer(object):
    def format(self, stream, options):
        indent = ' ' * options.get('indent_width', 2)
        return '\n'.join(indent + line.lstrip() for line in stream.splitlines())
```

## 5. Third-party plugins

External packages can contribute plugins without modifying the sqlparse source
code.  Expose an entry point in your project's `pyproject.toml`:

```toml
[project.entry-points."sqlparse.plugins"]
my_plugin = "mypackage.module:PluginClass"
```

Once the package is installed, sqlparse discovers the plugin the first time the
registry is queried.

## 6. Testing

Write pytest tests for each plugin to show the expected transformation.
Configure the test case so it calls the plugin with a sample SQL string and
asserts on the result.  Running `python -m pytest` from the repository root will
execute all tests.

## 7. Best practices

- Target Python 3.2.5 and avoid modern language features not supported by that
  version.
- Keep modules self-contained; plugins should not modify global state outside of
their own file.
- Fail gracefully—unexpected input should be returned unchanged rather than
raising errors.
- Document configuration keys and default behaviour within the module and in
this guide so other developers can build on your work.

With these guidelines you can extend sqlparse with new formatting behaviours
while keeping the core library stable and easy to maintain.
