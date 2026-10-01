# OPM — Orbit Parameter Message

An Orbit Parameter Message (OPM), defined by the [CCSDS 502.0-B-3 Orbit Data Messages standard](https://ccsds.org/Pubs/502x0b3e1.pdf), carries a single spacecraft state at one epoch — position, velocity, and optionally Keplerian elements, spacecraft parameters, maneuvers, and covariance. It is the standard format for handing off initial conditions for propagation or documenting a maneuver plan.

## Parse and Initialize a Propagator

Extract position, velocity, epoch, and spacecraft parameters from an OPM to initialize a `NumericalOrbitPropagator`:

```python
import numpy as np

import brahe as bh
from brahe.ccsds import OPM

bh.initialize_eop()
bh.initialize_sw()

# Parse OPM — use Example1 which has spacecraft mass
opm = OPM.from_file("test_assets/ccsds/opm/OPMExample1.txt")
print(f"Object: {opm.object_name} ({opm.object_id})")
print(f"Epoch:  {opm.epoch}")
print(f"Frame:  {opm.ref_frame}")

# Extract initial conditions from OPM via .state property
initial_state = opm.state  # numpy array [x, y, z, vx, vy, vz]
print("\nInitial state (ITRF):")
print(
    f"  Position: [{initial_state[0] / 1e3:.3f}, {initial_state[1] / 1e3:.3f}, {initial_state[2] / 1e3:.3f}] km"
)
print(
    f"  Velocity: [{initial_state[3]:.3f}, {initial_state[4]:.3f}, {initial_state[5]:.3f}] m/s"
)

# Build spacecraft parameters from OPM
mass = opm.mass or 500.0
drag_area = opm.drag_area or 2.0
drag_coeff = opm.drag_coeff or 2.2
srp_area = opm.solar_rad_area or 2.0
srp_coeff = opm.solar_rad_coeff or 1.3
params = np.array([mass, drag_area, drag_coeff, srp_area, srp_coeff])
print(f"\nSpacecraft params: mass={mass}kg, Cd={drag_coeff}, Cr={srp_coeff}")

# Initialize propagator from OPM state
# The message declares its state in ITRF2000; the propagator expects GCRF, and
# state_in_frame maps the declared frame through the reference frame router
state_eci = opm.state_in_frame(bh.CelestialFrame.GCRF)
prop = bh.NumericalOrbitPropagator(
    opm.epoch,
    state_eci,
    bh.NumericalPropagationConfig.default(),
    bh.ForceModelConfig.default(),
    params,
)

# Propagate for 1 orbit period (approximately)
r = np.linalg.norm(initial_state[:3])
period = 2 * np.pi * np.sqrt(r**3 / bh.GM_EARTH)
print(f"\nEstimated period: {period:.0f}s ({period / 60:.1f} min)")

target_epoch = opm.epoch + period
prop.propagate_to(target_epoch)

# Check final state
final_state = prop.current_state()
print("\nAfter 1 orbit:")
print(f"  Epoch: {prop.current_epoch()}")
print(
    f"  Position: [{final_state[0] / 1e3:.3f}, {final_state[1] / 1e3:.3f}, {final_state[2] / 1e3:.3f}] km"
)
print(
    f"  Velocity: [{final_state[3]:.3f}, {final_state[4]:.3f}, {final_state[5]:.3f}] m/s"
)
```


## Accessing OPM Data

Parse from file or string, then access the state vector, optional Keplerian elements, spacecraft parameters, covariance, and maneuvers:

```python
import brahe as bh
from brahe.ccsds import OPM

bh.initialize_eop()

# Parse OPM with Keplerian elements and maneuvers
opm = OPM.from_file("test_assets/ccsds/opm/OPMExample2.txt")

# Header
print(f"Format version: {opm.format_version}")
print(f"Originator:     {opm.originator}")
print(f"Creation date:  {opm.creation_date}")

# Metadata
print(f"\nObject name:  {opm.object_name}")
print(f"Object ID:    {opm.object_id}")
print(f"Center name:  {opm.center_name}")
print(f"Ref frame:    {opm.ref_frame}")
print(f"Time system:  {opm.time_system}")

# State vector (SI units: meters, m/s)
print(f"\nEpoch:    {opm.epoch}")
pos = opm.position
vel = opm.velocity
print(f"Position: [{pos[0] / 1e3:.4f}, {pos[1] / 1e3:.4f}, {pos[2] / 1e3:.4f}] km")
print(f"Velocity: [{vel[0]:.8f}, {vel[1]:.8f}, {vel[2]:.8f}] m/s")

# Keplerian elements
print(f"\nHas Keplerian: {opm.has_keplerian_elements}")
if opm.has_keplerian_elements:
    print(f"  Semi-major axis:    {opm.semi_major_axis / 1e3:.4f} km")
    print(f"  Eccentricity:       {opm.eccentricity:.9f}")
    print(f"  Inclination:        {opm.inclination:.6f} deg")
    print(f"  RAAN:               {opm.ra_of_asc_node:.6f} deg")
    print(f"  Arg of pericenter:  {opm.arg_of_pericenter:.6f} deg")
    print(f"  True anomaly:       {opm.true_anomaly:.6f} deg")
    print(f"  GM:                 {opm.gm:.4e} m³/s²")

# Spacecraft parameters
print(f"\nMass:           {opm.mass} kg")
print(f"Solar rad area: {opm.solar_rad_area} m²")
print(f"Solar rad coef: {opm.solar_rad_coeff}")
print(f"Drag area:      {opm.drag_area} m²")
print(f"Drag coeff:     {opm.drag_coeff}")

# Maneuvers
print(f"\nManeuvers: {len(opm.maneuvers)}")
for i, man in enumerate(opm.maneuvers):
    print(f"\n  Maneuver {i}:")
    print(f"    Epoch ignition: {man.epoch_ignition}")
    print(f"    Duration:       {man.duration} s")
    print(f"    Delta mass:     {man.delta_mass} kg")
    print(f"    Ref frame:      {man.ref_frame}")
    dv = man.dv
    print(f"    Delta-V:        [{dv[0]:.5f}, {dv[1]:.5f}, {dv[2]:.5f}] m/s")
```


## What an OPM Contains

Every OPM has a **header** (version, creation date, originator), **metadata** (object identity, center body, reference frame, time system), and a **state vector** (epoch plus position and velocity). Beyond these required parts, four optional sections can be present.

`CENTER_NAME` and `REF_FRAME` are resolved jointly: `REF_FRAME` names the state vector's orientation and `CENTER_NAME` its origin, independently of each other. `state_in_frame` converts the state vector to any other supported frame through the reference frame router; converting to a frame centered on the same body as the OPM's `CENTER_NAME` is a rotation only, while converting to a frame centered on a different body also translates through the loaded SPK kernels. A message that also declares `REF_FRAME_EPOCH` is interpreted in the of-epoch frame frozen at that epoch before `state_in_frame` converts it. See [Axes and Centers](../frames/frame_transformations.md#axes-and-centers) for the full `FrameAxes`/`CelestialFrame` picture.

**Keplerian elements** duplicate the state vector information in orbital-element form — semi-major axis, eccentricity, inclination, RAAN, argument of pericenter, and true or mean anomaly, plus $GM$. The redundancy is intentional: elements are easier for humans to review at a glance, and some receiving systems prefer them as input.

**Spacecraft parameters** record physical properties relevant to force modeling — mass, drag area and coefficient ($C_D$), and solar radiation pressure area and coefficient ($C_R$). These feed directly into atmospheric drag and SRP force models during numerical propagation.

**Maneuvers** describe planned or executed burns. Each maneuver specifies an ignition epoch, duration, delta-mass, reference frame, and three delta-V components. Multiple maneuvers are allowed, and the reference frame can differ between them (e.g., RTN for in-plane burns, EME2000 for inertial targeting).

**Covariance** provides a 6$\times$6 symmetric position-velocity covariance matrix with an optional reference frame override relative to the state vector frame.

## Maneuver Propagation

Read OPM maneuvers and apply them as impulsive delta-V events during propagation. The example message declares its state vector in the TOD frame, and `state_in_frame` converts it to GCRF through the reference frame router before it is handed to the propagator. The message's maneuver ignition epochs precede its state vector epoch, so the example schedules the maneuvers relative to the state epoch, preserving the spacing between them:

```python
import numpy as np

import brahe as bh
from brahe.ccsds import OPM

bh.initialize_eop()
bh.initialize_sw()

# Parse OPM with maneuvers
opm = OPM.from_file("test_assets/ccsds/opm/OPMExample2.txt")
print(f"Object: {opm.object_name}")
print(f"Epoch:  {opm.epoch}")
print(f"Maneuvers: {len(opm.maneuvers)}")

# Extract initial state; the OPM declares its state in the TOD frame
state_eci = opm.state_in_frame(bh.CelestialFrame.GCRF)

# Spacecraft parameters from OPM
mass = opm.mass or 500.0
params = np.array(
    [
        mass,
        opm.drag_area or 10.0,
        opm.drag_coeff or 2.3,
        opm.solar_rad_area or 10.0,
        opm.solar_rad_coeff or 1.3,
    ]
)

# Create propagator
prop = bh.NumericalOrbitPropagator(
    opm.epoch,
    state_eci,
    bh.NumericalPropagationConfig.default(),
    bh.ForceModelConfig.default(),
    params,
)

# The message's ignition epochs precede its state epoch, so maneuvers are
# scheduled relative to the state epoch, preserving the spacing between them
first_ignition = opm.maneuvers[0].epoch_ignition
scheduled_epochs = [
    opm.epoch + 3600.0 + (man.epoch_ignition - first_ignition) for man in opm.maneuvers
]


def make_callback(dv_vec, man_idx, is_rtn):
    """Create a closure that rotates the delta-V into GCRF and applies it.

    Args:
        dv_vec (numpy.ndarray): Delta-V [dv1, dv2, dv3] in the maneuver frame (m/s)
        man_idx (int): Index of the maneuver within the OPM
        is_rtn (bool): True if `dv_vec` is expressed in the RTN frame

    Returns:
        callable: Event callback returning the post-maneuver state and action
    """

    def apply_dv(epoch, state):
        dv_gcrf = bh.rotation_rtn_to_eci(state) @ dv_vec if is_rtn else dv_vec
        new_state = state.copy()
        new_state[3] += dv_gcrf[0]
        new_state[4] += dv_gcrf[1]
        new_state[5] += dv_gcrf[2]
        dv_mag = np.linalg.norm(dv_gcrf)
        print(f"  Applied maneuver {man_idx} at {epoch}: |dv|={dv_mag:.3f} m/s")
        return (new_state, bh.EventAction.CONTINUE)

    return apply_dv


# The frame bias between EME2000 (alias J2000) and GCRF is epoch-independent
r_eme2000_to_gcrf = bh.rotation_eme2000_to_gcrf()

# Add an event detector for each maneuver
for i, (man, sched_epoch) in enumerate(zip(opm.maneuvers, scheduled_epochs)):
    dv = man.dv  # [dv1, dv2, dv3] in m/s in the maneuver's ref frame
    frame = man.ref_frame

    if frame in ("J2000", "EME2000"):
        # Inertial delta-V: rotate into GCRF once, ahead of propagation
        callback = make_callback(r_eme2000_to_gcrf @ dv, i, False)
    elif frame == "RTN":
        # RTN delta-V: the rotation depends on the state at the ignition epoch
        callback = make_callback(dv, i, True)
    else:
        raise ValueError(f"Unsupported maneuver reference frame: {frame}")

    event = bh.TimeEvent(sched_epoch, f"Maneuver-{i}")
    event = event.with_callback(callback)
    prop.add_event_detector(event)
    print(
        f"  Registered maneuver {i}: epoch={sched_epoch}, frame={frame}, "
        f"|dv|={np.linalg.norm(dv):.3f} m/s"
    )

# Propagate past all maneuvers
target = scheduled_epochs[-1] + 3600.0  # 1 hour after last maneuver
print(f"\nPropagating to {target}...")
prop.propagate_to(target)

# Report final state
final = prop.current_state()
print(f"\nFinal state at {prop.current_epoch()}:")
print(
    f"  Position: [{final[0] / 1e3:.3f}, {final[1] / 1e3:.3f}, {final[2] / 1e3:.3f}] km"
)
print(f"  Velocity: [{final[3]:.3f}, {final[4]:.3f}, {final[5]:.3f}] m/s")

# Check event log
events = prop.event_log()
print(f"\nEvent log: {len(events)} events triggered")
for e in events:
    print(f"  {e}")
```


## KVN Format Example

An OPM KVN file with a state vector, Keplerian elements, and a maneuver:

```
CCSDS_OPM_VERS = 3.0
CREATION_DATE = 2024-01-15T00:00:00
ORIGINATOR = EXAMPLE

OBJECT_NAME = MY SATELLITE
OBJECT_ID = 2024-001A
CENTER_NAME = EARTH
REF_FRAME = EME2000
TIME_SYSTEM = UTC

EPOCH = 2024-01-15T00:00:00
X = 6878.137 [km]
Y = 0.000 [km]
Z = 0.000 [km]
X_DOT = 0.000 [km/s]
Y_DOT = 7.612 [km/s]
Z_DOT = 0.000 [km/s]

SEMI_MAJOR_AXIS = 6878.137 [km]
ECCENTRICITY = 0.001
INCLINATION = 0.0 [deg]
RA_OF_ASC_NODE = 0.0 [deg]
ARG_OF_PERICENTER = 0.0 [deg]
TRUE_ANOMALY = 0.0 [deg]
GM = 398600.4415 [km**3/s**2]

MAN_EPOCH_IGNITION = 2024-01-15T01:00:00
MAN_DURATION = 60.0 [s]
MAN_DELTA_MASS = -5.0 [kg]
MAN_REF_FRAME = RTN
MAN_DV_1 = 0.010 [km/s]
MAN_DV_2 = 0.000 [km/s]
MAN_DV_3 = 0.000 [km/s]
```

Note the optional unit annotations in square brackets (`[km]`, `[deg]`). Brahe strips these during parsing.

---

## See Also

- [API Reference — OPM](../../library_api/ccsds/opm.md)
- [CCSDS Data Formats](index.md) — Overview of all message types
- [Keplerian Elements](../orbits/properties.md) — Orbital element definitions
- [CCSDS 502.0-B-3](https://ccsds.org/Pubs/502x0b3e1.pdf) — Orbit Data Messages, the standard OPM implements