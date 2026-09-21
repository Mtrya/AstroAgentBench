#!/bin/bash
# Build the sandbox_template with required packages and code.
#
# Usage: ./build_sandbox.sh
#
# Run this script whenever you update engine/planner source code to sync
# changes to the sandbox workspace.
#
# This prepares the sandbox environment:
# - Installs MCP dependencies to lib/ (for MCP server)
# - Copies engine/ and planner/ source to workspace/ (for agent to use)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LIB_DIR="$SCRIPT_DIR/sandbox_template/lib"
WORKSPACE_DIR="$SCRIPT_DIR/sandbox_template/workspace"

# Use the same interpreter as the locked project environment.
PYTHON=${PYTHON:-"$PROJECT_ROOT/.venv/bin/python3"}

echo "Building sandbox environment..."
echo "Using Python: $PYTHON ($($PYTHON --version))"
echo "Project root: $PROJECT_ROOT"

# Clean lib directory
echo ""
echo "Installing MCP dependencies to lib/..."
rm -rf "$LIB_DIR"
mkdir -p "$LIB_DIR"

# Install the locked project runtime (without optional SatNet training groups)
REQUIREMENTS=$(mktemp)
trap 'rm -f "$REQUIREMENTS"' EXIT
uv export --project "$PROJECT_ROOT" --locked --no-default-groups --no-emit-project --format requirements.txt --output-file "$REQUIREMENTS" --quiet
uv pip sync --python "$PYTHON" --target="$LIB_DIR" --require-hashes --quiet "$REQUIREMENTS"

# Clean and copy engine to workspace
echo "Copying engine/ source to workspace/..."
rm -rf "$WORKSPACE_DIR/engine"
cp -r "$PROJECT_ROOT/src/engine" "$WORKSPACE_DIR/engine"

# Clean and copy planner to workspace
echo "Copying planner/ source to workspace/..."
rm -rf "$WORKSPACE_DIR/planner"
cp -r "$PROJECT_ROOT/src/planner" "$WORKSPACE_DIR/planner"

# Verify
echo ""
echo "MCP library installed to lib/:"
ls -1 "$LIB_DIR" | head -10

echo ""
echo "Source code in workspace/:"
echo "  engine/:"
ls -1 "$WORKSPACE_DIR/engine" | head -5
echo "  planner/:"
ls -1 "$WORKSPACE_DIR/planner" | head -5

echo ""
echo "Testing imports..."
cd "$WORKSPACE_DIR"
"$PYTHON" -c "from engine.models import Satellite, Target; print('✓ engine import OK')"
"$PYTHON" -c "from planner.scenario import Scenario; print('✓ planner import OK')"
PYTHONPATH="../lib" "$PYTHON" -c "from mcp.server.fastmcp import FastMCP; print('✓ MCP import OK (with PYTHONPATH)')"

echo ""
echo "Sandbox built successfully!"
echo ""
echo "Run from the repository root with the project environment activated:"
echo "  python src/benchmark/run_benchmark.py --help"
