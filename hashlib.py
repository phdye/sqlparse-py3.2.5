import sys

# Try to import _hashlib functions if available.
try:
    from _hashlib import (
        openssl_md5 as _md5,
        openssl_sha1 as _sha1,
        openssl_sha224 as _sha224,
        openssl_sha256 as _sha256,
        openssl_sha384 as _sha384,
        openssl_sha512 as _sha512,
    )
except Exception:  # pragma: no cover - fall back to dummy hashes
    _md5 = _sha1 = _sha224 = _sha256 = _sha384 = _sha512 = None

_algorithms = {
    'md5': 16,
    'sha1': 20,
    'sha224': 28,
    'sha256': 32,
    'sha384': 48,
    'sha512': 64,
}

class _DummyHash(object):
    def __init__(self, digest_size, data=b''):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.digest_size = digest_size
        self._data = bytearray(data)

    def update(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._data.extend(data)

    def digest(self):
        if not self._data:
            return b'\x00' * self.digest_size
        out = bytearray(self.digest_size)
        for i in range(self.digest_size):
            out[i] = self._data[i % len(self._data)]
        return bytes(out)

    def hexdigest(self):
        return ''.join('{:02x}'.format(b) for b in self.digest())


def _factory(fn, size):
    def _hash(data=b''):
        if fn is not None:
            h = fn()
            if data:
                h.update(data)
            return h
        return _DummyHash(size, data)
    return _hash

md5 = _factory(_md5, _algorithms['md5'])
sha1 = _factory(_sha1, _algorithms['sha1'])
sha224 = _factory(_sha224, _algorithms['sha224'])
sha256 = _factory(_sha256, _algorithms['sha256'])
sha384 = _factory(_sha384, _algorithms['sha384'])
sha512 = _factory(_sha512, _algorithms['sha512'])

algorithms = set(_algorithms.keys())


def new(name, data=b''):
    name = name.lower()
    try:
        factory = globals()[name]
    except KeyError:
        raise ValueError('unsupported hash type ' + name)
    return factory(data)

__all__ = list(algorithms) + ['new', 'algorithms']
