# GCRF ↔ TEME ↔ ITRF Transformations

TEME is the true equator, mean equinox of date frame in which SGP4 expresses its output. Brahe defines it from the ITRF through Greenwich mean sidereal time on the IAU 1982 model, and it is available both as pairwise functions and through the frame router as `CelestialFrame.TEME`.

## Reference Frame

TEME is defined by the relation

$$[\mathrm{ITRF}] = W \, R_3(\mathrm{GMST}_{82}) \, [\mathrm{TEME}]$$

where $W$ is polar motion and $\mathrm{GMST}_{82}$ is Greenwich mean sidereal time on the IAU 1982 model evaluated on UT1. This is the convention of [Vallado et al., *Revisiting Spacetrack Report #3*](https://celestrak.org/publications/AIAA/2006-6753/AIAA-2006-6753-Rev3.pdf), Appendix C, which fixes the meaning of the frame SGP4 produces. Combined with the CIO-based chain

$$[\mathrm{ITRF}] = W \, R_3(\mathrm{ERA}) \, C \, [\mathrm{GCRF}]$$

from the [SOFA C transformation cookbook](https://www.iausofa.org/s/sofa_pn_c.pdf), the rotation from the GCRF is

$$[\mathrm{TEME}] = R_3(\mathrm{ERA} - \mathrm{GMST}_{82}) \, C \, [\mathrm{GCRF}]$$

where $C$ is the bias-precession-nutation matrix used by [GCRF ↔ ITRF Transformations](gcrf_itrf.md). The TEME equator is therefore the true equator of date. Its origin of right ascension is the mean equinox implied by the IAU 1982 sidereal time model, which differs from the IAU 2006 mean equinox of [MOD](equinox_frames.md) by the precession-model offset and from the true equinox of TOD by the equation of the equinoxes. The rotation from TEME to TOD is $R_3(\mathrm{GMST}_{82} - \mathrm{GAST})$, where $\mathrm{GAST}$ is Greenwich apparent sidereal time (GAST), evaluated by the frame router.

## Velocities

TEME is treated as non-rotating relative to the GCRF: its precession and nutation rates are below $10^{-11}$ rad/s, so state transforms between GCRF and TEME rotate position and velocity by the same matrix. The TEME to ITRF transformation includes the Earth rotation transport term, exactly as the GCRF to ITRF transformation does.

## SGP4 Propagator

`SGPPropagator.state` returns the raw SGP4 output in TEME. The configured output frame, `GCRF` by default, applies to `propagate_to`, the stored trajectory, and `current_state`/`initial_state`. The frame-specific accessors `state_gcrf` and `state_itrf` always return the GCRF and ITRF states respectively, using the pairwise TEME transforms, regardless of the configured output frame. `state_in_frame` likewise always returns the requested frame, converting the TEME output through the frame router.

## GCRF to TEME

### State Vector

Transform a complete state vector (position and velocity) from GCRF to TEME:


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

# Transform to TEME at the given epoch
state_teme = bh.state_gcrf_to_teme(epc, state_gcrf)

print("TEME state vector:")
print(f"  Position: [{state_teme[0]:.3f}, {state_teme[1]:.3f}, {state_teme[2]:.3f}] m")
print(
    f"  Velocity: [{state_teme[3]:.6f}, {state_teme[4]:.6f}, {state_teme[5]:.6f}] m/s\n"
)

pos_diff = np.linalg.norm(state_gcrf[0:3] - state_teme[0:3])
print(f"Position difference norm: {pos_diff:.3f} m")
```


## TEME to ITRF

### State Vector

Transform a TEME state vector from an SGP4 propagator into the ITRF:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

line1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
line2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
prop = bh.SGPPropagator.from_tle(line1, line2, 60.0)

epc = prop.epoch + 600.0
state_teme = prop.state(epc)
print(f"Epoch: {epc}")
print("TEME state vector:")
print(f"  Position: [{state_teme[0]:.3f}, {state_teme[1]:.3f}, {state_teme[2]:.3f}] m")
print(
    f"  Velocity: [{state_teme[3]:.6f}, {state_teme[4]:.6f}, {state_teme[5]:.6f}] m/s\n"
)

state_itrf = bh.state_teme_to_itrf(epc, state_teme)
print("ITRF state vector:")
print(f"  Position: [{state_itrf[0]:.3f}, {state_itrf[1]:.3f}, {state_itrf[2]:.3f}] m")
print(
    f"  Velocity: [{state_itrf[3]:.6f}, {state_itrf[4]:.6f}, {state_itrf[5]:.6f}] m/s\n"
)

speed_teme = np.linalg.norm(state_teme[3:6])
speed_itrf = np.linalg.norm(state_itrf[3:6])
print(f"Inertial speed: {speed_teme:.3f} m/s, Earth-fixed speed: {speed_itrf:.3f} m/s")
```


## SGP4 Output in TOD

`state_in_frame` converts the raw TEME output of `SGPPropagator.state` into any other router frame, here TOD, and can be compared against the `GCRF` accessor:


```python
import numpy as np

import brahe as bh

bh.initialize_eop()

line1 = "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927"
line2 = "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537"
prop = bh.SGPPropagator.from_tle(line1, line2, 60.0)

epc = prop.epoch + 600.0
state_tod = prop.state_in_frame(bh.CelestialFrame.TOD, epc)
state_gcrf = prop.state_gcrf(epc)

print(f"Epoch: {epc}")
print("TOD state vector:")
print(f"  Position: [{state_tod[0]:.3f}, {state_tod[1]:.3f}, {state_tod[2]:.3f}] m")
print(f"  Velocity: [{state_tod[3]:.6f}, {state_tod[4]:.6f}, {state_tod[5]:.6f}] m/s\n")

print("GCRF state vector:")
print(f"  Position: [{state_gcrf[0]:.3f}, {state_gcrf[1]:.3f}, {state_gcrf[2]:.3f}] m")
print(
    f"  Velocity: [{state_gcrf[3]:.6f}, {state_gcrf[4]:.6f}, {state_gcrf[5]:.6f}] m/s\n"
)

pos_diff = np.linalg.norm(state_tod[0:3] - state_gcrf[0:3])
print(f"Position difference norm: {pos_diff:.3f} m")
```


## Of-Epoch Frames

`FrameAxes.TODofEpoch(epoch)` and `FrameAxes.TEMEofEpoch(epoch)` are the TOD and TEME axes evaluated once at `epoch` and held fixed. Because the axes do not move, a frame built on them is inertial: its rotation to the GCRF is

$$R_{\mathrm{GCRF} \to \mathrm{TODofEpoch}(t_0)} = R_{\mathrm{GCRF} \to \mathrm{TOD}}(t_0)$$

for every transform epoch, and velocities transform by the same rotation with no transport term. `CelestialFrame.tod_of_epoch(epoch)` and `CelestialFrame.teme_of_epoch(epoch)` build the Earth-centered frames, and `CelestialFrame.Centered(center, axes)` pairs the axes with any other center. Two of-epoch axes are equal only when their epochs are equal, and `frame_epoch` returns the frozen epoch on both `FrameAxes` and `CelestialFrame`.

These frames are how Brahe represents a CCSDS ODM message whose `REF_FRAME` is `TOD` or `TEME` and which also carries a `REF_FRAME_EPOCH`: the message loads in the of-epoch frame and converts only when asked. The CCSDS ADM `TEMEOFEPOCH` token cannot be mapped, because ADM metadata has no keyword for the frozen epoch.

## References

- [SOFA C Transformation Cookbook](https://www.iausofa.org/s/sofa_pn_c.pdf)
- Vallado, D. A. et al., 2006, [*Revisiting Spacetrack Report #3*](https://celestrak.org/publications/AIAA/2006-6753/AIAA-2006-6753-Rev3.pdf), AIAA 2006-6753-Rev3, Appendix C
- Vallado, D. A., *Fundamentals of Astrodynamics and Applications*, 4th ed., Section 3.7

## See Also

- [GCRF ↔ ITRF Transformations](gcrf_itrf.md)
- [GCRF ↔ MOD ↔ TOD Transformations](equinox_frames.md)
- [Reference Frame Router](frame_transformations.md)
- [Reference Frames Overview](index.md)