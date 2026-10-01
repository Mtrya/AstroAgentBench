# Reference Frame Router

`CelestialFrame` is a single enum spanning every reference frame in Brahe &mdash; Earth-centered, lunar, Martian, barycentric, and generic NAIF-ID variants &mdash; and three router functions (`rotation_frame_to_frame`, `position_frame_to_frame`, `state_frame_to_frame`) that convert between *any* two of them. The router is the frame machinery underlying multibody numerical propagation; see [Cislunar and Lunar Propagation](../orbit_propagation/numerical_propagation/cislunar_lunar_propagation.md) and [Propagation Around Other Central Bodies](../orbit_propagation/numerical_propagation/other_central_bodies.md) for the propagation side.

## Available Frames

The **transformation source** column names how each frame's orientation is realized: `native` frames are computed from models compiled into Brahe (no kernel), `SPICE` frames are evaluated from a loaded NAIF kernel. Re-centering between frames with different origins is a separate step resolved through the loaded SPK kernels in the global registry (last-loaded-wins for overlapping segments); the default `de440s` ephemeris is loaded automatically when no SPK is resident.

| Frame | Kind | NAIF ID (If Any) | Transformation source |
|---|---|---|---|
| `GCRF` | Inertial | 399 | ICRF-aligned identity |
| `ITRF` | Earth-fixed | 399 | IAU 2006/2000A precession-nutation with EOP (native, model selectable) |
| `EME2000` | Inertial | 399 | Frame bias (native) |
| `MOD` | Inertial | 399 | IAU 2006 bias-precession (native, model selectable) |
| `TOD` | Inertial | 399 | IAU 2006/2000A bias-precession-nutation with EOP (native, model selectable) |
| `TEME` | Inertial | 399 | GMST 1982 anchored true equator, mean equinox of date (native) |
| `Centered(center, TODofEpoch(epoch))` | Inertial | `center` | TOD rotation frozen at `epoch` |
| `Centered(center, TEMEofEpoch(epoch))` | Inertial | `center` | TEME rotation frozen at `epoch` |
| `LCI` | Inertial | 301 | ICRF-aligned identity |
| `LFPA` | Moon-fixed | 301 | DE440 binary PCK (SPICE) |
| `LFME` | Moon-fixed | 301 | DE440 PA + constant PA&rarr;ME rotation (native) |
| `MCI` | Inertial | 499 | ICRF-aligned identity |
| `MCMF` | Mars-fixed | 499 | IAU/WGCCRE analytic (native) |
| `EMBI` | Inertial | 3 | ICRF-aligned identity |
| `SSBI` | Inertial | 0 | ICRF-aligned identity |
| `EMR` | Rotating | 3 | SPK-derived, analytic (native) |
| `SER` | Rotating | &mdash; (synthetic barycenter) | SPK-derived, analytic (native) |
| `GSE` | Rotating | 399 | SPK-derived, analytic (native) |
| `BodyCenteredICRF(naif_id)` | Inertial | `naif_id` | ICRF-aligned identity |
| `BodyFixedIAU(naif_id)` | Body-fixed | `naif_id` | IAU/WGCCRE analytic (native) |
| `BodyFixedPCK(center, frame_id)` | Body-fixed | `center` | Loaded binary PCK (SPICE) |
| `BodyFixedCustom(center, key)` | Body-fixed | `center` | User rotation callback (native) |

The NAIF ID column gives the NAIF integer ID of the body each frame is centered on; it is the ID used to resolve the frame's origin through the SPK kernels when re-centering. For `BodyFixedCustom`, `center` is that same center NAIF ID, while `key` is an integer handle naming a rotation callback function previously registered with `register_custom_frame` &mdash; see [Generic NAIF-ID Variants](#generic-naif-id-variants) below.

See [Lunar Reference Frames](lunar_frames.md) and [Mars Reference Frames](mars_frames.md) for `LCI`/`LFPA`/`LFME` and `MCI`/`MCMF` respectively, and [Synodic Reference Frames](synodic_frames.md) for `EMR`/`SER`/`GSE`.

## Router Functions

`rotation_frame_to_frame`, `position_frame_to_frame`, and `state_frame_to_frame` take a `from` frame, a `to` frame, and an epoch (plus a position/state vector for the latter two), and dispatch through a hub-and-spoke design: the source is rotated into ICRF axes centered on its own origin, re-centered to the target's origin if the two frames have different centers, and rotated into the target's axes. Same-frame calls short-circuit to an identity/no-op with no SPK query at all; same-center calls (e.g. `GCRF` &harr; `ITRF`, `LCI` &harr; `LFPA`) skip the re-centering step and are bit-identical to the underlying pairwise function.

The example below routes a `GCRF` (Earth-centered) state into `LCI` (Moon-centered) with `state_frame_to_frame` &mdash; a cross-center conversion that re-centers through the DE440 ephemeris &mdash; and takes a rotation-only `GCRF` &rarr; `MCMF` transform with `rotation_frame_to_frame`, which uses the compiled-in Mars model and needs no kernel.


```
import numpy as np

import brahe as bh

# Initialize EOP and the DE440s ephemeris used to re-center GCRF (Earth) to
# LCI (Moon) inside the router.
bh.initialize_eop()
bh.load_common_spice_kernels()

epc = bh.Epoch.from_datetime(2024, 3, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)

# A GCRF (Earth-centered inertial) state, built from Keplerian elements.
oe = np.array([bh.R_EARTH + 500e3, 0.01, 45.0, 15.0, 30.0, 45.0])
x_gcrf = bh.state_koe_to_eci(oe, bh.AngleFormat.DEGREES)

# state_frame_to_frame routes through ICRF and re-centers Earth -> Moon, so the
# same physical state is now expressed relative to the Moon.
x_lci = bh.state_frame_to_frame(
    bh.CelestialFrame.GCRF, bh.CelestialFrame.LCI, epc, x_gcrf
)

# rotation_frame_to_frame returns only the 3x3 axis rotation (no re-centering);
# GCRF -> MCMF uses the compiled-in WGCCRE Mars model and needs no kernel.
r_gcrf_to_mcmf = bh.rotation_frame_to_frame(
    bh.CelestialFrame.GCRF, bh.CelestialFrame.MCMF, epc
)

print(f"Epoch: {epc}")
print("\nGCRF state (Earth-centered inertial):")
print(
    f"  Position (km): [{x_gcrf[0] / 1e3:.3f}, {x_gcrf[1] / 1e3:.3f}, {x_gcrf[2] / 1e3:.3f}]"
)
print("\nSame state expressed in LCI (Moon-centered inertial):")
print(
    f"  Position (km): [{x_lci[0] / 1e3:.3f}, {x_lci[1] / 1e3:.3f}, {x_lci[2] / 1e3:.3f}]"
)

# The GCRF->LCI position shift equals the Moon's distance from Earth (~384,400 km),
# since both frames share ICRF axes and differ only in origin.
offset = np.linalg.norm(x_lci[:3] - x_gcrf[:3])
print(f"\nGCRF->LCI position offset (km): {offset / 1e3:.1f}")
assert 350_000e3 < offset < 410_000e3

# The returned rotation is a proper orthonormal direction cosine matrix.
assert np.allclose(r_gcrf_to_mcmf @ r_gcrf_to_mcmf.T, np.eye(3), atol=1e-9)
print("\nExample validated successfully!")
```


## Generic NAIF-ID Variants

Four variants cover bodies without a dedicated named frame:

- **`BodyCenteredICRF(naif_id)`**: ICRF-aligned axes centered on `naif_id`. Requires an SPK segment for `naif_id` when translating to/from a differently-centered frame.
- **`BodyFixedIAU(naif_id)`**: the compiled-in IAU/WGCCRE body-fixed rotation for `naif_id`, centered on `naif_id` itself. Requires no kernel. `iau_rotation_model_ids()` returns the supported NAIF IDs: the Sun, Mercury, Venus, the Moon (a lower-precision IAU model, distinct from `LFPA`), Mars, the Galilean moons (Io/Europa/Ganymede/Callisto), Phobos, Deimos, Enceladus, Titan, Jupiter, Saturn, Uranus, and Neptune.
- **`BodyFixedPCK { center, frame_id }`**: a body-fixed frame evaluated from a loaded binary PCK's `frame_id` (e.g. 31008 for `MOON_PA_DE440`), centered on `center`. The PCK must already be loaded &mdash; the router never auto-loads a generic PCK.
- **`BodyFixedCustom { center, key }`**: a body-fixed frame evaluated from a user-supplied rotation callback. `center` is the NAIF ID of the body the frame is centered on (used for SPK re-centering, exactly like the other variants). `key` is an arbitrary integer handle, unrelated to NAIF IDs: it names a callback function previously registered with `register_custom_frame(key, rotation, omega=None)`, and the router looks the callback up by `key` at evaluation time. `rotation` is a proper callback function mapping an epoch to the 3&times;3 ICRF&rarr;body-fixed rotation matrix; `omega` is an optional second callback mapping an epoch to the frame's angular velocity vector (rad/s), which supplies the velocity transport term (derived numerically by central differencing of `rotation` when omitted). This enables support for user-defined orientation models, enabling the framework to extend to additional bodies without needing hard-coded support for them in the library. For a body with no catalogued NAIF ID, self-assign a unique negative `center`, mirroring NAIF's convention for non-catalogued objects. See [Propagation Around Other Central Bodies](../orbit_propagation/numerical_propagation/other_central_bodies.md) for a worked registration example.

## Kernel Requirements Per Frame

| Frame(s) | Kernel needed | Auto-loaded? |
|---|---|---|
| `GCRF`, `ITRF`, `EME2000`, `MOD`, `TOD`, `TEME`, `TODofEpoch(epoch)`, `TEMEofEpoch(epoch)` | None (SOFA-based) | N/A |
| `LCI` (rotation only) | None (ICRF-aligned) | N/A |
| `LCI`, `MCI`, `EMBI`, `SSBI` (translation to/from another center) | `de440s` SPK | Yes, on first `spk_*` query |
| `MCI`, `MCMF` (translation to/from another center) | `de440s` SPK + `mar099s` satellite ephemeris | Yes, on first Mars body-center query |
| `LFPA`, `LFME` | `moon_pa_de440` binary PCK | Yes, on first LCI &harr; LFPA/LFME conversion |
| `MCMF` (rotation only) | None (compiled-in WGCCRE polynomial) | N/A |
| `EMR`, `SER`, `GSE` | `de440s` SPK | Yes, on first query |
| `BodyFixedIAU(naif_id)` | None (compiled-in), if `naif_id` is in `iau_rotation_model_ids()` | N/A |
| `BodyFixedPCK { .. }` | The named binary PCK | No; must be loaded explicitly with `load_spice_kernel` |
| `BodyFixedCustom { .. }` | None (user callback) | N/A |

The lunar PCK auto-load is a narrow exception to the general SPICE registry rule that binary PCKs are never auto-initialized (see [SPICE Kernels](../spice/index.md)); it exists because `LFPA`/`LFME` have no meaning without `moon_pa_de440` loaded, so every lunar body-fixed conversion loads it transparently on first use. `MCI`/`MCMF` are centered on the Mars body center (NAIF 499); a translation to or from another center resolves the body-center leg through the `mar099s` satellite ephemeris kernel, which is auto-loaded the same way.

## Axes and Centers

`CelestialFrame` pairs one origin with one orientation. `FrameCenter` names the origin alone: `Body(naif_id)` for a catalogued body or system barycenter (or any raw ID, including a self-assigned negative one), and `Barycenter(primary, secondary)` for the GM-weighted barycenter of a two-body pair that the synodic frames compute analytically. `FrameAxes` names the orientation alone &mdash; `ICRF`, `EME2000`, `MOD`, `TOD`, `TEME`, `ITRF`, `LunarPA`, `LunarME`, `MarsFixed`, `EMR`, `SER`, `GSE`, and the parameterized `BodyFixedIAU(naif_id)`, `BodyFixedPCK(frame_id)`, `BodyFixedCustom(key)`, `Synodic(primary, secondary)`, `TODofEpoch(epoch)`, and `TEMEofEpoch(epoch)`. `CelestialFrame::centered(center, axes)` builds the pair, returning a named shorthand when one exists (`centered(399, EME2000)` is `EME2000`; `centered(301, ICRF)` is `LCI`) and the generic `Centered { center, axes }` variant otherwise. `center()` and `axes()` split any frame back into its two halves, so `centered(f.center(), f.axes()) == f` holds for every frame Brahe produces.

`center()` returns the semantic `FrameCenter` rather than the raw integer `center_naif_id()` returns. `FrameCenter::naif_id()` is the identity the router translates on, so a `Barycenter` and the raw synthetic ID encoding the same pair reach the same origin; `centered` canonicalizes on that ID, and stores the `FrameCenter` as given when the pair has no named form. `FrameCenter::name()` prints the NAIF body name, the raw ID for an uncatalogued body, or `BARYCENTER(primary, secondary)`.

This split matters because most named frames only cover one origin: `EME2000`, `MOD`, `TOD`, `TEME`, and `ITRF` are welded to Earth, `MCI`/`MCMF` to Mars, and so on. `Centered` lifts that restriction, pairing any orientation with any NAIF center.

In Python a trajectory's `frame` attribute is a `ReferenceFrame`, and its `celestial_frame` attribute gives the underlying `CelestialFrame` whose `axes` and `center` split it into its two halves.

Converting between two frames that share a center is a rotation only and never touches an SPK kernel; converting between frames centered on different bodies also translates by the vector between those centers, resolved through the loaded ephemeris exactly as any other cross-center router call. The example below loads an OEM whose `CENTER_NAME` is Mars, converts a sample to `MCI` (same center, rotation only) and to `GCRF` (different center, needs the `de440s` kernel loaded below):


```
import brahe as bh
from brahe.ccsds import OEM

bh.initialize_eop()
bh.load_common_spice_kernels()

oem = OEM.from_file("test_assets/ccsds/oem/OEMExample4.txt")
seg = oem.segments[0]
print(f"REF_FRAME = {seg.ref_frame}, CENTER_NAME = {seg.center_name}")

traj = oem.to_trajectories()[0]
print(f"\nTrajectory frame: {traj.frame}")

# The trajectory's frame is a CelestialFrame naming the (center, axes)
# pair; celestial_frame unwraps the ReferenceFrame and axes and center split
# the result back into its two halves.
traj_frame = traj.frame.celestial_frame
print(f"  Axes:   {traj_frame.axes}")
print(f"  Center: {traj_frame.center.name}")

# Same-center conversion: EME2000 to MCI is a rotation only, both centered on
# Mars.
traj_mci = traj.to_frame(bh.CelestialFrame.MCI)
epc, x_mci = traj_mci.get(0)
print(f"\nState at {epc} in MCI (Mars-centered):")
print(
    f"  Position (km): [{x_mci[0] / 1e3:.3f}, {x_mci[1] / 1e3:.3f}, {x_mci[2] / 1e3:.3f}]"
)
print(f"  Velocity (m/s): [{x_mci[3]:.3f}, {x_mci[4]:.3f}, {x_mci[5]:.3f}]")

# Cross-center conversion: EME2000/Mars to GCRF/Earth adds the Earth-Mars
# translation from the loaded SPK kernels.
traj_gcrf = traj.to_frame(bh.CelestialFrame.GCRF)
_, x_gcrf = traj_gcrf.get(0)
print(f"\nState at {epc} in GCRF (Earth-centered):")
print(
    f"  Position (km): [{x_gcrf[0] / 1e3:.3e}, {x_gcrf[1] / 1e3:.3e}, {x_gcrf[2] / 1e3:.3e}]"
)
print(f"  Velocity (m/s): [{x_gcrf[3]:.3f}, {x_gcrf[4]:.3f}, {x_gcrf[5]:.3f}]")

assert traj_frame.center == bh.NAIFId.MARS
assert traj_frame.axes == bh.FrameAxes.EME2000
print("\nExample validated successfully!")
```


## See Also

- [Lunar Reference Frames](lunar_frames.md)
- [Mars Reference Frames](mars_frames.md)
- [Synodic Reference Frames](synodic_frames.md)
- [ECI &harr; ECEF Transformations](eci_ecef.md) - Earth-only frame transformations
- [Cislunar and Lunar Propagation](../orbit_propagation/numerical_propagation/cislunar_lunar_propagation.md) - `Moon`/`EMB` central bodies and force-model defaults
- [Propagation Around Other Central Bodies](../orbit_propagation/numerical_propagation/other_central_bodies.md) - `Mars`, custom bodies, and user-defined body-fixed frames
- [SPICE Kernels](../spice/index.md) - Kernel loading and the underlying SPK/PCK registry
- [Reference Frame Router API Reference](../../library_api/frames/router.md)
- [Force Model Configuration API Reference](../../library_api/propagators/force_model_config.md)