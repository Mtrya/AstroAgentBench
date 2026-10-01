# Frame Graph

`ReferenceFrame` is the top-level frame identity in Brahe. It extends `CelestialFrame`, the router covered in [Reference Frame Router](frame_transformations.md), to frames that are scoped to a specific object: a spacecraft's orbit-relative frame (`RTN`, `LVLH`, ...) or a body/sensor/actuator frame (`SC_BODY`, `CSS_1`, ...). `rotation_frame_to_frame`, `position_frame_to_frame`, and `state_frame_to_frame` (and their batch forms) accept either a `CelestialFrame` or a `ReferenceFrame` for `from`/`to`, so a call site that only ever uses `CelestialFrame` needs no changes to keep working.

A `ReferenceFrame` is one of three variants:

- **Celestial**: any `CelestialFrame` (`GCRF`, `ITRF`, `LFPA`, ...). Evaluable analytically from an epoch alone, exactly as in the router.
- **Orbit-relative**: a local orbital frame of one object (`RTN`, `LVLH`, `NTW`, `TNW`, `PQW`, `EQW`, `SEZ`, `VNC`, or `NSW`), either rotating with the orbit or frozen as an inertial snapshot at each evaluation epoch. Only `RTN` has an axes derivation today; the other kinds are valid frame identities, which is what parsing a data file needs, but a transform through one raises until [issue #452](https://github.com/duncaneddy/brahe/issues/452) adds the remaining derivations.
- **Body**: an object-local frame with no global transformation, such as a spacecraft body frame, a sensor, an actuator, or an instrument.

Orbit-relative and body frames carry an object identity, a plain string (e.g. `"LRO"`, `"2024-123A"`) kept separate from NAIF or NORAD IDs. Constructing one through a family method, `ReferenceFrame.RTN("SC")` or `ReferenceFrame.CSS("SC", "1")`, binds it to that object directly.

## Bound vs. Unbound

A frame is **bound** when it can be evaluated: every `CelestialFrame` is bound by construction, and an orbit-relative or body frame is bound once it carries an object. Constructing one with no object gives the unbound form instead: `ReferenceFrame.body(None, ...)` or `ReferenceFrame.orbit_relative(..., object=None)` in Python, and converting a bare `BodyFrame` or `OrbitRelativeFrame` in Rust. An unbound frame is a pure label, useful for parsing a data file's frame column before an object identity is known. `is_bound()` and `object()` report which case a given `ReferenceFrame` is in.

Calling any transform on an unbound frame raises immediately, naming the frame and the constructor that binds it, rather than failing later inside a registry lookup.

## Registering Objects

An orbit-relative or body frame's origin is the registered state of the object it is bound to. `register_object(name, provider, frame)` accepts either a callable `Epoch -> state` (position and velocity, meters and m/s, expressed in `frame`) or an `OrbitTrajectory`, and stores it under `name` in a single global object registry, keyed by object identity rather than NAIF ID: kernel data only enters this registry through an explicit provider such as `register_object_from_naif`, never implicitly.

Parsing a CCSDS OEM is the common case, and `OEM.register_for(name)` is a one-liner for it: it converts the ephemeris to a trajectory and registers it under `name`, in the frame the OEM itself declares (`GCRF`, `ITRF`, or `EME2000`).


```python
import numpy as np

import brahe as bh
from brahe.ccsds import OEM

bh.clear_object_registry()

# OEM.register_for is a one-liner: it converts the ephemeris segment to a
# trajectory, wraps it as a state provider, and registers it under a name.
oem = OEM.from_file("test_assets/ccsds/oem/OEMExample5.txt")
oem.register_for("ISS")
print(f"Registered objects: {bh.registered_objects()}")

# The registered object anchors ReferenceFrame.RTN("ISS"): its origin is the object's
# GCRF position, interpolated from the OEM ephemeris.
epc = oem.segments[0].start_time + 300.0
x_rtn_origin = bh.state_frame_to_frame(
    bh.ReferenceFrame.RTN("ISS"), bh.CelestialFrame.GCRF, epc, np.zeros(6)
)
print(f"\nISS position at {epc}: {x_rtn_origin[:3] / 1e3} km")

bh.clear_object_registry()
print("\nExample validated successfully!")
```


## Registering Orientation Chains

A body frame's orientation is not derived from any model; it is registered explicitly with `register_frame(frame, parent, provider)`. `parent` must itself resolve to a celestial root: either it is a `CelestialFrame` directly, or it is a body frame that is already registered and whose own parent chain terminates at one. Re-registering an existing frame replaces its entry, and the replacement's parent chain is revalidated, so a change that would cycle back through the frame itself is rejected.

`provider` supplies the rotation and, optionally, the angular velocity of `frame` relative to `parent`, expressed in `frame`. Two kinds of provider are available today:

- A **constant attitude** (a `Quaternion`, `RotationMatrix`, `EulerAngle`, or `EulerAxis`) for a sensor mounted at a fixed orientation. Its angular velocity relative to its parent is zero by construction.
- A **callable**, `Epoch -> rotation matrix`, optionally paired with a second callable returning the angular velocity. This covers time-varying orientations such as a slewing sensor or an articulated appendage.

An orientation chain driven by an attitude ephemeris (AEM), analogous to `OEM.register_for`, ships in a later release; a time-varying orientation is registered as a callable in the meantime.

## Worked Example: A Sun Vector in a Sensor Frame

The example below registers a spacecraft as an object, builds a two-link orientation chain (`SC_BODY` off `GCRF`, then a coarse sun sensor `CSS_1` off `SC_BODY`), and routes the Sun's GCRF position through both links with `position_frame_to_frame`. Body frames share their object's origin exactly, with no lever arm between an object's center and the sensor frames mounted on it. The example confirms this by routing the spacecraft's own position into `CSS_1` and getting the origin back. Querying an unregistered link (`CSS_2`, never registered) raises an error naming the missing frame and the `register_frame` call that would supply it.


```python
import numpy as np

import brahe as bh

bh.clear_frame_registry()
bh.clear_object_registry()

# A body or orbit-relative frame that carries no object name is only a label:
# it describes a set of axes and nothing more. Binding it to a named object
# makes it resolvable against that object's registered data. A celestial frame
# such as CelestialFrame.GCRF is resolvable on its own. The family
# staticmethods (ReferenceFrame.RTN, ReferenceFrame.SC_BODY,
# ReferenceFrame.CSS, ...) bind an object directly, while
# ReferenceFrame.body(None, ...) leaves the frame unbound.
rtn = bh.ReferenceFrame.RTN("SC")
label = bh.ReferenceFrame.body(None, bh.BodyFrame.SC_BODY())
print(f"{rtn}: bound={rtn.is_bound()}, object={rtn.object()}")
print(f"{label}: bound={label.is_bound()}, object={label.object()}")

# Register "SC" as an object: a callable Epoch -> state (m, m/s) in GCRF. An
# OrbitTrajectory, or an OEM's `register_for` one-liner (see the CCSDS OEM
# docs), registers the same way.
oe = np.array([bh.R_EARTH + 500e3, 0.001, 97.8, 15.0, 30.0, 45.0])
x_sc = bh.state_koe_to_eci(oe, bh.AngleFormat.DEGREES)
bh.register_object("SC", lambda epc: x_sc, bh.CelestialFrame.GCRF)

# Register SC's body frame and a coarse sun sensor mounted on it. The BodyFrame
# families (SC_BODY, CSS, RW, ...) are the values of the SANA spacecraft body
# reference frame registry:
# https://sanaregistry.org/r/spacecraft_body_reference_frames/
# A constant attitude (Quaternion, RotationMatrix, EulerAngle, EulerAxis)
# registers directly; orientation chains driven by an attitude ephemeris ship
# in a later release.
q_body = bh.Quaternion(1.0, 0.0, 0.0, 0.0)
q_css = bh.EulerAxis(
    np.array([0.0, 1.0, 0.0]), 0.7, bh.AngleFormat.RADIANS
).to_quaternion()
bh.register_frame(bh.ReferenceFrame.SC_BODY("SC"), bh.CelestialFrame.GCRF, q_body)
bh.register_frame(
    bh.ReferenceFrame.CSS("SC", "1"), bh.ReferenceFrame.SC_BODY("SC"), q_css
)

# Route the Sun's GCRF position through GCRF -> SC_BODY -> CSS_1.
epc = bh.Epoch.from_date(2024, 3, 1, bh.TimeSystem.UTC)
sun_gcrf = bh.sun_position(epc)
sun_css = bh.position_frame_to_frame(
    bh.CelestialFrame.GCRF, bh.ReferenceFrame.CSS("SC", "1"), epc, sun_gcrf
)
print(f"\nSun direction in CSS_1: {sun_css}")

# Body frames share their object's origin exactly: routing SC's own position
# into CSS_1 lands at the origin, with no lever arm applied.
sc_in_css = bh.position_frame_to_frame(
    bh.CelestialFrame.GCRF, bh.ReferenceFrame.CSS("SC", "1"), epc, x_sc[:3]
)
print(f"SC origin in CSS_1 (zero lever arm): {sc_in_css}")
np.testing.assert_allclose(sc_in_css, 0.0, atol=1e-6)

# Querying an unregistered link raises with a fix: which frame is missing and
# the register_frame call that would supply it.
try:
    bh.rotation_frame_to_frame(
        bh.CelestialFrame.GCRF, bh.ReferenceFrame.CSS("SC", "2"), epc
    )
except RuntimeError as e:
    print(f"\nMissing-link error: {e}")

bh.clear_frame_registry()
bh.clear_object_registry()
print("\nExample validated successfully!")
```


## The Rates Rule and `with_numerical_rates`

`position_frame_to_frame` needs no angular-velocity data: it only rotates and re-centers. `state_frame_to_frame` does, since converting a velocity requires the transport term $\omega \times r$ at every link in the chain. Celestial frames define their rotation rates internally, so the router supplies them without any input from you. Registered links are the other case: an orbit-relative frame takes its rate from the object's orbital motion, and a body frame takes its rate from the `OrientationProvider` registered for it. A rotation-only provider (a callable given no `omega`) reports `None` for its rate, and a state transform through that link raises rather than silently dropping the transport term.

`with_numerical_rates` can be used to add body rates for an `OrientationProvider` that does not include body rates by default: it wraps the provider so a missing rate is derived by central-differencing the rotation matrix over $\pm \text{step}/2$ seconds, using $[\omega]_\times = -\dot{R} R^\mathsf{T}$. In Python, this is the `numerical_rates_step` argument to `register_frame`, and it applies only to a callable provider; a constant attitude already has an exact zero rate and does not need it.


```python
import numpy as np

import brahe as bh

bh.clear_frame_registry()
bh.clear_object_registry()

t0 = bh.Epoch.from_date(2024, 3, 1, bh.TimeSystem.UTC)
rate = 1.0e-3  # spin rate (rad/s)


def rotation(epc):
    dt = epc - t0
    c, s = np.cos(rate * dt), np.sin(rate * dt)
    return np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])


# A rotation-only callback carries no angular velocity, so a state transform
# through it fails: the velocity transport term is otherwise undefined.
bh.register_frame(bh.ReferenceFrame.SC_BODY("SC"), bh.CelestialFrame.GCRF, rotation)
bh.register_object("SC", lambda epc: np.zeros(6), bh.CelestialFrame.GCRF)

epc = t0 + 100.0
x_gcrf = np.array([1.0e3, 2.0e3, 3.0e3, 0.0, 0.0, 0.0])
try:
    bh.state_frame_to_frame(
        bh.CelestialFrame.GCRF, bh.ReferenceFrame.SC_BODY("SC"), epc, x_gcrf
    )
except RuntimeError as e:
    print(f"Rates rule error: {e}")

# Re-registering with `numerical_rates_step` wraps the same callback so a
# missing angular velocity is derived by central differencing the rotation
# over +/- step/2 seconds; a provider that already returns rates is used
# unchanged. The state transform then succeeds.
bh.unregister_frame(bh.ReferenceFrame.SC_BODY("SC"))
bh.register_frame(
    bh.ReferenceFrame.SC_BODY("SC"),
    bh.CelestialFrame.GCRF,
    rotation,
    numerical_rates_step=1.0,
)
x_body = bh.state_frame_to_frame(
    bh.CelestialFrame.GCRF, bh.ReferenceFrame.SC_BODY("SC"), epc, x_gcrf
)
print(f"\nBody-frame state with numerical rates: {x_body}")

# Compare against a hand-differenced velocity: with_numerical_rates recovers
# the transport term from the same central-difference recipe.
delta = 0.5
r_plus = rotation(epc + delta) @ x_gcrf[:3]
r_minus = rotation(epc - delta) @ x_gcrf[:3]
v_numerical = (r_plus - r_minus) / (2.0 * delta)
np.testing.assert_allclose(x_body[3:], v_numerical, atol=1e-6)

bh.clear_frame_registry()
bh.clear_object_registry()
print("\nExample validated successfully!")
```


---

## See Also

- [ReferenceFrame / BodyFrame API Reference](../../library_api/frames/frame.md)
- [Reference Frame Router](frame_transformations.md) - `CelestialFrame` and the frame-to-frame router functions
- [CCSDS OEM](../ccsds/oem.md) - Parsing and writing OEM ephemeris files