"""Name keys: a name reduced for matching (pure string functions shared by the domain libraries).

`name_key` reduces a well name to letters and digits, folding the Norwegian letters, a leading `N` before the licence digits and the zero padding of the well number.  `unit_key_of_name`
reduces a stratigraphic unit or an interpretation pick name the same way.  Moved here from the biostratigraphy code so that the petrophysics and facies code need not import it.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def name_key(text: Any) -> str:
    """A name reduced to letters and digits, upper case, ASCII (the Norwegian letters folded), without a leading `N` before the licence digits: `N15/9-F-11 A`, `15/9-F11A` and `15/9-F-11 A` give the same key."""
    t = str(text or "")
    t = t.replace("Ø", "O").replace("ø", "o").replace("Å", "A").replace("å", "a").replace("Æ", "AE").replace("æ", "ae")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Za-z0-9]+", "", t).upper()
    t = re.sub(r"^N(?=\d)", "", t)
    return re.sub(r"(?<=F)0+(?=\d)", "", t)                      # F-04 and F-4 are one wellbore


def unit_key_of_name(text: Any) -> str:
    """A unit or pick name reduced for matching: upper case, ASCII, without the trailing `Top` / `Base` word of an interpretation pick and without punctuation (`Sleipner Fm. Top` and `SLEIPNER FM` give one key)."""
    t = re.sub(r"\b(top|base)\b\.?$", "", str(text or "").strip(), flags=re.I).strip()
    m = re.match(r"(.*?)\b(?:fm|gp|mbr|sgp)\b", t, flags=re.I)             # `Hugin Fm. VOLVE`, `Heather Fm. Sand` -> `Hugin`, `Heather` (the interpretation's variants of a unit take its age)
    return name_key(m.group(1) if m and m.group(1).strip() else t)
