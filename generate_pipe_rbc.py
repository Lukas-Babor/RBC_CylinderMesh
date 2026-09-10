#!/usr/bin/env python3

import math
from pathlib import Path
from string import Template

# ============================================================
# USER INPUT
# ============================================================

# Geometry parameters
R = 0.5
Lz = 1.0

# Physics parameters
Re_tau = 180.0
eta_bulk = 0.003

# Resolution targets
dy_plus_wall = 1.0
bulk_res_Kolmogorov = 2.0

# Mesh parameters
NB = 1
compressRatio_B = 0.85
compressRatio_M = 0.87
lambda_ = 0.30
AR_max = 5.0
priority = "monotonicity"   # monotonicity | continuity

# File names
geo_template = "pipe_rbc.geo.j2"
geo_output = "pipe_rbc.geo"

# Computed mesh parameters
d_wall = dy_plus_wall * Lz / Re_tau
d_bulk = bulk_res_Kolmogorov * eta_bulk

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def geometric_series(d0, q, n):
    return [d0 * q**i for i in range(n)]

def cumsum(lst,factor=1.0):
    '''Cumulative sum of a list of floats (not suitable for 
    integers or large arrays).'''
    total = 0.0
    result = []
    for x in lst:
        total += x * factor
        result.append(total)
    return result

# ============================================================
# WALL BLOCK
# ============================================================

qB = 1.0 / compressRatio_B
qM = 1.0 / compressRatio_M

wall_elems = geometric_series(d_wall, qB, NB)
hB = sum(wall_elems)
RB = R - hB

wall_elems_top = list(reversed(wall_elems))
wall_bottom_coords = cumsum(wall_elems, factor=1/hB)
wall_top_coords = cumsum(wall_elems_top, factor=1/hB)
wall_counts = [1] * NB

# ============================================================
# TRANSITION BLOCK
# ============================================================

d_trans_first = wall_elems[-1] * qB
NM = math.ceil(1 + math.log(d_bulk/d_trans_first) / math.log(qM))
trans_elems = geometric_series(d_trans_first, qM, NM)
hM = sum(trans_elems)
d_trans_last = trans_elems[-1]

trans_elems_top = list(reversed(trans_elems))
trans_bottom_coords = cumsum(trans_elems, factor=1/hM)
trans_top_coords = cumsum(trans_elems_top, factor=1/hM)
trans_counts = [1] * NM

# ============================================================
# COMPUTE r
# ============================================================

sqrt2 = math.sqrt(2.0)
rax = RB - hM
R_arc = rax + lambda_ * R
r = -lambda_*R/sqrt2 + math.sqrt(R_arc**2 -(lambda_*R)**2/2)

# ============================================================
# COMPUTE Nc
# ============================================================

Nc = math.floor(2*rax/d_trans_last+1)
delta_core = 2*rax/(Nc-1)
ratio_core = delta_core/d_trans_last

# ============================================================
# AXIAL STRUCTURE
# ============================================================

h_bulk = Lz - 2.0 * (hB + hM)

if h_bulk <= 0:
    raise RuntimeError(
        "Boundary-layer blocks occupy entire height.")

# ============================================================
# BULK CANDIDATES
# ============================================================

Nz1 = max(1, math.floor(h_bulk / d_trans_last))
Nz2 = max(1, math.ceil(h_bulk / d_trans_last))

d_bulk1 = h_bulk / Nz1
d_bulk2 = h_bulk / Nz2

ratio1 = d_bulk1 / d_trans_last
ratio2 = d_bulk2 / d_trans_last

tol = abs(1.0 - compressRatio_M) / 100.0

candidate1 = {
    "name"        : "floor",
    "Nz"          : Nz1,
    "d_bulk"      : d_bulk1,
    "ratio"       : ratio1,
    "continuity"  : (1.0 - tol <= ratio1 <= qM + tol),
    "monotonicity": (ratio1 >= 1.0 - tol)
}

candidate2 = {
    "name"        : "ceil",
    "Nz"          : Nz2,
    "d_bulk"      : d_bulk2,
    "ratio"       : ratio2,
    "continuity"  : (compressRatio_M-tol <= ratio2 <= qM+tol),
    "monotonicity": (ratio2 >= 1.0 - tol)
}

# ============================================================
# SELECT BULK CANDIDATE
# ============================================================

if candidate1["continuity"] and candidate1["monotonicity"]:

    selected = candidate1
    selection_reason = "candidate 1 satisfies both conditions"

elif candidate2["continuity"] and candidate2["monotonicity"]:

    selected = candidate2
    selection_reason = """
    candidate 1 failed (probably violates continuity)
    candidate 2 satisfies both conditions (exact match)"""

elif candidate1["monotonicity"] and candidate2["continuity"]:

    if priority == "monotonicity":

        selected = candidate1
        selection_reason = (
            "conflict resolved in favour of monotonicity")

    elif priority == "continuity":

        selected = candidate2
        selection_reason = (
            "conflict resolved in favour of continuity")

    else:

        print(f"WARNING: Unknown priority '{priority}'. "
            "Falling back to candidate 1.")

        selected = candidate1
        selection_reason = "unknown priority setting"

else:

    selected = candidate1
    selection_reason = "fallback to candidate 1"


Nz_bulk = selected["Nz"]

# ============================================================
# AXIAL BLOCK LOCATIONS
# ============================================================

z0 = 0.0

z1 = hB
z2 = hB + hM

z3 = Lz - hB - hM
z4 = Lz - hB

z5 = Lz

# ============================================================
# REPORT
# ============================================================

print() # Header
print("=" * 60)
print("PIPE RBC MESH REPORT")
print("=" * 60)

print(f"""
INPUT PARAMETERS:

R                      = {R}
Lz                     = {Lz}
d_wall                 = {d_wall}
NB                     = {NB}
NM                     = {NM}
compressRatio_B        = {compressRatio_B:.6f}
compressRatio_M        = {compressRatio_M:.6f}
lambda_                = {lambda_:.6f}

BLOCK SIZES:

RB                     = {RB:.8f}
r                      = {r:.8f}
r_axis                 = {rax:.8f}
wall layer thickness   = {hB:.8e}
transition thickness   = {hM:.8e}

CORE BLOCK MESH:

Nc                     = {Nc}
core element sizes     = {delta_core:.8e}
size ratio at core edge= {ratio_core:.6f}

SELECTION OF AXIAL RESOLUTION IN CORE BLOCK:

Candidate 1 (floor)
  Nz_bulk       = {candidate1['Nz']}
  ratio         = {candidate1['ratio']:.6f}
  continuity    = {candidate1['continuity']}
  monotonicity  = {candidate1['monotonicity']}

Candidate 2 (ceil)
    Nz_bulk       = {candidate2['Nz']}
    ratio         = {candidate2['ratio']:.6f}
    continuity    = {candidate2['continuity']}
    monotonicity  = {candidate2['monotonicity']}

Selected candidate = {selected['name']}
Selection reason   = {selection_reason}

""")

print("=" * 60) # Footer

# ============================================================
# GEO GENERATION
# ============================================================

template = Template(Path(geo_template).read_text())

wall_counts_str = ",".join(str(c) for c in wall_counts)
trans_counts_str = ",".join(str(c) for c in trans_counts)
wall_bottom_coords_str = ",".join(f"{c:.8g}" for c in wall_bottom_coords)
trans_bottom_coords_str = ",".join(f"{c:.8g}" for c in trans_bottom_coords)
wall_top_coords_str = ",".join(f"{c:.8g}" for c in wall_top_coords)
trans_top_coords_str = ",".join(f"{c:.8g}" for c in trans_top_coords)

geo_text = template.substitute(
    R=R,
    r=r,
    RB=RB,
    Lz=Lz,
    Nc=Nc,
    NB=NB,
    NM=NM,
    lambda_=lambda_,
    compressRatio_B=compressRatio_B,
    compressRatio_M=compressRatio_M,
    Nz_bulk=Nz_bulk,
    z0=z0,
    z1=z1,
    z2=z2,
    z3=z3,
    z4=z4,
    z5=z5,
    wall_counts=wall_counts_str,
    trans_counts=trans_counts_str,
    wall_bottom_coords=wall_bottom_coords_str,
    trans_bottom_coords=trans_bottom_coords_str,
    wall_top_coords=wall_top_coords_str,
    trans_top_coords=trans_top_coords_str
)

Path(geo_output).write_text(geo_text)

print(f"\nGenerated: {geo_output}")