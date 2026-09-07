# PipeMesh-RBC

A parametric Gmsh mesh generator for Direct Numerical Simulation (DNS) of Rayleigh-Bénard convection in a cylindrical enclosure using spectral-element solvers such as NekRS and Nek5000.

The generator is based on the excellent KTH PipeMesh topology by Saleh Rezaeiravesh, but extends it to applications with wall-bounded convection, where high resolution is required not only at the cylindrical sidewall but also at the top and bottom plates.

The mesh preserves the original PipeMesh cross-sectional topology while introducing a fully consistent wall-normal meshing strategy in both radial and axial directions.

---

## Features

- Cylindrical enclosure geometry
- Hexahedral spectral-element mesh
- KTH PipeMesh topology
- Automatic wall-layer construction
- Automatic transition-layer construction
- Automatic computation of:
  - wall-block radius `RB`
  - central-block radius `r`
  - azimuthal resolution `Nc`
  - axial bulk resolution `Nz_bulk`
- Geometric grading toward:
  - cylindrical wall
  - bottom plate
  - top plate
- Continuity checks between blocks
- Monotonicity checks of wall-normal spacing
- Automatic generation of a Gmsh `.geo` file
- Compatible with NekRS/Nek5000 workflows

---

## Mesh Topology

The cross-section follows the original KTH PipeMesh decomposition consisting of:

- one central inflated-square block
- four transition blocks
- four outer wall-adjacent blocks

Analogously, the axial extrusion of the cross-sectional mesh consists of:

- top boundary-layer block
- top transition block
- bulk
- bottom transition block
- bottom boundary-layer block

The resulting mesh contains only structured hexahedral elements after extrusion.

## Meshing Philosophy

The original KTH PipeMesh was designed for turbulent pipe flow and therefore resolves the cylindrical wall.

For Rayleigh-Bénard convection, the strongest gradients occur at:

- the cylindrical wall
- the heated bottom plate
- the cooled top plate

This mesh generator therefore applies the same wall-normal meshing philosophy in all directions.
This yields comparable wall-normal element sizes at all walls.

## User Inputs

The mesh is controlled by a small set of physically meaningful parameters:

```
R                   # cylinder radius
Lz                  # cylinder height

lambda_             # curved-square parameter

d_wall              # wall-adjacent element size

NB                  # elements in wall block
NM                  # elements in transition block

compressRatio_B     # grading in wall block
compressRatio_M     # grading in transition block

priority            # continuity or monotonicity
```

Typical values:

```
R = 0.5
Lz = 1.0

lambda_ = 0.30

NB = 1
NM = 8

compressRatio_B = 0.85
compressRatio_M = 0.87
```

# Wall-Normal Grading
## Boundary-layer block

The wall-normal element sizes are

```
d_wall
d_wall*qB
d_wall*qB²
...
```

with
$$q_B = \frac{1}{\mathrm{compressRatio}_B}.$$


The wall-block thickness is

$$h_B = \sum_{i=0}^{NB-1} d_{wall} q_B^i$$

The radius of the wall-block interface is then

$$R_B = R - h_B .$$


## Transition block

The first transition-layer element continues the grading:

$$d_{T,1} = d_{wall} q_B^{NB}.$$

Within the transition block, along the coordinate axes:

$$d_{T,k} = d_{T,1} q_M^{k-1}$$

with

$$q_M = \frac{1}{\mathrm{compressRatio}_M}$$


The transition-block thickness along the coordinate axes becomes

$$h_M = \sum_{k=1}^{NM} d_{T,k}.$$

# Automatic Computation of $r$

The radius $r$ of the circle passing through the edges of the deformed-square central block is computed automatically. The corner points of the central block are located at

$$\left( \pm \frac{r}{\sqrt2}, \pm \frac{r}{\sqrt2} \right).$$

The arcs defining the curved sides of the central block have centers

$$(0,\pm\lambda R), (\pm\lambda R,0).$$

The central-block half-thickness along the coordinate axes ($r_\mathrm{axis}$) satisfies

$$r_\mathrm{axis} = RB - h_M .$$

Using elementary geometry and the law of cosines, one obtains

$$r = -\frac{\lambda R}{\sqrt2} + \sqrt{ R_{arc}^2 - \frac{(\lambda R)^2}{2} }$$

where

$$R_{arc} = r_{axis} + \lambda R.$$


# Automatic Computation of $N_c$

Continuity between the core block and the transition block is enforced along the coordinate axes.
The curved core-block boundary intersects the $x$ and $y$ axes at the radial distance from the origin 

$$r_{axis} = R_B - h_M.$$

The element size in the core block is then

$$\Delta_c = \frac{2r_{axis}} {N_c-1},$$

where $N_c-1$ is the 1D number of elements in the core block along the $x$ and $y$ axis. It is also the azimuthal resolution of the outer rings per quadrant. This azimuthal/core-block resolution is automatically chosen as

$$N_c = \left\lfloor \frac{2r_{axis}} {d_{T,last}} +1 \right\rfloor,$$

where

$$d_{T,last}$$

is the largest transition-layer element along the $x$ and $y$ axis (at the interface with the core block).

# Automatic Computation of `Nz_bulk`

The axial mesh consists of

- bottom wall block
- bottom transition block
- bulk
- top transition block
- top wall block


The remaining bulk height is

$h_{bulk} = L_z - 2(h_B+h_M).$

Two candidate values are considered:

$$ N_{z,1} = \left\lfloor \frac{h_\mathrm{bulk}} {d_\mathrm{T,last}} \right\rfloor $$
$$ N_{z,2} = \left\lceil \frac{h_\mathrm{bulk}} {d_\mathrm{T,last}} \right\rceil $$

The corresponding element-size ratios at the transition-to-core interface are checked for:

- continuity of the element size (within the prescribed compression ratio/growth rate)
- monotonicity of the element size variation with respect to wall distance

A user-configurable priority flag selects between them.

## Continuity Criterion

A size ratio, e.g. $d_\mathrm{bulk} / d_\mathrm{T,last}$, is considered continuous if

$$\mathrm{compressRatio} \le \frac{d_\mathrm{bulk}}{d_\mathrm{T,last}} \le \frac1{\mathrm{compressRatio}}.$$

This criterion is used at:

- wall block ↔ transition block
- transition block ↔ bulk block

## Monotonicity Criterion

The wall-normal element size should not decrease when moving away from a wall.

The corresponding ratio must satisfy

$$\frac{d_\mathrm{bulk}}{d_\mathrm{T,last}} \ge 1 - \mathrm{tol.}$$

with a relative tolerance adjusted with respect to the compress ratio:

$$\mathrm{tol} = \frac{|1-\mathrm{compressRatio_M}|} {100}.$$


# Physical Groups

The generated mesh consists of the outer boundaries (walls) with the following group names:

- `bottom`: heated bottom plate (base)
- `top`: cooled top plate
- `side`: cylindrical wall

and the interior fluid volume (named `flowDomain`). These names can be mapped directly to NekRS boundary conditions. See the comment from the original KTH `pipeMesh.geo` file:

> BC tag of the surfaces are assigned in accordance with what is added in usrdat2() routine in case.usr. This is in accordance with the requirements by gmsh2nek. See the following link: https://github.com/yhaomin2007/Nek5000/tree/master/gmsh2nek_sourcecode/gmsh2nek/

although the link does not seem to work anymore.

# Generated Files

Running

```python generate_pipe_rbc.py```

creates a [GMSH](http://gmsh.info//) script

`pipe_rbc.geo`

which can be meshed using either the GMSH GUI or the CLI with

`gmsh pipe_rbc.geo -3 -order 2`

producing the mesh file

`pipe_rbc.msh`

that can be converted to Nek5000/NekRS or other solver formats.

# Typical Workflow

```
python generate_pipe_rbc.py

gmsh pipe_rbc.geo -3

gmsh2nek
```

# Origin

This mesh generator is based on **KTH PipeMesh** by Saleh Rezaeiravesh (salehr@kth.se) and extends the original pipe-flow mesh design to wall-bounded thermal convection problems.

The mesh generator as well as this documentation was mostly generated by a Large Language Model (LLM) *GPT* using MS Copilot (basic subscription) on September 3-4, 2026. As a consequence, the codes and especially this documentation migth suffer from some "Absence of Intelligence" (AI). Apologies for that, but humans were too lazy to write this repository themselves.

# Intended Applications
- Rayleigh-Bénard natural convection in cylindrical enclosures
- DNS with NekRS/Nek5000
- High-order spectral-element simulations

