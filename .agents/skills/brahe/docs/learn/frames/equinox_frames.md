# GCRF ↔ MOD ↔ TOD Transformations

MOD and TOD are the classical equinox-based Earth frames. Brahe defines them from the GCRF using the selected precession-nutation model, IAU 2006/2000A by default, together with the loaded Earth orientation data, and they are available both as pairwise functions and through the frame router as `CelestialFrame.MOD` / `CelestialFrame.TOD`.

## Reference Frames

### Mean Equator and Equinox of Date (MOD)

MOD is defined by the mean equator and mean equinox of date: the frame bias and precession from the GCRF, with no nutation applied. It is the intermediate frame

$$[\mathrm{MOD}] = P \, B \, [\mathrm{GCRF}]$$

in the [SOFA C transformation cookbook](https://www.iausofa.org/s/sofa_pn_c.pdf) Appendix p. A4 summary table, where $P$ is precession and $B$ is the frame bias. It corresponds to the mean-of-date frame in [NASA TP-20220014814](https://ntrs.nasa.gov/citations/20220014814).

### True Equator and Equinox of Date (TOD)

TOD is defined by the true equator and true equinox of date: nutation applied on top of MOD, giving the intermediate frame

$$[\mathrm{TOD}] = N \, P \, B \, [\mathrm{GCRF}]$$

in the same cookbook table, where $N$ is the nutation matrix. TOD is the frame in which the classical equation of the equinoxes and Greenwich apparent sidereal time are defined.

## Relationship to the CIO-Based Chain

The SOFA cookbook gives two equivalent factorizations of the transformation between the GCRF and the ITRF.

The CIO-based form is

$$[\mathrm{ITRF}] = W \, R_3(\mathrm{ERA}) \, C \, [\mathrm{GCRF}]$$

and the equinox-based form is

$$[\mathrm{ITRF}] = W \, R_3(\mathrm{GAST}) \, N \, P \, B \, [\mathrm{GCRF}]$$

In both equations $W$ is polar motion, $C$ is the CIO-based bias-precession-nutation matrix used by [GCRF ↔ ITRF Transformations](gcrf_itrf.md), and $N$, $P$, $B$ are the classical nutation, precession, and frame bias matrices of the equinox chain. Brahe evaluates the IAU 2006/2000A precession-nutation model by default. The truncated IAU 2000B model (IAU 2000 precession with the abridged IAU 2000B nutation series) is selectable with a single global setting that applies to every subsequent transformation; see [Precession-Nutation Model](precession_nutation_model.md). Greenwich apparent sidereal time ($\mathrm{GAST}$) is $\mathrm{ERA}$ minus the equation of the origins taken from the same combined nutation-precession-bias matrix used to reach TOD. As a result, converting a state from GCRF to ITRF through TOD agrees with the direct GCRF to ITRF transformation at the microarcsecond level.

## Velocities

MOD and TOD are treated as non-rotating relative to the GCRF: their precession and nutation rates are below $10^{-11}$ rad/s, under $10^{-4}$ m/s in low Earth orbit, so state transforms among GCRF, MOD, and TOD rotate position and velocity by the same matrix. This differs from EME2000, whose bias rotation relative to the GCRF is exactly fixed; MOD and TOD rotate slowly relative to the GCRF, and that rate is neglected here. The TOD to ITRF transformation includes the Earth rotation transport term, exactly as the GCRF to ITRF transformation does.

## GCRF to TOD

### State Vector

Transform a complete state vector (position and velocity) from GCRF to TOD:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

# Define orbital elements in degrees
# LEO satellite: 500 km altitude, sun-synchronous orbit
oe = np.array(
    [
        bh.R_EARTH + 500e3,  # Semi-major axis (m)
        0.01,  # Eccentricity
        97.8,  # Inclination (deg)
        15.0,  # Right ascension of ascending node (deg)
        30.0,  # Argument of periapsis (deg)
        45.0,  # Mean anomaly (deg)
    ]
)

epc = bh.Epoch(2024, 1, 1, 12, 0, 0.0, time_system=bh.UTC)
print(f"Epoch: {epc}")

# Convert to GCRF Cartesian state
state_gcrf = bh.state_koe_to_eci(oe, bh.AngleFormat.DEGREES)

print("\nGCRF state vector:")
print(f"  Position: [{state_gcrf[0]:.3f}, {state_gcrf[1]:.3f}, {state_gcrf[2]:.3f}] m")
print(
    f"  Velocity: [{state_gcrf[3]:.6f}, {state_gcrf[4]:.6f}, {state_gcrf[5]:.6f}] m/s\n"
)

# Transform to TOD at the given epoch
state_tod = bh.state_gcrf_to_tod(epc, state_gcrf)

print("TOD state vector:")
print(f"  Position: [{state_tod[0]:.3f}, {state_tod[1]:.3f}, {state_tod[2]:.3f}] m")
print(f"  Velocity: [{state_tod[3]:.6f}, {state_tod[4]:.6f}, {state_tod[5]:.6f}] m/s\n")

pos_diff = np.linalg.norm(state_gcrf[0:3] - state_tod[0:3])
print(f"Position difference norm: {pos_diff:.3f} m")
```


### Rotation Matrix

Get the GCRF to TOD rotation matrix and compare it with the CIO-based bias-precession-nutation matrix:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

epc = bh.Epoch(2024, 1, 1, 12, 0, 0.0, time_system=bh.UTC)
print(f"Epoch: {epc}")

R_gcrf_to_tod = bh.rotation_gcrf_to_tod(epc)

print("\nGCRF to TOD rotation matrix:")
print(
    f"  [{R_gcrf_to_tod[0, 0]:13.10f}, {R_gcrf_to_tod[0, 1]:13.10f}, {R_gcrf_to_tod[0, 2]:13.10f}]"
)
print(
    f"  [{R_gcrf_to_tod[1, 0]:13.10f}, {R_gcrf_to_tod[1, 1]:13.10f}, {R_gcrf_to_tod[1, 2]:13.10f}]"
)
print(
    f"  [{R_gcrf_to_tod[2, 0]:13.10f}, {R_gcrf_to_tod[2, 1]:13.10f}, {R_gcrf_to_tod[2, 2]:13.10f}]\n"
)

identity = R_gcrf_to_tod @ R_gcrf_to_tod.T
print("Verify orthonormality (R @ R^T should be identity):")
print(f"  Max deviation from identity: {np.max(np.abs(identity - np.eye(3))):.2e}\n")

R_cio = bh.bias_precession_nutation(epc)
print("Comparison with the CIO-based bias-precession-nutation matrix:")
print(f"  Max element difference: {np.max(np.abs(R_gcrf_to_tod - R_cio)):.6e}")
print("\nNote: rotation_gcrf_to_tod and bias_precession_nutation share the same")
print("Celestial Intermediate Pole direction (third row) and differ only by the")
print("equation of the origins, a rotation within the equatorial plane.")
```


## TOD to GCRF

### State Vector

Transform a complete state vector (position and velocity) from TOD to GCRF:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

epc = bh.Epoch(2024, 1, 1, 12, 0, 0.0, time_system=bh.UTC)
print(f"Epoch: {epc}")

# Hard-coded TOD state vector
state_tod = np.array([6878137.0, 0.0, 0.0, 0.0, 7612.0, 0.0])

print("\nTOD state vector:")
print(f"  Position: [{state_tod[0]:.3f}, {state_tod[1]:.3f}, {state_tod[2]:.3f}] m")
print(f"  Velocity: [{state_tod[3]:.6f}, {state_tod[4]:.6f}, {state_tod[5]:.6f}] m/s\n")

# Transform to GCRF at the given epoch
state_gcrf = bh.state_tod_to_gcrf(epc, state_tod)

print("GCRF state vector:")
print(f"  Position: [{state_gcrf[0]:.3f}, {state_gcrf[1]:.3f}, {state_gcrf[2]:.3f}] m")
print(
    f"  Velocity: [{state_gcrf[3]:.6f}, {state_gcrf[4]:.6f}, {state_gcrf[5]:.6f}] m/s\n"
)

# Round trip back to TOD
state_tod_roundtrip = bh.state_gcrf_to_tod(epc, state_gcrf)

pos_err = np.linalg.norm(state_tod[0:3] - state_tod_roundtrip[0:3])
vel_err = np.linalg.norm(state_tod[3:6] - state_tod_roundtrip[3:6])
print("Round-trip error (TOD -> GCRF -> TOD):")
print(f"  Position: {pos_err:.6e} m")
print(f"  Velocity: {vel_err:.6e} m/s")
```


## GCRF to MOD

### Rotation Matrix

Get the GCRF to MOD rotation matrix and confirm it reduces to the EME2000 frame bias at J2000.0, where the precession is identity:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

epc = bh.Epoch(2024, 1, 1, 12, 0, 0.0, time_system=bh.UTC)
print(f"Epoch: {epc}")

R_gcrf_to_mod = bh.rotation_gcrf_to_mod(epc)

print("\nGCRF to MOD rotation matrix:")
print(
    f"  [{R_gcrf_to_mod[0, 0]:13.10f}, {R_gcrf_to_mod[0, 1]:13.10f}, {R_gcrf_to_mod[0, 2]:13.10f}]"
)
print(
    f"  [{R_gcrf_to_mod[1, 0]:13.10f}, {R_gcrf_to_mod[1, 1]:13.10f}, {R_gcrf_to_mod[1, 2]:13.10f}]"
)
print(
    f"  [{R_gcrf_to_mod[2, 0]:13.10f}, {R_gcrf_to_mod[2, 1]:13.10f}, {R_gcrf_to_mod[2, 2]:13.10f}]\n"
)

epc_j2000 = bh.Epoch(2000, 1, 1, 12, 0, 0.0, time_system=bh.TT)
print(f"J2000 epoch: {epc_j2000}")

R_gcrf_to_mod_j2000 = bh.rotation_gcrf_to_mod(epc_j2000)

print("\nGCRF to MOD rotation matrix at J2000:")
print(
    f"  [{R_gcrf_to_mod_j2000[0, 0]:13.10f}, {R_gcrf_to_mod_j2000[0, 1]:13.10f}, {R_gcrf_to_mod_j2000[0, 2]:13.10f}]"
)
print(
    f"  [{R_gcrf_to_mod_j2000[1, 0]:13.10f}, {R_gcrf_to_mod_j2000[1, 1]:13.10f}, {R_gcrf_to_mod_j2000[1, 2]:13.10f}]"
)
print(
    f"  [{R_gcrf_to_mod_j2000[2, 0]:13.10f}, {R_gcrf_to_mod_j2000[2, 1]:13.10f}, {R_gcrf_to_mod_j2000[2, 2]:13.10f}]\n"
)

B = bh.bias_eme2000()
print("Comparison with the EME2000 frame bias matrix at J2000:")
print(f"  Max absolute difference: {np.max(np.abs(R_gcrf_to_mod_j2000 - B)):.2e}")
print("\nNote: at J2000 the precession is identity, so MOD reduces")
print("to the constant frame bias between GCRF and EME2000.")
```


## MOD to TOD

### Rotation Matrix

Get the MOD to TOD nutation matrix and recover the nutation angle it represents:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

epc = bh.Epoch(2024, 1, 1, 12, 0, 0.0, time_system=bh.UTC)
print(f"Epoch: {epc}")

R_mod_to_tod = bh.rotation_mod_to_tod(epc)

print("\nMOD to TOD rotation matrix:")
print(
    f"  [{R_mod_to_tod[0, 0]:13.10f}, {R_mod_to_tod[0, 1]:13.10f}, {R_mod_to_tod[0, 2]:13.10f}]"
)
print(
    f"  [{R_mod_to_tod[1, 0]:13.10f}, {R_mod_to_tod[1, 1]:13.10f}, {R_mod_to_tod[1, 2]:13.10f}]"
)
print(
    f"  [{R_mod_to_tod[2, 0]:13.10f}, {R_mod_to_tod[2, 1]:13.10f}, {R_mod_to_tod[2, 2]:13.10f}]\n"
)

trace = np.trace(R_mod_to_tod)
nutation_angle = np.degrees(np.arccos((trace - 1.0) / 2.0)) * 3600.0
print(
    f"Nutation angle (rotation angle of the MOD -> TOD matrix): {nutation_angle:.3f} arcsec"
)
```


## TOD to ITRF

### State Vector

Transform a state vector from TOD to ITRF directly, and compare it with the GCRF-mediated path:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

epc = bh.Epoch(2024, 1, 1, 12, 0, 0.0, time_system=bh.UTC)
print(f"Epoch: {epc}")

# Hard-coded TOD state vector
state_tod = np.array([6878137.0, 0.0, 0.0, 0.0, 7612.0, 0.0])

print("\nTOD state vector:")
print(f"  Position: [{state_tod[0]:.3f}, {state_tod[1]:.3f}, {state_tod[2]:.3f}] m")
print(f"  Velocity: [{state_tod[3]:.6f}, {state_tod[4]:.6f}, {state_tod[5]:.6f}] m/s\n")

# Transform directly from TOD to ITRF
state_itrf_direct = bh.state_tod_to_itrf(epc, state_tod)

print("ITRF state vector (direct TOD -> ITRF):")
print(
    f"  Position: [{state_itrf_direct[0]:.3f}, {state_itrf_direct[1]:.3f}, {state_itrf_direct[2]:.3f}] m"
)
print(
    f"  Velocity: [{state_itrf_direct[3]:.6f}, {state_itrf_direct[4]:.6f}, {state_itrf_direct[5]:.6f}] m/s\n"
)

# Transform via GCRF: TOD -> GCRF -> ITRF
state_gcrf = bh.state_tod_to_gcrf(epc, state_tod)
state_itrf_via_gcrf = bh.state_gcrf_to_itrf(epc, state_gcrf)

print("ITRF state vector (via GCRF: TOD -> GCRF -> ITRF):")
print(
    f"  Position: [{state_itrf_via_gcrf[0]:.3f}, {state_itrf_via_gcrf[1]:.3f}, {state_itrf_via_gcrf[2]:.3f}] m"
)
print(
    f"  Velocity: [{state_itrf_via_gcrf[3]:.6f}, {state_itrf_via_gcrf[4]:.6f}, {state_itrf_via_gcrf[5]:.6f}] m/s\n"
)

pos_diff = np.linalg.norm(state_itrf_direct[0:3] - state_itrf_via_gcrf[0:3])
vel_diff = np.linalg.norm(state_itrf_direct[3:6] - state_itrf_via_gcrf[3:6])
print("Difference between the direct and GCRF-mediated paths:")
print(f"  Position: {pos_diff:.6e} m")
print(f"  Velocity: {vel_diff:.6e} m/s")
```


## References

- [SOFA C Transformation Cookbook](https://www.iausofa.org/s/sofa_pn_c.pdf), Sections 2.7-2.9, 3.1-3.2, 3.5-3.6, 4.1, 5.4, and Appendix p. A4
- IERS Conventions (2010), IERS Technical Note 36, Chapter 5
- NASA TP-20220014814, *Astrodynamics Convention and Modeling Reference for Lunar, Cislunar, and Libration Point Orbits*, Section 4.3.5
- Wallace, P. T. & Capitaine, N., 2006, A&A 459, 981

## See Also

- [GCRF ↔ ITRF Transformations](gcrf_itrf.md)
- [EME2000 ↔ GCRF Transformations](eme2000_gcrf.md)
- [Reference Frame Router](frame_transformations.md)
- [Reference Frames Overview](index.md)