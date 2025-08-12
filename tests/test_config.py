import os

from sqlparse import config


def test_load_style():
    style = config.load_style('postgres')
    assert style['keyword_case'] == 'lower'


def test_load_config(tmpdir):
    cfg_dir = tmpdir.mkdir('cfg')
    cfg_file = cfg_dir.join('.sqlparse')
    cfg_file.write('version: 1\nkeywords:\n  case: upper\n')
    options = config.load_config(str(cfg_dir))
    assert options['keyword_case'] == 'upper'


def test_load_config_ignores_comments(tmpdir, monkeypatch):
    monkeypatch.setattr(config, 'yaml', None)
    cfg_dir = tmpdir.mkdir('cfg_comment')
    cfg_file = cfg_dir.join('.sqlparse')
    cfg_file.write('version: 1\nkeywords:\n  case: upper   # comment\n')
    options = config.load_config(str(cfg_dir))
    assert options['keyword_case'] == 'upper'


def test_dump_config():
    opts = config.DEFAULT_CONFIG.copy()
    opts['keyword_case'] = 'upper'
    dumped = config.dump_config(opts)
    assert 'KeywordCase: upper' in dumped


def test_load_clang_config(tmpdir):
    cfg = tmpdir.join('style.yaml')
    cfg.write('version: 1\nlayout:\n  indent_width: 3\nkeywords:\n  case: lower\n')
    opts = config.load_clang_config(str(cfg))
    assert opts['indent_width'] == 3
    assert opts['keyword_case'] == 'lower'
