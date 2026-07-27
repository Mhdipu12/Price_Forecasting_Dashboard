"""Flip every meaningful control on every page and confirm nothing breaks."""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

failures = []


def check(name, at):
    if at.exception:
        failures.append(name)
        print(f"[FAIL] {name}")
        for ex in at.exception:
            print(f"       {ex.type}: {ex.message}")
    else:
        print(f"[ OK ] {name}")


def fresh(page, timeout=180):
    at = AppTest.from_file(str(ROOT / page), default_timeout=timeout)
    at.run()
    return at


# ---------------------------------------------------------------- Home
at = fresh("Home.py")
for opt in ["Actual prices", "Rebased to 100"]:
    at.radio[0].set_value(opt).run()
    check(f"Home · scale={opt}", at)

# ---------------------------------------------------- Historical Analysis
page = "pages/1_Historical_Analysis.py"
at = fresh(page)
for period in ["Full history", "Last 3 years", "Last 12 months", "Last 6 months"]:
    at.selectbox[1].set_value(period).run()
    check(f"Historical · period={period}", at)

at = fresh(page)
for c in at.selectbox[0].options:
    at.selectbox[0].set_value(c).run()
    check(f"Historical · commodity={c}", at)

at = fresh(page)
for freq in ["Daily", "Weekly", "Monthly", "Annual"]:
    at.radio[0].set_value(freq).run()
    check(f"Historical · inflation freq={freq}", at)

at = fresh(page)
at.checkbox[0].set_value(True).run()
check("Historical · rebase on", at)

# ------------------------------------------------------------- Forecast
page = "pages/2_Forecast.py"
at = fresh(page)
for opt in at.selectbox[1].options:
    at.selectbox[1].set_value(opt).run()
    check(f"Forecast · model={opt}", at)

at = fresh(page)
for c in at.selectbox[0].options:
    at.selectbox[0].set_value(c).run()
    check(f"Forecast · commodity={c}", at)

at = fresh(page)
at.checkbox[0].set_value(False).run()
check("Forecast · hide confidence interval", at)

at = fresh(page)
at.sidebar.slider[0].set_value(7).run()
check("Forecast · horizon=7", at)
at.sidebar.slider[0].set_value(60).run()
check("Forecast · horizon=60", at)

at = fresh(page)
at.sidebar.toggle[0].set_value(True).run()
check("Forecast · dark charts", at)

# ------------------------------------------------------------ Inflation
page = "pages/3_Inflation.py"
at = fresh(page)
for freq in [90, 365, 1825]:
    at.select_slider[0].set_value(freq).run()
    check(f"Inflation · window={freq}", at)

at = fresh(page)
for c in at.selectbox[0].options:
    at.selectbox[0].set_value(c).run()
    check(f"Inflation · commodity={c}", at)

# these radios use format_func, so AppTest reports formatted labels -
# set the underlying values directly
at = fresh(page)
for h in [30, 60]:
    at.radio(key="infl_h").set_value(h).run()
    check(f"Inflation · future horizon={h}", at)
    at.radio(key="basket_h").set_value(h).run()
    check(f"Inflation · basket horizon={h}", at)

at = fresh(page)
for t in at.toggle:
    if t.key != "dark_charts":
        t.set_value(not t.value).run()
        check("Inflation · toggle flipped", at)

# ----------------------------------------------------- Model Comparison
page = "pages/4_Model_Comparison.py"
at = fresh(page)
for metric in at.radio[0].options:
    at.radio[0].set_value(metric).run()
    check(f"Comparison · metric={metric}", at)

at = fresh(page)
at.toggle[1].set_value(True).run()
check("Comparison · hide naive baseline", at)

at = fresh(page)
at.multiselect[0].set_value([at.multiselect[0].options[0]]).run()
check("Comparison · single commodity", at)

at = fresh(page)
for c in at.selectbox[0].options:
    at.selectbox[0].set_value(c).run()
    check(f"Comparison · diagnostics for {c}", at)

# ------------------------------------------------------------ Insights
page = "pages/5_Insights.py"
at = fresh(page)
for h in [7, 30, 60]:
    at.sidebar.slider[0].set_value(h).run()
    check(f"Insights · horizon={h}", at)

# ----------------------------------------------------------- Downloads
page = "pages/6_Downloads.py"
at = fresh(page)
for kind in at.selectbox[1].options:
    at.selectbox[1].set_value(kind).run()
    check(f"Downloads · chart={kind}", at)

at = fresh(page)
for scope in at.radio[0].options:
    at.radio[0].set_value(scope).run()
    check(f"Downloads · scope={scope}", at)

at = fresh(page)
at.multiselect[0].set_value([]).run()
check("Downloads · empty commodity selection", at)

print()
if failures:
    print(f"{len(failures)} INTERACTION(S) FAILED: {failures}")
    sys.exit(1)
print("ALL INTERACTIONS PASSED")
