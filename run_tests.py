"""Execute every page headlessly and report any exception."""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

PAGES = [ROOT / "Home.py"] + sorted((ROOT / "pages").glob("*.py"))

failures = 0
for page in PAGES:
    at = AppTest.from_file(str(page), default_timeout=180)
    try:
        at.run()
    except Exception as e:
        failures += 1
        print(f"[HARNESS ERROR] {page.name}: {type(e).__name__}: {e}")
        continue

    if at.exception:
        failures += 1
        print(f"[FAIL] {page.name}")
        for ex in at.exception:
            print(f"    {ex.type}: {ex.message}")
            if getattr(ex, "stack_trace", None):
                for line in ex.stack_trace[-8:]:
                    print("      " + line.rstrip())
    else:
        counts = (f"markdown={len(at.markdown)} "
                  f"dataframe={len(at.dataframe)} "
                  f"tabs={len(at.tabs)} "
                  f"buttons={len(at.button) + len(at.download_button)}")
        warn = f"  warnings={len(at.warning)}" if len(at.warning) else ""
        print(f"[ OK ] {page.name:<32} {counts}{warn}")
        for w in at.warning:
            print(f"       warning: {w.value[:120]}")

print()
print("ALL PAGES PASSED" if failures == 0 else f"{failures} PAGE(S) FAILED")
sys.exit(1 if failures else 0)
