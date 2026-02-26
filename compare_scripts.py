"""
Compare the three SatMagSim scripts: structure, GMAT usage, and features.
Run from project root: python compare_scripts.py
"""
import ast
import os

scripts = [
    ("SatMagSim_Base.py", "Base (sade temel)"),
    ("SatMagSim.py", "Core (dengeli fizik)"),
    ("SatMagSim_Extended.py", "Extended (geniş kabiliyet)"),
]

def count_defs_classes(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    defs = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
    classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    return defs, classes

def grep_count(path, *patterns):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return [text.count(p) for p in patterns]

print("=" * 70)
print("SCRIPT COMPARISON (SatMagSim)")
print("=" * 70)

for filename, label in scripts:
    path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.isfile(path):
        print(f"\n{label}: FILE NOT FOUND")
        continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = len(f.readlines())
    defs, classes = count_defs_classes(path)
    gmat_clear = "gmat.Clear()" in open(path, encoding="utf-8", errors="replace").read()
    fm_module = "fm = gmat.Construct" in open(path, encoding="utf-8", errors="replace").read() and "\n# Define the force model" in open(path, encoding="utf-8", errors="replace").read()
    # Force model at module level: look for "fm = gmat.Construct" not inside a function (simplified: check if it appears before "def run_simulation" or "def run_calculations")
    content = open(path, encoding="utf-8", errors="replace").read()
    idx_fm = content.find("fm = gmat.Construct")
    idx_run_sim = content.find("def run_simulation(")
    idx_run_calc = content.find("def run_calculations(")
    fm_at_module = (idx_fm >= 0 and (idx_run_sim < 0 or idx_fm < idx_run_sim) and (idx_run_calc < 0 or idx_fm < idx_run_calc))
    impulsive = "impulsive_" in content
    load_script = "LoadScript" in content
    initial_kepler = "initial_Kepler" in content
    update_from_file = "update_satellite_params_from_file" in content
    coord_combo = "Local" in content and "Spherical" in content and "CTkComboBox" in content

    print(f"\n--- {label} ({filename}) ---")
    print(f"  Lines: {lines}  |  Functions: {defs}  |  Classes: {classes}")
    print(f"  gmat.Clear() at module level: {gmat_clear}")
    print(f"  GMAT force model at module level: {fm_at_module}")
    print(f"  Impulsive maneuver (spherical/local): {impulsive}")
    print(f"  gmat.LoadScript (external script): {load_script}")
    print(f"  initial_Kepler.txt / update from file: {initial_kepler} / {update_from_file}")
    print(f"  Coordinate combo (Local/Spherical): {coord_combo}")

print("\n" + "=" * 70)
