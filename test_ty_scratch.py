import sys
import os
sys.path.append(os.getcwd())

from discorun.wire.types import Ty
from discopy.cat import Ob

try:
    t = Ty("A")
    print(f"Type: {t!r}")
    print(f"Objects: {t.inside}")
except Exception as e:
    print(f"Error 1: {e}")

try:
    t2 = Ty(Ob("A"))
    print(f"Type 2: {t2!r}")
    print(f"Objects 2: {t2.inside}")
except Exception as e:
    print(f"Error 2: {e}")
