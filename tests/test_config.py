import os

from sqlparse import config


def test_load_style():
    style = config.load_style('postgres')
    assert style['keyword_case'] == 'lower'


def test_load_config(tmpdir):
    cfg_dir = tmpdir.mkdir('cfg')
    cfg_file = cfg_dir.join('.sqlparse')
    cfg_file.write('KeywordCase: upper\n')
    options = config.load_config(str(cfg_dir))
    assert options['keyword_case'] == 'upper'


def test_dump_config():
    opts = config.DEFAULT_CONFIG.copy()
    opts['keyword_case'] = 'upper'
    dumped = config.dump_config(opts)
    assert 'KeywordCase: upper' in dumped
