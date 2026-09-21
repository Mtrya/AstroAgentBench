"""Harbor adapter for the standalone setup.sh / solve.sh solver contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class SolverAgent(BaseAgent):
    @staticmethod
    def name() -> str:
        return "standalone-solver"

    def version(self) -> str:
        return "1"

    def __init__(self, *, solver_dir: str, config_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.solver_dir = Path(solver_dir).resolve()
        self.config_dir = Path(config_dir).resolve()
        for name in ("setup.sh", "solve.sh"):
            if not (self.solver_dir / name).is_file():
                raise FileNotFoundError(self.solver_dir / name)
        if not self.config_dir.is_dir():
            raise NotADirectoryError(self.config_dir)

    async def setup(self, environment: BaseEnvironment) -> None:
        # Exclude local environments and generated outputs; callers supply only public configs.
        ignore = shutil.ignore_patterns(".git", ".venv", ".solver-env", "__pycache__", ".pytest_cache", "build", "target", "solution", "debug")
        with tempfile.TemporaryDirectory() as temporary:
            bundle = Path(temporary)
            shutil.copytree(self.solver_dir, bundle / "solver", ignore=ignore)
            shutil.copytree(self.config_dir, bundle / "config", ignore=ignore)
            files = {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.rglob("*")) if p.is_file()}
            self.provenance = {"solver": str(self.solver_dir), "config": str(self.config_dir), "files": files}
            (self.logs_dir / "solver-inputs.json").write_text(json.dumps(self.provenance, indent=2) + "\n")
            await environment.upload_dir(source_dir=bundle, target_dir="/opt/method")
        result = await environment.exec(command="bash /opt/method/solver/setup.sh", timeout_sec=600)
        (self.logs_dir / "setup.stdout").write_text(result.stdout or "")
        (self.logs_dir / "setup.stderr").write_text(result.stderr or "")
        if result.return_code != 0:
            raise RuntimeError(f"Solver setup exited with {result.return_code}")

    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        context.metadata = self.provenance
        result = await environment.exec(command="bash /opt/method/solver/solve.sh /workspace/case /opt/method/config /workspace/solution")
        (self.logs_dir / "solve.stdout").write_text(result.stdout or "")
        (self.logs_dir / "solve.stderr").write_text(result.stderr or "")
        if result.return_code != 0:
            raise RuntimeError(f"Solver exited with {result.return_code}")
