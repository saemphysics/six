#!/usr/bin/env python3
"""text_normalizer.py — Prep narration text for XTTS.

Converts numbers, units, symbols, and math notation into a form that
XTTS-v2 pronounces naturally. Designed for narration scripts with
scientific, engineering, or technical content.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from functools import lru_cache


# ---------------------------------------------------------------------------
# Number → words
# ---------------------------------------------------------------------------

_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
]
_SCALES = ["", "thousand", "million", "billion", "trillion"]

_DIGITS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
    "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
}


def _spell_below_1000(n: int) -> str:
    if n < 20:
        return _ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return _TENS[t] + ("-" + _ONES[o] if o else "")
    h, r = divmod(n, 100)
    out = _ONES[h] + " hundred"
    if r:
        out += " " + _spell_below_1000(r)
    return out


@lru_cache(maxsize=2048)
def _spell_int(s: str) -> str:
    s = s.lstrip("0") or "0"
    if len(s) > 15:
        # Too large for named scales — spell digit-by-digit.
        return " ".join(_DIGITS[d] for d in s)
    n = int(s)
    if n < 1000:
        return _spell_below_1000(n)
    parts: list[str] = []
    i = 0
    while n > 0:
        chunk = n % 1000
        if chunk:
            word = _spell_below_1000(chunk)
            if _SCALES[i]:
                word += " " + _SCALES[i]
            parts.append(word)
        n //= 1000
        i += 1
    return " ".join(reversed(parts))


_ORDINAL_MAP = {
    "one": "first", "two": "second", "three": "third", "four": "fourth",
    "five": "fifth", "six": "sixth", "seven": "seventh", "eight": "eighth",
    "nine": "ninth", "ten": "tenth", "eleven": "eleventh",
    "twelve": "twelfth", "thirteen": "thirteenth", "fourteen": "fourteenth",
    "fifteen": "fifteenth", "sixteen": "sixteenth",
    "seventeen": "seventeenth", "eighteen": "eighteenth",
    "nineteen": "nineteenth",
    "twenty": "twentieth", "thirty": "thirtieth", "forty": "fortieth",
    "fifty": "fiftieth", "sixty": "sixtieth", "seventy": "seventieth",
    "eighty": "eightieth", "ninety": "ninetieth",
    "hundred": "hundredth", "thousand": "thousandth",
    "million": "millionth", "billion": "billionth", "trillion": "trillionth",
}


def _ordinal_word(n: int) -> str | None:
    if n < 0:
        return None
    words = _spell_int(str(n)).split()
    if not words:
        return None
    last = words[-1]
    if "-" in last:
        head, tail = last.rsplit("-", 1)
        if tail in _ORDINAL_MAP:
            words[-1] = f"{head}-{_ORDINAL_MAP[tail]}"
            return " ".join(words)
    if last in _ORDINAL_MAP:
        words[-1] = _ORDINAL_MAP[last]
        return " ".join(words)
    return None


_FRACTION_WORDS = {
    (1, 2): "one half", (1, 3): "one third", (2, 3): "two thirds",
    (1, 4): "one quarter", (3, 4): "three quarters",
    (1, 5): "one fifth", (2, 5): "two fifths", (3, 5): "three fifths",
    (4, 5): "four fifths",
    (1, 8): "one eighth", (3, 8): "three eighths",
    (5, 8): "five eighths", (7, 8): "seven eighths",
    (1, 10): "one tenth", (3, 10): "three tenths",
    (7, 10): "seven tenths", (9, 10): "nine tenths",
    (1, 16): "one sixteenth",
}


def _fraction_word(num: str, den: str) -> str | None:
    try:
        n, d = int(num), int(den)
    except ValueError:
        return None
    if d == 0:
        return None
    if (n, d) in _FRACTION_WORDS:
        return _FRACTION_WORDS[(n, d)]
    if d == 1:
        return _spell_int(num)
    ord_word = _ordinal_word(d)
    if not ord_word:
        return None
    if n != 1 and not ord_word.endswith("s"):
        ord_word += "s"
    return f"{_spell_int(num)} {ord_word}"


# ---------------------------------------------------------------------------
# Symbol tables
# ---------------------------------------------------------------------------

_GREEK = {
    "Δ": "delta", "δ": "delta", "π": "pi",    "Π": "pi",
    "θ": "theta", "ω": "omega", "Ω": "omega", "λ": "lambda",
    "μ": "mu",    "φ": "phi",   "Φ": "phi",   "ψ": "psi",   "Ψ": "psi",
    "α": "alpha", "β": "beta",  "γ": "gamma", "ε": "epsilon",
    "σ": "sigma", "τ": "tau",   "ρ": "rho",   "ν": "nu",
    "η": "eta",   "ζ": "zeta",  "ξ": "xi",
}

# Unit symbols → spoken words.  Each rule requires a digit *before* the
# symbol (with optional whitespace), so standalone English words like
# "in", "A", or "K" are never touched.  Longer units are listed first so
# substrings (e.g. "m/s" inside "m/s^2") cannot shadow them.
_UNIT_RULES = [
    (r"(?<=\d)\s*m/s\^2\b",    " meters per second squared"),
    (r"(?<=\d)\s*m/s²\b",      " meters per second squared"),
    (r"(?<=\d)\s*m/s\b(?!\^)", " meters per second"),
    (r"(?<=\d)\s*km/h\b",      " kilometers per hour"),
    (r"(?<=\d)\s*N/m\b",       " newtons per meter"),
    (r"(?<=\d)\s*rad/s\b",     " radians per second"),
    (r"(?<=\d)\s*kWh\b",       " kilowatt hours"),
    (r"(?<=\d)\s*kHz\b",       " kilohertz"),
    (r"(?<=\d)\s*MHz\b",       " megahertz"),
    (r"(?<=\d)\s*GHz\b",       " gigahertz"),
    (r"(?<=\d)\s*Hz\b",        " hertz"),
    (r"(?<=\d)\s*kg\b",        " kilograms"),
    (r"(?<=\d)\s*Pa\b",        " pascals"),
    (r"(?<=\d)\s*kW\b",        " kilowatts"),
    (r"(?<=\d)\s*mAh\b",       " milliamp hours"),
    (r"(?<=\d)\s*dB\b",        " decibels"),
    (r"(?<=\d)\s*rpm\b",       " revolutions per minute"),
    (r"(?<=\d)\s*mph\b",       " miles per hour"),
    (r"(?<=\d)\s*km\b",        " kilometers"),
    (r"(?<=\d)\s*cm\b",        " centimeters"),
    (r"(?<=\d)\s*mm\b",        " millimeters"),
    (r"(?<=\d)\s*nm\b",        " nanometers"),
    (r"(?<=\d)\s*ft\b",        " feet"),
    (r"(?<=\d)\s*lb\b",        " pounds"),
    (r"(?<=\d)\s*oz\b",        " ounces"),
    (r"(?<=\d)\s*mi\b",        " miles"),
    (r"(?<=\d)\s*in\b",        " inches"),
    (r"(?<=\d)\s*N\b",         " newtons"),
    (r"(?<=\d)\s*J\b",         " joules"),
    (r"(?<=\d)\s*K\b",         " kelvin"),
    (r"(?<=\d)\s*W\b",         " watts"),
    (r"(?<=\d)\s*V\b",         " volts"),
    (r"(?<=\d)\s*A\b",         " amperes"),
]


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Dashes → comma pause
    text = re.sub(r"\s*[—–]\s*", ", ", text)
    text = re.sub(r"\s+--+\s+", ", ", text)

    # LaTeX leftovers
    text = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"[{}]", "", text)

    # Greek letters → names
    for sym, name in _GREEK.items():
        if sym in text:
            text = text.replace(sym, f" {name} ")

    # Currency
    text = re.sub(r"\$\s*(\d+(?:\.\d+)?)", r"\1 dollars", text)
    text = re.sub(r"€\s*(\d+(?:\.\d+)?)", r"\1 euros", text)
    text = re.sub(r"£\s*(\d+(?:\.\d+)?)", r"\1 pounds", text)

    # Percent
    text = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"\1 percent", text)

    # Temperature
    text = re.sub(r"(\d+(?:\.\d+)?)\s*°\s*C\b", r"\1 degrees Celsius", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*°\s*F\b", r"\1 degrees Fahrenheit", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*°\b", r"\1 degrees", text)

    # Time HH:MM → "H MM" (bare integers get spelled later)
    text = re.sub(r"\b(\d{1,2}):(\d{2})\b", r"\1 \2", text)

    # Ordinals (1st → first, 21st → twenty-first)
    def _ord(m: re.Match) -> str:
        word = _ordinal_word(int(m.group(1)))
        return word if word else m.group(0)
    text = re.sub(r"\b(\d+)(?:st|nd|rd|th)\b", _ord, text, flags=re.IGNORECASE)

    # Fractions (1/2 → one half)
    def _frac(m: re.Match) -> str:
        word = _fraction_word(m.group(1), m.group(2))
        return word if word else m.group(0)
    text = re.sub(r"\b(\d+)\s*/\s*(\d+)\b", _frac, text)

    # Unit symbols → words (before number spelling, so "5 kg" → "5 kilograms")
    for pattern, spoken in _UNIT_RULES:
        text = re.sub(pattern, spoken, text)

    # Scientific notation: 5 x 10^3 → "5 times ten to the power of three"
    def _sci(m: re.Match) -> str:
        mantissa, exp = m.group(1), m.group(2)
        neg = exp.startswith("-")
        exp = exp.lstrip("-")
        words = _spell_int(exp)
        return (f"{mantissa} times ten to the power of "
                f"{'minus ' if neg else ''}{words}")
    text = re.sub(r"(\d+(?:\.\d+)?)\s*[×xX]\s*10\^(-?\d+)", _sci, text)

    # Remaining caret exponents (x^4, 2^10, ...)
    def _caret(m: re.Match) -> str:
        exp = m.group(1)
        neg = exp.startswith("-")
        exp = exp.lstrip("-")
        words = _spell_int(exp)
        return f" to the power of {'minus ' if neg else ''}{words}"
    text = re.sub(r"\^(-?\d+)", _caret, text)

    # Decimal numbers (3.14 → three point one four)
    def _dec(m: re.Match) -> str:
        whole, frac = m.group(1), m.group(2)
        return (f"{_spell_int(whole)} point "
                + " ".join(_DIGITS[d] for d in frac))
    text = re.sub(r"\b(\d+)\.(\d+)\b", _dec, text)

    # Bare integers
    text = re.sub(r"\b(\d+)\b", lambda m: _spell_int(m.group(0)), text)

    # Operators (with optional surrounding whitespace)
    text = re.sub(r"\s*=\s*", " equals ", text)
    text = re.sub(r"\s*\+\s*", " plus ", text)
    text = re.sub(r"\s*×\s*", " times ", text)
    text = re.sub(r"\s*÷\s*", " divided by ", text)

    # Final cleanup
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = text.strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


# ---------------------------------------------------------------------------
# Chunking for XTTS
# ---------------------------------------------------------------------------

def _hard_split(text: str, max_chars: int) -> list[str]:
    """Split on whitespace; force-split any single token > max_chars."""
    out: list[str] = []
    cur = ""
    for w in text.split():
        cand = (cur + " " + w).strip() if cur else w
        if len(cand) > max_chars and cur:
            out.append(cur)
            cur = w
        else:
            cur = cand
    if cur:
        out.append(cur)

    final: list[str] = []
    for c in out:
        while len(c) > max_chars:
            final.append(c[:max_chars])
            c = c[max_chars:]
        if c:
            final.append(c)
    return final


def chunk_for_xtts(text: str, max_chars: int = 280) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        cand = (cur + " " + s).strip() if cur else s
        if len(cand) > max_chars and cur:
            chunks.append(cur)
            cur = s
        else:
            cur = cand
    if cur:
        chunks.append(cur)

    # Second pass: split on commas / semicolons.
    sub_chunks: list[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            sub_chunks.append(c)
            continue
        parts = re.split(r"(?<=[,;])\s+", c)
        sub = ""
        for p in parts:
            cand = (sub + " " + p).strip() if sub else p
            if len(cand) > max_chars and sub:
                sub_chunks.append(sub)
                sub = p
            else:
                sub = cand
        if sub:
            sub_chunks.append(sub)

    # Third pass: hard split on whitespace.
    final: list[str] = []
    for c in sub_chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            final.extend(_hard_split(c, max_chars))

    return final or [text.strip()]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    raw = (
        " ".join(sys.argv[1:])
        or "At 25°C, a 5 kg block moving at 10 m/s^2 needs N = 50 N "
           "and K = 300 K. The 1st test used 5 x 10^3 Hz and 3/4 of $5 "
           "for a 12% gain at 3:30."
    )
    n = normalize(raw)
    print(f"IN : {raw}")
    print(f"OUT: {n}")
    for i, c in enumerate(chunk_for_xtts(n)):
        print(f"  chunk {i + 1} ({len(c)} chars): {c}")