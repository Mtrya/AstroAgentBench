# AEM — Attitude Ephemeris Message

An Attitude Ephemeris Message (AEM) carries a spacecraft's time-ordered attitude history as one or more segments, each holding a sequence of attitude data lines at strictly increasing epochs. It is the attitude-message counterpart to the OEM: the standard format for exchanging attitude ephemerides between agencies and operators. The message is defined by the [CCSDS 504.0-B-2 Attitude Data Messages standard](https://ccsds.org/Pubs/504x0b2.pdf).

## Parse and Access

Parse from file or string, then access header, metadata, and attitude data for each segment:

```python
import brahe as bh
from brahe.ccsds import AEM

bh.initialize_eop()

# Parse an AEM with two quaternion segments
aem = AEM.from_file("test_assets/ccsds/aem/AEMExampleG4.txt")

# Header
print(f"Format version: {aem.format_version}")
print(f"Originator:     {aem.originator}")
print(f"Creation date:  {aem.creation_date}")
print(f"Message ID:     {aem.message_id}")

print(f"\nSegments: {len(aem.segments)}")
for i, segment in enumerate(aem.segments):
    print(f"\n  Segment {i}:")
    print(f"    Object name:   {segment.object_name}")
    print(f"    Ref frame A:   {segment.ref_frame_a}")
    print(f"    Ref frame B:   {segment.ref_frame_b}")
    print(f"    Attitude type: {segment.attitude_type}")
    print(f"    Interpolation: {segment.interpolation_method}")
    print(f"    States:        {len(segment.states)}")

    first = segment.states[0]
    wire = first.quaternion.to_vector(scalar_first=False)
    print(
        f"    First quaternion [Q1, Q2, Q3, QC] @ {first.epoch}: "
        f"[{wire[0]:.5f}, {wire[1]:.5f}, {wire[2]:.5f}, {wire[3]:.5f}]"
    )
```


## Segments and Attitude Types

An AEM message has a **header** (version, creation date, originator) and one or more **segments**. Each segment carries its own metadata — object identity, center body, reference frames, time system, and the segment's total and useable time spans — followed by a data block of attitude states at strictly increasing epochs. A message is only valid to write if every segment has at least one state.

Every segment declares `REF_FRAME_A` and `REF_FRAME_B`, and every attitude value in the segment's data block is a rotation from frame A to frame B, exactly as in APM. A segment's `ATTITUDE_TYPE` fixes which of nine data layouts its data lines use; brahe rejects a data line whose column count does not match the declared type. Data lines carry no keyword names or bracketed units — only the epoch followed by the fixed-order numeric columns below (angles and rates on the wire are degrees and deg/s; brahe converts to radians and rad/s on parse):

| `ATTITUDE_TYPE` | Columns (after epoch) | Conditional metadata |
|---|---|---|
| `QUATERNION` | `Q1 Q2 Q3 QC` | — |
| `QUATERNION/DERIVATIVE` | `Q1 Q2 Q3 QC Q1_DOT Q2_DOT Q3_DOT QC_DOT` | — |
| `QUATERNION/ANGVEL` | `Q1 Q2 Q3 QC ANGVEL_X ANGVEL_Y ANGVEL_Z` | `ANGVEL_FRAME` |
| `EULER_ANGLE` | `ANGLE_1 ANGLE_2 ANGLE_3` | `EULER_ROT_SEQ` |
| `EULER_ANGLE/DERIVATIVE` | `ANGLE_1 ANGLE_2 ANGLE_3 ANGLE_1_DOT ANGLE_2_DOT ANGLE_3_DOT` | `EULER_ROT_SEQ` |
| `EULER_ANGLE/ANGVEL` | `ANGLE_1 ANGLE_2 ANGLE_3 ANGVEL_X ANGVEL_Y ANGVEL_Z` | `EULER_ROT_SEQ`, `ANGVEL_FRAME` |
| `SPIN` | `SPIN_ALPHA SPIN_DELTA SPIN_ANGLE SPIN_ANGLE_VEL` | — |
| `SPIN/NUTATION` | `SPIN_ALPHA SPIN_DELTA SPIN_ANGLE SPIN_ANGLE_VEL NUTATION NUTATION_PER NUTATION_PHASE` | — |
| `SPIN/NUTATION_MOM` | `SPIN_ALPHA SPIN_DELTA SPIN_ANGLE SPIN_ANGLE_VEL MOMENTUM_ALPHA MOMENTUM_DELTA NUTATION_VEL` | — |

`EULER_ROT_SEQ` is required exactly when `ATTITUDE_TYPE` is one of the `EULER_ANGLE*` types, and its rotation sequence (e.g. `ZXZ`) applies to every `ANGLE_1`/`ANGLE_2`/`ANGLE_3` column in the segment. `ANGVEL_FRAME` is required exactly when `ATTITUDE_TYPE` ends in `/ANGVEL`, and must equal the segment's `REF_FRAME_A` or `REF_FRAME_B`; brahe validates both rules when parsing and when writing. `INTERPOLATION_DEGREE` is required exactly when `INTERPOLATION_METHOD` is present.

## Converting to AttitudeTrajectory

`AEM::segment_to_attitude_trajectory` (Rust) or `aem.segment_to_attitude_trajectory` (Python) converts one segment into an [`AttitudeTrajectory`](../trajectories/attitude_trajectory.md), normalizing every attitude representation to a canonical quaternion (frame A to frame B) plus optional body-frame angular velocity. `AEM::to_attitude_trajectories` (Rust) or `aem.to_attitude_trajectories()` (Python) converts every segment at once.

```python
import brahe as bh
from brahe.ccsds import AEM

bh.initialize_eop()

# Parse an AEM with two quaternion segments
aem = AEM.from_file("test_assets/ccsds/aem/AEMExampleG4.txt")

# Segment 1 carries no INTERPOLATION_METHOD, so it converts cleanly to the
# default slerp trajectory. Segment 0 sets INTERPOLATION_METHOD = HERMITE,
# which has no AttitudeTrajectory equivalent and would raise an error.
traj = aem.segment_to_attitude_trajectory(1)
print(f"Trajectory: {len(traj)} states")
print(f"  Frame A:       {traj.frame_a}")
print(f"  Frame B:       {traj.frame_b}")
print(f"  Interpolation: {traj.interpolation_method}")
print(f"  Has rates:     {traj.has_rates}")
print(f"  Start:         {traj.start_epoch}")
print(f"  End:           {traj.end_epoch}")

# Slerp-query the attitude at the midpoint of the trajectory's span
t0 = traj.start_epoch
t1 = traj.end_epoch
mid = t0 + (t1 - t0) / 2.0
quaternion = traj.quaternion(mid)
wire = quaternion.to_vector(scalar_first=False)
print(
    f"\nInterpolated quaternion [Q1, Q2, Q3, QC] at {mid}: "
    f"[{wire[0]:.5f}, {wire[1]:.5f}, {wire[2]:.5f}, {wire[3]:.5f}]"
)
```


**Interpolation method.** A segment's `INTERPOLATION_METHOD` maps onto [`AttitudeInterpolationMethod`](../trajectories/attitude_trajectory.md):

| AEM `INTERPOLATION_METHOD` | `AttitudeInterpolationMethod` |
|---|---|
| Unset | `Slerp` |
| `LINEAR` | `Linear` |
| `LAGRANGE` | `Lagrange { degree }` (from `INTERPOLATION_DEGREE`) |
| `HERMITE` | Conversion errors — construct the trajectory and call `set_interpolation_method` with an explicit choice instead |

**SPIN limitation.** The `SPIN`, `SPIN/NUTATION`, and `SPIN/NUTATION_MOM` attitude types describe a spin-stabilized attitude by spin-axis geometry rather than a full 3-axis orientation, and have no `AttitudeTrajectory` representation. Converting a segment with one of these types returns an error naming the offending type; the AEM itself can still be read and written normally.

**ANGVEL frame handling.** For the `QUATERNION/ANGVEL` and `EULER_ANGLE/ANGVEL` types, the wire angular velocity is expressed in whichever frame `ANGVEL_FRAME` names. `AttitudeState::angular_velocity` is always in frame B (the canonical convention used throughout brahe), so when `ANGVEL_FRAME` equals `REF_FRAME_A`, brahe re-expresses the vector as $\omega_B = R(q) \, \omega_A$, where $R(q)$ is the rotation matrix of the state's attitude quaternion. When `ANGVEL_FRAME` already equals `REF_FRAME_B`, the value is used as-is. Building an AEM from a rate-carrying `AttitudeTrajectory` always writes `ANGVEL_FRAME = REF_FRAME_B`, so no re-expression is needed on that path.

## Creating and Writing

Build an AEM programmatically by defining metadata, adding attitude states to a segment, and serializing to KVN, XML, or JSON:

```python
import math

import brahe as bh
from brahe.ccsds import AEM, AEMAttitudeState, AEMSegment

bh.initialize_eop()

# One segment spanning 60 seconds, carrying the rotation from EME2000 into the
# spacecraft body frame at each epoch.
t0 = bh.Epoch.from_datetime(2024, 1, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)
t1 = t0 + 60.0

segment = AEMSegment(
    "SAT1", "2024-001A", "EME2000", "SC_BODY_1", "UTC", t0, t1, "QUATERNION"
)

# The body starts aligned with EME2000 and rotates 2 degrees about its Z axis
# over the segment. A quaternion stores the half-angle, so the sample at t1
# uses 1 degree.
half_angle = math.radians(1.0)
segment.add_state(
    AEMAttitudeState.from_quaternion(t0, bh.Quaternion(1.0, 0.0, 0.0, 0.0))
)
segment.add_state(
    AEMAttitudeState.from_quaternion(
        t1, bh.Quaternion(math.cos(half_angle), 0.0, 0.0, math.sin(half_angle))
    )
)

aem = AEM("BRAHE_EXAMPLE")
aem.message_id = "AEM-2024-001"
aem.add_segment(segment)

print(
    f"Created AEM with {len(aem.segments)} segment, "
    f"{len(aem.segments[0].states)} attitude states"
)

# Write to KVN string
kvn = aem.to_string("KVN")
print(f"\nKVN output ({len(kvn)} chars):")
print(kvn)

# Write to file
aem.to_file("/tmp/brahe_example_aem.txt", "KVN")
print("\nWritten to /tmp/brahe_example_aem.txt")

# Verify round-trip
aem2 = AEM.from_file("/tmp/brahe_example_aem.txt")
print(
    f"Round-trip: {len(aem2.segments)} segment, "
    f"{len(aem2.segments[0].states)} attitude states"
)
```


**Round-Trip Fidelity**
Writing and re-parsing an AEM preserves all header, metadata, and attitude-state values. Numeric precision may vary slightly due to floating-point formatting, but values are preserved within the precision of the output format.

## KVN Format Example

The CCSDS 504.0-B-2 Annex G-4 example file ships with brahe as `test_assets/ccsds/aem/AEMExampleG4.txt`, and is the file the [Parse and Access](#parse-and-access) example reads. It holds a header followed by two segments, each with its own metadata block and data block:

```
CCSDS_AEM_VERS = 2.0
CREATION_DATE = 2002-11-04T17:22:31
ORIGINATOR = NASA/JPL
MESSAGE_ID = A7015Z3

META_START
COMMENT This file was produced by M.R. Somebody, MSOO NAV/JPL.
COMMENT It is to be used for attitude reconstruction only. The relative accuracy of these
COMMENT  attitudes is 0.1 degrees per axis.
OBJECT_NAME     = MARS GLOBAL SURVEYOR
OBJECT_ID       = 1996-062A
CENTER_NAME     = MARS BARYCENTER
REF_FRAME_A     = EME2000
REF_FRAME_B     = SC_BODY_1
TIME_SYSTEM     = UTC
START_TIME      = 1996-11-28T21:29:07.2555
USEABLE_START_TIME = 1996-11-28T22:08:02.5555
USEABLE_STOP_TIME  = 1996-11-30T01:18:02.5555
STOP_TIME       = 1996-11-30T01:28:02.5555
ATTITUDE_TYPE   = QUATERNION
INTERPOLATION_METHOD = hermite
INTERPOLATION_DEGREE = 7
META_STOP

DATA_START
1996-11-28T21:29:07.2555 0.56748  0.03146  0.45689  0.68427
1996-11-28T22:08:03.5555 0.42319  -0.45697 0.23784  0.74533
1996-11-28T22:08:04.5555 -0.84532 0.26974  -0.06532 0.45652
1996-11-30T01:28:02.5555 0.74563  -0.45375  0.36875  0.31964
DATA_STOP

META_START
COMMENT  This block begins after trajectory correction maneuver TCM-3.
OBJECT_NAME     = mars global surveyor
OBJECT_ID       = 1996-062A
CENTER_NAME     = MARS BARYCENTER
REF_FRAME_A     = EME2000
REF_FRAME_B      = SC_BODY_1
TIME_SYSTEM     = UTC
START_TIME      = 1996-12-18T12:05:00.5555
USEABLE_START_TIME = 1996-12-18T12:10:00.5555
USEABLE_STOP_TIME  = 1996-12-28T21:23:00.5555
STOP_TIME       = 1996-12-28T21:28:00.5555
ATTITUDE_TYPE   = QUATERNION
META_STOP

DATA_START
1996-12-18T12:05:00.5555 -0.64585 0.018542  -0.23854 0.72501
1996-12-18T12:10:05.5555 0.87451  -0.43475  0.13458  0.16767
1996-12-18T12:10:10.5555 0.03125  -0.65874  0.23458  0.71418
1996-12-28T21:28:00.5555 -0.25485 0.58745  -0.36845  0.67394
DATA_STOP
```

The data lines carry no keyword names. `QUATERNION` fixes the column order to epoch, `Q1`, `Q2`, `Q3`, `QC`. The first segment's `INTERPOLATION_METHOD = hermite` is preserved on parse and write, but has no `AttitudeTrajectory` equivalent; see [Converting to AttitudeTrajectory](#converting-to-attitudetrajectory) above.

---

## See Also

- [API Reference — AEM](../../library_api/ccsds/aem.md)
- [CCSDS Data Formats](index.md) — Overview of all message types
- [OEM — Orbit Ephemeris Message](oem.md) — The orbit-ephemeris counterpart to AEM
- [APM — Attitude Parameter Message](apm.md) — Single-epoch attitude snapshot
- [AttitudeTrajectory](../trajectories/attitude_trajectory.md) — Native attitude trajectory storage and interpolation
- [Attitude Representations](../attitude_representations/index.md) — Quaternion, Euler angle, and rotation matrix conventions
- [CCSDS 504.0-B-2](https://ccsds.org/Pubs/504x0b2.pdf) — Attitude Data Messages, the standard AEM implements