# Modified ITC Ephemeris Format

The Modified ITC format is the Space-Track ephemeris exchange format defined in the
[Spaceflight Safety Handbook for Satellite Operators](https://www.space-track.org/documents/SFS_Handbook_For_Operators_V1.7.pdf)
(version 1.7). A file holds a short header followed by one
record per epoch: a line giving the `YYYYDDDHHMMSS.sss` UTC epoch, position (km) and velocity
(km/s), optionally followed by the lower triangle of a 6x6 position and velocity covariance (21
values, km-based units) in the frame the header names. Brahe reads and writes the format through
`ITC`, converting positions and velocities to SI units (m, m/s) and covariance elements by $10^6$ on
input, so every quantity on an `ITC` object is already in SI.

## Reading a File

```python
import numpy as np

import brahe as bh

PATH = "test_assets/starlink/MEME_100001_STARLINK-38128_2540142_Operational_1473385380_UNCLASSIFIED.txt"

itc = bh.ITC.from_file(PATH)
header = itc.header

print(f"Source file:      {itc.source_name}")
print(f"Created:          {header.created}")
print(f"Ephemeris start:  {header.ephemeris_start}")
print(f"Ephemeris stop:   {header.ephemeris_stop}")
print(f"Step size:        {header.step_size} s")
print(f"State frame:      {header.state_frame}")
print(f"Covariance frame: {header.covariance_frame}")
print(f"Records:          {len(itc)}")
print(f"Has covariance:   {itc.has_covariance}")

first = itc.states[0]
print(f"First epoch:      {first.epoch}")
print(f"Position [m]:     {np.array2string(first.position, precision=3)}")
print(f"Velocity [m/s]:   {np.array2string(first.velocity, precision=6)}")

sigma = np.sqrt(np.diag(itc.covariances[0]))
print(f"1-sigma RTN position [m]:   {np.array2string(sigma[:3], precision=3)}")
print(f"1-sigma RTN velocity [m/s]: {np.array2string(sigma[3:], precision=6)}")
```


`ITC.from_file` infers the state frame and the object's identity from a Space-Track compliant file
name: the DataType field `MEME`, `EME2000` or `J2000` all map to EME2000, and `TEME` and `ITRF` map
to those frames; the decoded name is kept on `source_name`. `ITC.from_str` parses only the file text
and leaves the state frame at its default, EME2000, since there is no file name to read a DataType
from. The header carries the creation time, the declared ephemeris start, stop and step, a free-text
source label, and the covariance frame; the state frame comes from the file name rather than the
body. `states` holds the parsed records and
`covariances` holds one matrix per record when the file carries covariance; `has_covariance` is
`true` only when every record does, since a Modified ITC message's covariance is all-or-none.

## Frames and Covariance

The state frame is the file's `MEME J2000.0`, the mean equator and mean equinox of J2000.0, which
brahe treats as `CelestialFrame.EME2000`; it is related to GCRF by the constant frame bias. The
covariance frame `UVW` is RTN (radial, in-track, cross-track), with

$$
\hat{R} = \frac{\mathbf{r}}{|\mathbf{r}|}, \quad
\hat{N} = \frac{\mathbf{r} \times \mathbf{v}}{|\mathbf{r} \times \mathbf{v}|}, \quad
\hat{T} = \hat{N} \times \hat{R}.
$$

When a message's covariance frame is `UVW` (RTN), converting it to a trajectory rotates each
record's covariance from RTN into the state frame with the block-diagonal Jacobian
$\mathrm{blockdiag}(R, R)$ by default, following the
[NASA Conjunction Assessment Risk Analysis handbook](https://ntrs.nasa.gov/citations/20205011318)
(Appendix N, eq. N-13) and the CARA
[`RIC2ECI`](https://github.com/nasa/CARA_Analysis_Tools) implementation. The rotating-frame form

$$
\begin{bmatrix} R & 0 \\ R[\boldsymbol{\omega}\times] & R \end{bmatrix}
$$

([Vallado, AAS 03-526](https://celestrak.org/publications/AAS/03-526/AAS-03-526.pdf)) is available by
passing `OrbitRelativeFrameVariant.ROTATING` to `to_trajectory_with_covariance_variant`. A covariance
frame of `EME2000` or `ITRF` skips RTN entirely: it is rotated directly between that frame and the
state frame with the state-transform Jacobian, so a message can carry covariance in either frame
regardless of which one is the state frame. `from_trajectory` and
`from_trajectory_with_covariance_variant` invert the same rotations to build a message from a
trajectory; both reject a trajectory that is not six-dimensional Cartesian, so a Keplerian-element
trajectory must be converted first.

## Converting to a Trajectory

```python
import numpy as np

import brahe as bh

bh.initialize_eop()

PATH = "test_assets/starlink/MEME_100001_STARLINK-38128_2540142_Operational_1473385380_UNCLASSIFIED.txt"

itc = bh.ITC.from_file(PATH)
trajectory = itc.to_trajectory()
start = trajectory.start_epoch()
end = trajectory.end_epoch()
print(f"Trajectory: {len(trajectory)} samples from {start} to {end}")

mid = start + 30.0
state = trajectory.interpolate(mid)
print(f"State at {mid} [m, m/s]: {np.array2string(state, precision=3)}")
covariance = trajectory.covariance(mid)
print(
    f"Position 1-sigma at {mid} [m]: {np.array2string(np.sqrt(np.diag(covariance))[:3], precision=3)}"
)

itrf = trajectory.to_itrf()
ecef = itrf.interpolate(mid)
print(f"ITRF position at {mid} [m]: {np.array2string(ecef[:3], precision=3)}")

station = bh.PointLocation(-122.4194, 37.7749, 0.0).with_name("San Francisco")
constraint = bh.ElevationConstraint(min_elevation_deg=10.0)
windows = bh.location_accesses(station, trajectory, start, end, constraint)
print(f"Access windows above 10 deg: {len(windows)}")
for window in windows[:3]:
    print(f"  {window.window_open} to {window.window_close} ({window.duration:.1f} s)")
```


The resulting `OrbitTrajectory` interpolates position, velocity and covariance at any epoch within
its span, and `to_frame` -- including the frame-specific shortcuts such as `to_eci` and `to_itrf` --
carries a Cartesian covariance along with the states by rotating it with the state-transform Jacobian,
so a conversion to any frame keeps it. Because it is an ordinary `OrbitTrajectory`, it can be used directly with
`location_accesses` to compute ground-station access windows, as in the example above, without a
separate conversion step.

## Writing a File and Naming It

```python
import tempfile
from pathlib import Path

import brahe as bh

bh.initialize_eop()

PATH = "test_assets/starlink/MEME_100002_STARLINK-37711_2540149_Operational_1473385800_UNCLASSIFIED.txt"

trajectory = bh.ITC.from_file(PATH).to_trajectory()

header = bh.ITCHeader(
    created=bh.Epoch(2026, 9, 11, 2, 0, 0.0, 0.0, time_system=bh.TimeSystem.UTC),
    ephemeris_source="brahe example",
)
itc = bh.ITC.from_trajectory(trajectory, header)
print(f"Records: {len(itc)}, covariance: {itc.has_covariance}")
print(f"Span: {itc.start_epoch} to {itc.end_epoch}")

name = itc.file_name(
    100002, "STARLINK-37711", bh.SpaceTrackEphemerisFileCategory.OPERATIONAL, "nomnvr"
)
print(f"File name: {name}")

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / str(name)
    itc.to_file(str(path))
    reread = bh.ITC.from_file(str(path))
    print(f"Re-read {len(reread)} records; state frame {reread.header.state_frame}")
    print(f"First line: {path.read_text().splitlines()[0]}")
```


`from_trajectory` requires a Cartesian, six-dimensional trajectory; it fills the header's ephemeris
start, stop and step from the trajectory's samples and keeps the header's state frame, covariance
frame, `created` and `ephemeris_source` fields. `ITC.file_name` then builds a Space-Track compliant
name from the message: `<DataType>_<NORAD>_<Name>_<DDDHHMM>_<Category>_<Metadata>_<Classification>.<ext>`,
where the DataType comes from the state frame, the day-time group from the ephemeris start, and the
catalog number, name, category and metadata from the arguments passed to `file_name`, and the
classification and extension from the defaults of `SpaceTrackEphemerisFileName`. That type is the one behind
the convention: `parse` reads a compliant name, constructing a `SpaceTrackEphemerisFileName` gives the `MEME`
data type, `UNCLASSIFIED` classification and `txt` extension, and the `with_*` methods replace
individual fields. Every field is rejected if it contains a path separator (`/` or `\`) or is `.` or `..`, so a
name built from untrusted input can never address a file outside its directory; the data type,
metadata, classification and extension fields are additionally rejected if they contain an underscore, since
that is the field delimiter -- the object name is the exception, since `parse` recovers it by
anchoring the other six fixed-position fields from either end and taking whatever remains between
them.

---

## See Also

- [Starlink Public Ephemerides](starlink.md) -- The public mirror that publishes files in this format
- [File Operations](spacetrack/file_operations.md) -- Space-Track's own SP Ephemeris downloads, in the same format
- [Modified ITC API Reference](../../library_api/ephemeris/itc.md) -- Class and function documentation
- [Space-Track Response Types](../../library_api/ephemeris/spacetrack/responses.md) -- `SpaceTrackEphemerisFileName` and `SpaceTrackEphemerisFileCategory`