# -*- coding: utf-8 -*-
import os
import stat

__all__ = ["cmp","dircmp","cmpfiles"]

_cache = {}

BUFSIZE=8*1024

# filetest.cmp('backups/backup-11-08-10-2016', 'backups/backup-14-08-10-2016', shallow=False)

def cmp(f1, f2, shallow=1):
    """Compare two files.
    Arguments:
    f1 -- First file name
    f2 -- Second file name

    shallow -- Just check stat signature (do not read the files).
               defaults to 1.

    Return value:
    True if the files are the same, False otherwise.

    This function uses a cache for past comparisons and the results,
    with a cache invalidation mechanism relying on stale signatures.
    """
    s1 = _sig(os.stat(f1))
    s2 = _sig(os.stat(f2))
    if s1[0] != stat.S_IFREG or s2[0] != stat.S_IFREG:
        return False
    if shallow and s1 == s2:
        return True
    if s1[1] != s2[1]:
        return False

    outcome = _cache.get((f1, f2, s1, s2))
    if outcome is None:
        outcome = _do_cmp(f1, f2)
        if len(_cache) > 100:      # limit the maximum size of the cache
            _cache.clear()
        _cache[f1, f2, s1, s2] = outcome
    return outcome

def _sig(st):
    return (stat.S_IFMT(st.st_mode),
            st.st_size,
            st.st_mtime)

def _do_cmp(f1, f2):
    bufsize = BUFSIZE
    with open(f1, 'rb') as fp1, open(f2, 'rb') as fp2:
        # Pular começo que é sempre diferente
        fp1.read(40)
        fp2.read(40)
        while True:
            b1 = fp1.read(bufsize)
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                return True