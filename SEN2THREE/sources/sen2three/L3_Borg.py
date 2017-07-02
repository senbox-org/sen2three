#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

class Borg(object):
    _shared = {}
    def __new__(cls, *p, **k):
        inst = object.__new__(cls)
        inst.__dict__ = cls._shared
        return inst
