# -*- coding: utf-8 -*-
from __future__ import (print_function, unicode_literals, division, absolute_import)  # We require Python 2.6 or later
import sys
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
if PY2:
    try:
        from future import standard_library
        standard_library.install_aliases()
        from builtins import *
        from builtins import str
        from builtins import map
        from builtins import object
        reload(sys)
        sys.setdefaultencoding('utf8')
    except ImportError:
        pass

import logging
from . import logger as log_manager