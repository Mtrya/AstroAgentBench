# AttitudeTrajectory

`AttitudeTrajectory` is a chronologically sorted collection of attitude samples relating two [`ReferenceFrame`](../frames/index.md) endpoints. Each sample is an `AttitudeState`: a unit quaternion, plus an optional body angular velocity. Use `AttitudeTrajectory` when you have or want to produce a time-ordered attitude history — converting from an AEM, storing a propagated or ground-solved attitude solution, or interpolating attitude for pointing analysis.

`AttitudeTrajectory` implements the [`Trajectory`](trajectory.md) trait, so the standard trajectory operations — `add`, `get`, `len`, `start_epoch`/`end_epoch`, eviction policies — all apply. It does not implement `InterpolatableTrajectory`: that trait's default interpolation methods require the state type to support scalar multiplication and addition, and unit quaternions are not closed under either operation. Interpolation is instead an inherent method (`interpolate`) and the [`OrientationProvider`](#orientationprovider) trait, both quaternion-aware.

## Canonical State and Rate Uniformity

Every quaternion stored in an `AttitudeTrajectory` represents the attitude of `frame_b` relative to `frame_a` — the same A$\to$B convention used throughout brahe's CCSDS attitude support. When a state carries an angular velocity, it is the angular velocity of frame B relative to frame A, expressed in frame B, in rad/s.

A trajectory's states must uniformly carry angular velocity or uniformly omit it. `add` rejects a state whose rate presence does not match the trajectory's existing states, so a trajectory is never a mix of rate-carrying and rate-free samples. `has_rates()` reports which case a non-empty trajectory is in.

```python
import numpy as np

import brahe as bh

bh.initialize_eop()

# A trajectory relates two frame endpoints: every stored quaternion rotates
# from frame_a into frame_b.
traj = bh.AttitudeTrajectory(
    bh.ReferenceFrame.celestial(bh.CelestialFrame.GCRF),
    bh.ReferenceFrame.body(None, bh.BodyFrame.SC_BODY("1")),
)

epoch = bh.Epoch.from_datetime(2024, 1, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)
traj.add(epoch, bh.Quaternion(1.0, 0.0, 0.0, 0.0))

print(f"frame_a:   {traj.frame_a}")
print(f"frame_b:   {traj.frame_b}")
print(f"States:    {len(traj)}")
print(f"has_rates: {traj.has_rates}")

# The first state carries no angular velocity, so every later state must omit
# it as well. Adding a rate-carrying state to a rate-free trajectory is
# rejected rather than producing a mixed trajectory.
try:
    traj.add(
        epoch + 60.0,
        bh.Quaternion(1.0, 0.0, 0.0, 0.0),
        np.array([0.0, 0.0, 0.01]),
    )
except bh.BraheError as exc:
    print(f"\nMixed rate rejected: {exc}")
```


## Interpolation

`interpolate` (Rust) or the [`OrientationProvider`](#orientationprovider) accessors (Rust and Python) retrieve the attitude at an arbitrary epoch within the trajectory's span, using the configured `AttitudeInterpolationMethod`:

- **`Slerp`** (default): [spherical linear interpolation](https://en.wikipedia.org/wiki/Spherical_linear_interpolation) of the bracketing quaternions. Exact for constant-angular-rate motion, and always produces a unit quaternion. This is the same interpolation family used for attitude in most spacecraft dynamics software, and is brahe's chosen default for an AEM segment whose `INTERPOLATION_METHOD` is not set, since the standard itself does not mandate a method in that case.
- **`Linear`**: componentwise linear interpolation of the bracketing quaternions (scalar-first), renormalized afterward. Because the two bracketing quaternions can represent the same rotation with either sign — a unit quaternion and its negation are the same attitude — brahe aligns their hemisphere (negating the later quaternion's components if its dot product with the earlier one is negative) before interpolating, so the short way around is always taken and the result varies continuously across that sign boundary.
- **`Lagrange { degree }`**: Lagrange polynomial interpolation over a window of `degree + 1` samples centered on the query epoch, hemisphere-aligned sequentially and renormalized afterward.

Body angular velocity, when present, always interpolates linearly regardless of the quaternion interpolation method (except under `Lagrange`, where it uses the same polynomial degree). An epoch matching a stored node exactly returns that node's state directly; otherwise the query epoch must lie within `[start_epoch, end_epoch]`, and interpolation errors outside that range.

The following example builds a trajectory from a constant-rate rotation and compares `Slerp` against `Linear` at a query epoch away from the interpolation midpoint, where the two methods diverge:

```python
import math

import brahe as bh

bh.initialize_eop()

# Two attitude samples 60 seconds apart: a constant-rate rotation of 2 deg/s
# about the spacecraft Z axis, from 0 to 120 degrees.
traj = bh.AttitudeTrajectory(
    bh.ReferenceFrame.celestial(bh.CelestialFrame.GCRF),
    bh.ReferenceFrame.body(None, bh.BodyFrame.SC_BODY(None)),
)

t0 = bh.Epoch.from_datetime(2024, 1, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)
t1 = t0 + 60.0
q0 = bh.Quaternion(1.0, 0.0, 0.0, 0.0)
half_angle = math.radians(60.0)
q1 = bh.Quaternion(math.cos(half_angle), 0.0, 0.0, math.sin(half_angle))
traj.add(t0, q0)
traj.add(t1, q1)

# Query one third of the way between the two nodes. At the exact midpoint,
# linear interpolation of a single-axis rotation happens to coincide with
# slerp, so an off-center query is needed to see them diverge.
query = t0 + 20.0

traj.set_interpolation_method("SLERP")
slerp_q = traj.quaternion(query)

traj.set_interpolation_method("LINEAR")
linear_q = traj.quaternion(query)

slerp_angle_deg = math.degrees(slerp_q.to_euler_axis().angle)
linear_angle_deg = math.degrees(linear_q.to_euler_axis().angle)

print(f"Query epoch: {query} (1/3 of the way from t0 to t1)")
print(f"Slerp  rotation angle:  {slerp_angle_deg:.4f} deg (exact)")
print(f"Linear rotation angle:  {linear_angle_deg:.4f} deg (approximate)")
```


## OrientationProvider

`OrientationProvider` is the common interface every rotation source in the frame graph implements — a constant attitude, a user callback, or an `AttitudeTrajectory`. Implementing it is what lets an attitude history be registered as a frame-graph link. It provides:

- `quaternion(epoch)` — attitude quaternion, frame A to frame B
- `angular_velocity(epoch)` — body angular velocity in rad/s, or `None` when the trajectory carries no rate data. brahe never silently finite-differences a quaternion history to fabricate a rate; `with_numerical_rates` derives one by explicit opt-in
- `coverage()` — the trajectory's `(start, end)` epoch bounds
- `euler_angle(epoch, order)` — Euler angles in the requested sequence
- `euler_axis(epoch)` — axis-angle representation
- `rotation_matrix(epoch)` — direction cosine matrix

`AttitudeTrajectory` additionally provides `quaternions(epochs)` and `angular_velocities(epochs)` as batched forms.

The following example builds a rate-carrying trajectory and queries every accessor at an epoch between two stored nodes:

```python
import math

import numpy as np

import brahe as bh

bh.initialize_eop()

# Two samples 60 seconds apart, rotating about the spacecraft Z axis at
# 0.01 rad/s. The rate is carried on both states, so angular_velocity is
# available alongside the attitude.
traj = bh.AttitudeTrajectory(
    bh.ReferenceFrame.celestial(bh.CelestialFrame.GCRF),
    bh.ReferenceFrame.body(None, bh.BodyFrame.SC_BODY("1")),
)

omega = np.array([0.0, 0.0, 0.01])
t0 = bh.Epoch.from_datetime(2024, 1, 1, 0, 0, 0.0, 0.0, bh.TimeSystem.UTC)
t1 = t0 + 60.0
half_angle = 0.5 * omega[2] * 60.0
traj.add(t0, bh.Quaternion(1.0, 0.0, 0.0, 0.0), omega)
traj.add(t1, bh.Quaternion(math.cos(half_angle), 0.0, 0.0, math.sin(half_angle)), omega)

# Every accessor evaluates the same interpolated attitude and returns it in a
# different representation.
epoch = t0 + 30.0
quaternion = traj.quaternion(epoch)
angles = traj.euler_angle(epoch, bh.EulerAngleOrder.ZYX)
axis = traj.euler_axis(epoch)
matrix = traj.rotation_matrix(epoch).to_matrix()
rate = traj.angular_velocity(epoch)

q = quaternion.to_vector(scalar_first=True)
print(f"Coverage:    {traj.start_epoch} to {traj.end_epoch}")
print(f"Query epoch: {epoch}")
print(f"Quaternion:  s {q[0]:.6f}, v {q[1]:.6f} {q[2]:.6f} {q[3]:.6f}")
print(
    "Euler ZYX:   "
    f"{math.degrees(angles.phi):.4f}, "
    f"{math.degrees(angles.theta):.4f}, "
    f"{math.degrees(angles.psi):.4f} deg"
)
print(
    "Euler axis:  "
    f"{axis.axis[0]:.4f} {axis.axis[1]:.4f} {axis.axis[2]:.4f}, "
    f"angle {math.degrees(axis.angle):.4f} deg"
)
print("Rotation matrix:")
for row in matrix:
    print(f"  {row[0]:9.6f} {row[1]:9.6f} {row[2]:9.6f}")
print(f"Rate:        {rate[0]:.4f} {rate[1]:.4f} {rate[2]:.4f} rad/s")
```


## frame_a / frame_b Semantics

`frame_a` and `frame_b` are [`ReferenceFrame`](../frames/index.md) values — each one either a celestial frame, an orbit-relative frame, or a body frame. AEM endpoints parse as unbound frames: the message names the frame but not the object it belongs to. Every stored quaternion rotates from `frame_a` to `frame_b`.

---

## See Also

- [Trajectories Overview](index.md) — Trait hierarchy and implementation guide
- [Trajectory](trajectory.md) — Dynamic-dimension trajectory
- [AEM — Attitude Ephemeris Message](../ccsds/aem.md) — Parsing AEM data into an `AttitudeTrajectory`
- [Attitude Representations](../attitude_representations/index.md) — `Quaternion` and related types
- [AttitudeTrajectory API Reference](../../library_api/trajectories/attitude_trajectory.md)