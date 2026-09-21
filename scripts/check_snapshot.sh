#!/usr/bin/env bash
# Bounded local validation; no model calls or hosted orbital service requests.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"
export PATH="$PROJECT_ROOT/.venv/bin:$PATH"
export PYTHON="$PROJECT_ROOT/.venv/bin/python3"

# Fail clearly if the pinned source/data checkout has not been initialized.
test -f satnet/data/problems.json
test -f satnet/data/maintenance.csv

bash src/benchmark/build_sandbox.sh
bash src/satnet_agent/build_sandbox.sh

"$PYTHON" src/benchmark/run_benchmark.py --help >/dev/null
"$PYTHON" src/benchmark/run_baseline.py --help >/dev/null
"$PYTHON" src/satnet_agent/run_benchmark.py --help >/dev/null
"$PYTHON" src/satnet_agent/scorer.py --help >/dev/null

"$PYTHON" -m pytest -q \
  tests/test_satnet_state.py \
  tests/test_scenario_satnet.py \
  tests/test_mcp_server_satnet.py \
  tests/test_scorer_satnet.py \
  tests/test_strip_attitude.py \
  tests/test_chain_latency.py::TestTimeQuantization \
  tests/test_chain_latency.py::TestLatencyMath::test_direct_distance_latency \
  tests/test_chain_latency.py::TestLatencyMath::test_geo_satellite_latency \
  tests/test_strip_accessibility.py::TestPolylineInterpolation \
  tests/test_scenario.py::TestQueryMethods \
  tests/test_scenario.py::TestExceptionHierarchy \
  tests/test_mcp_server.py::test_mcp_server_name_and_basic_shape \
  tests/test_sandbox_setup.py
