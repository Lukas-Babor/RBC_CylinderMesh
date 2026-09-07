# PipeMesh-RBC

A parametric hexahedral mesh generator for **Rayleigh-Bénard convection in cylindrical enclosures**, designed for high-order spectral-element solvers such as [**NekRS**](https://nekrs.readthedocs.io/en/latest/) and [**Nek5000**](https://github.com/Nek5000/Nek5000).

The mesh generator is based on the excellent [**KTH PipeMesh**](https://github.com/KTH-Nek5000/PipeMesh) topology by Saleh Rezaeiravesh (salehr@kth.se), but extends it to wall-bounded thermal convection problems, where boundary layers must be resolved not only at the cylindrical sidewall, but also at the heated bottom plate and the cooled top plate.

The generator automatically constructs a structured hexahedral mesh with graded resolution near all solid walls and produces a ready-to-mesh [Gmsh](https://gmsh.info/) geometry script.

## Main Features

✅ Structured hexahedral mesh

✅ Spectral-element-friendly topology

✅ Cylindrical geometry

✅ Boundary-layer refinement near all walls

✅ Geometric wall-normal grading

✅ Automatic element-size matching between mesh blocks

✅ Compatible with NekRS / Nek5000 workflows

✅ Based on the proven KTH PipeMesh cross-sectional topology

---

# Block Structure

The generated mesh consists of:

### Radial decomposition

```text
cylindrical wall
│
boundary-layer block
│
transition block
│
inflated-square core
```

### Axial decomposition

```text
top plate
│
boundary-layer block
│
transition block
│
bulk
│
transition block
│
boundary-layer block
│
bottom plate
```

The resulting mesh contains only structured hexahedral elements.

docs/images/cross_section.svg

docs/images/walls_3d.svg

---

# Quick Start

## Generate the Gmsh geometry

```bash
python generate_pipe_rbc.py
```

This creates

```text
pipe_rbc.geo
```

using the parameters specified in the Python script.

---

## Generate the mesh

Using the Gmsh GUI:

```bash
gmsh pipe_rbc.geo
```

or from the command line:

```bash
gmsh pipe_rbc.geo -3 -order 2
```

This generates

```text
pipe_rbc.msh
```

---

## Visualize the mesh

Using Gmsh:

```bash
gmsh pipe_rbc.msh
```

or ParaView:

```bash
paraview
```

and open

```text
pipe_rbc.msh
```

---

## Convert to NekRS / Nek5000

```bash
gmsh2nek
```

The generated physical groups are already prepared for typical Nek workflows.

---

# Parameters You Will Most Likely Want to Change

For most applications, only a few parameters need to be adjusted.

---

## Geometry

```python
R  = 0.5
Lz = 1.0
```

where

- `R` is the cylinder radius
- `Lz` is the cylinder height

---

## Wall Resolution

```python
d_wall = ...
```

This is the thickness of the element immediately adjacent to all walls. Decreasing `d_wall` increases wall resolution. This is usually the most important parameter (to achieve the desired $y^+$ value of the near-wall nodes).

---

## Number of Boundary-Layer Elements

```python
NB = ...
```

Number of elements in the wall-adjacent block.

Increase `NB` if:

- higher Rayleigh numbers are considered,
- higher boundary-layer resolution is desired.

---

## Number of Transition Elements

```python
NM = ...
```

Controls the thickness of the transition region between the boundary-layer block and the core region. Increasing `NM` (with fixed `compressRatio_M`) increases the size of elements in the bulk (relative to the wall-adjacent elements), shrinks the core block and, in consequence, decreases the azimuthal resolution.

---

## Grading Strength

```python
compressRatio_B = 0.85
compressRatio_M = 0.87
```

Smaller values produce stronger geometric growth of element size with increasing wall distance. `compressRatio_B` controls the wall-adjacent boundary block, and `compressRatio_M` controls the transition block.

Typical values are:

```python
0.80 – 0.95
```

---

## Central-Block Shape

```python
lambda_ = 0.30
```

Controls the shape of the inflated-square central block. The default value reproduces the original KTH PipeMesh quite closely.

---

## Continuity vs Monotonicity

```python
priority = "monotonicity"
```

Possible values:

```python
"monotonicity"
"continuity"
```

This only becomes relevant if the automatically computed bulk resolution cannot simultaneously satisfy:

- continuity of element size,
- monotonic growth of element size away from the walls.

The flag selects which of these reguirements has priority.

---

# All User Inputs

The only parameters that must be specified are:

```python
R
Lz

lambda_

d_wall

NB
NM

compressRatio_B
compressRatio_M

priority
```



Everything else is computed automatically.

---

# Mesh Topology

The cross-section follows the original KTH PipeMesh decomposition, consisting of:

- one central inflated-square block,
- four transition blocks (composing one transition O-ring),
- four outer wall-adjacent blocks (composing one boundary-layer O-ring).

The entire cross-section is extruded into five axial regions:

```text
top wall block
top transition block
bulk
bottom transition block
bottom wall block
```

---

# Physical Groups

The generated mesh contains the following physical groups:

| Group | Description |
|---------|---------|
| `bottom` | heated bottom plate |
| `top` | cooled top plate |
| `side` | cylindrical wall |
| `flowDomain` | fluid volume |

These names can be mapped directly to NekRS/Nek5000 boundary conditions.

---

# Typical Workflow

```bash
python generate_pipe_rbc.py

gmsh pipe_rbc.geo -3 -order 2

gmsh2nek
```

---

# Meshing Philosophy

The original KTH PipeMesh was developed for turbulent pipe-flow DNS.

For Rayleigh-Bénard convection, strong gradients occur at:

- the cylindrical wall,
- the heated bottom plate,
- the cooled top plate.

This generator therefore applies the same wall-normal meshing philosophy everywhere:

```text
wall
│
boundary-layer block
│
transition block
│
core
```

The goal is to obtain comparable wall-normal resolution at all solid boundaries.

---

# Implementation Details

This section explains how the mesh is generated internally.

Users who only want to generate meshes can safely skip it.

---

## Wall-Normal Grading

### Boundary-Layer Block

Element sizes are generated as a geometric series:

```text
d_wall
d_wall*qB
d_wall*qB²
...
```

where

```math
q_B=\frac{1}{\mathrm{compressRatio}_B}.
```

The resulting wall-block thickness is

```math
h_B=\sum_{i=0}^{NB-1} d_{wall}q_B^i.
```

The wall-block interface radius becomes

```math
R_B=R-h_B.
```

---

### Transition Block

The transition-layer grading continues the same progression:

```math
d_{T,1}=d_{wall}q_B^{NB}.
```

and

```math
d_{T,k}=d_{T,1}q_M^{k-1}
```

where

```math
q_M=\frac{1}{\mathrm{compressRatio}_M}.
```

The transition-block thickness is

```math
h_M=\sum_{k=1}^{NM} d_{T,k}.
```

---

## Automatic Computation of the Core Radius

The radius `r` of the circle passing through the corners of the inflated-square core block is computed automatically.

The transition thickness along the coordinate axes satisfies

```math
r_{axis}=R_B-h_M.
```

Using elementary geometry and the law of cosines:

```math
r=
-\frac{\lambda R}{\sqrt2}
+
\sqrt{
R_{arc}^2
-
\frac{(\lambda R)^2}{2}
}
```

where

```math
R_{arc}=r_{axis}+\lambda R.
```

---

## Automatic Computation of `Nc`

Continuity between the transition block and the core block is enforced along the coordinate axes.

The core element size is

```math
\Delta_c=
\frac{2r_{axis}}
     {N_c-1}.
```

The azimuthal resolution is automatically chosen as

```math
N_c=
\left\lfloor
\frac{2r_{axis}}
     {d_{T,last}}
+1
\right\rfloor.
```

---

## Automatic Computation of `Nz_bulk`

The remaining bulk height is

```math
h_{bulk}
=
L_z-2(h_B+h_M).
```

Two candidate values are considered:

```math
N_{z,1}
=
\left\lfloor
\frac{h_{bulk}}
     {d_{T,last}}
\right\rfloor
```

and

```math
N_{z,2}
=
\left\lceil
\frac{h_{bulk}}
     {d_{T,last}}
\right\rceil.
```

The generator automatically evaluates:

- continuity,
- monotonicity,

and selects the preferred candidate according to the user-specified priority.

---

## Continuity Criterion

A size ratio $\Delta_2/\Delta_1$ is considered acceptable if

```math
\mathrm{compressRatio}
\le \frac{\Delta_2}{\Delta_1} \le
\frac1{\mathrm{compressRatio}}.
```

This criterion is applied at:

- wall block ↔ transition block
- transition block ↔ bulk block

---

## Monotonicity Criterion

Element sizes should not decrease when moving away from a wall.

The ratio therefore satisfies

```math
\frac{d_{bulk}}
     {d_{T,last}}
\ge 1-\mathrm{tol}
```

where

```math
\mathrm{tol}
=
\frac{|1-\mathrm{compressRatio}_M|}
     {100}.
```

---

# Origin

This mesh generator is based on the original [**KTH PipeMesh**](https://github.com/KTH-Nek5000/PipeMesh) developed by

**Saleh Rezaeiravesh**  
salehr@kth.se

and extends the original pipe-flow mesh topology to wall-bounded thermal convection problems.

Large parts of both the mesh generator and this documentation were developed with extensive assistance from Microsoft Copilot (GPT-based LLMs) during September 2026. Consequently, the repository may occasionally exhibit episodes of *Artificial Non-Intelligence*. Bug reports, corrections, and improvements are therefore very welcome.

---

# Intended Applications

- Rayleigh-Bénard natural convection in cylindrical enclosures
- DNS with NekRS/Nek5000
- High-order spectral-element simulations
- Research and educational use