#!/usr/bin/env python3
"""parse_timss2015_hours.py -- exhibit TIMSS 2015 (9.1, G4) en PDF: heures totales et heures de maths par an.
Le .xls renvoie HTTP 406; le PDF est lu a la place. Auto-verification: le CSV n'est ecrit que si 6 pays sentinelles
(valeurs 2015 relevees le 2026-10-20: FR 193, DE 147, PL 112, FI 115, JP 151, KR 100) concordent exactement."""
import re, sys, hashlib, subprocess, urllib.request
from pathlib import Path
import pandas as pd

RAW, OUT = Path("data/raw"), Path("data/processed")
URL = ("https://timssandpirls.bc.edu/timss2015/international-results/wp-content/uploads/filebase/mathematics/"
       "9.-classroom-instruction/9_1_math-instructional-time-spent-on-mathematics-grade-4.pdf")
PDF = RAW / "timss2015_instruction_time_g4.pdf"
SENT = {"France": 193, "Germany": 147, "Poland": 112, "Finland": 115, "Japan": 151, "Korea": 100}
PAT = re.compile(r"^(?P<c>[A-Za-z][^\d]*?(?:\s*\(\d\))?)\s+(?:[rsy]\s+)?(?P<t>\d{3,4})\s*\((?P<tse>\d+\.?\d*)\)\s*(?:[rsy]\s+)?"
                 r"(?P<m>\d{2,3})\s*\((?P<mse>\d+\.?\d*)\)")


def get_text(path):
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages)
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    except Exception:
        return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True).stdout


def parse_lines(text):
    rows, stop = [], False
    for line in text.splitlines():
        if "Benchmarking" in line:
            stop = True
        m = PAT.match(line.strip())
        if m:
            name = re.sub(r"\s+", " ", m.group("c")).strip()
            rows.append(dict(country_raw=name, total_hours=float(m.group("t")), total_se=float(m.group("tse")),
                             math_hours=float(m.group("m")), math_se=float(m.group("mse")), benchmarking=stop))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    data = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read()
    PDF.write_bytes(data)
    print(f"{len(data)} octets; sha256 {hashlib.sha256(data).hexdigest()[:16]}; debut {data[:5]!r}")
    text = get_text(PDF)
    lines = [l for l in text.splitlines() if l.strip()]
    print(f"{len(lines)} lignes de texte; 22 premieres:")
    for l in lines[:22]:
        print("   ", l[:150])
    df = parse_lines(text)
    print(f"\n{len(df)} lignes parsees (dont benchmarking: {int(df.benchmarking.sum()) if len(df) else 0})")
    bad = []
    for k, v in SENT.items():
        got = df[df.country_raw.str.startswith(k)].math_hours.tolist()
        ok = bool(got) and got[0] == v
        print(f"  sentinelle {k}: attendu {v}, lu {got[:1]} -> {'OK' if ok else 'ECART'}")
        if not ok:
            bad.append(k)
    if bad or len(df) < 40:
        print("\nAUCUN CSV ECRIT: auto-verification echouee ou trop peu de lignes. Lignes non reconnues (aide):")
        for l in lines[:60]:
            if not PAT.match(l.strip()):
                print("   ?", l[:150])
        sys.exit(1)
    df.to_csv(OUT / "timss2015_math_hours_g4.csv", index=False)
    print("\nCSV ecrit: data/processed/timss2015_math_hours_g4.csv")
