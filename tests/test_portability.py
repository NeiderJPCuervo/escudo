"""Los paquetes de dominio y simulador solo pueden importar la biblioteca estándar (y entre ellos):
es lo que permite ejecutarlos en el navegador con Pyodide (ADR 0001)."""

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FIRST_PARTY = {
    "escudo-domain": {"escudo_domain"},
    "escudo-sim": {"escudo_domain", "escudo_sim"},
}


def imported_modules(path: Path) -> set[str]:
    mods: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            mods |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    return mods


@pytest.mark.parametrize("package", sorted(ALLOWED_FIRST_PARTY))
def test_package_only_imports_stdlib(package: str) -> None:
    src = ROOT / "packages" / package / "src"
    files = list(src.rglob("*.py"))
    assert files, f"no hay módulos en {src}"
    for f in files:
        foreign = imported_modules(f) - set(sys.stdlib_module_names) - ALLOWED_FIRST_PARTY[package]
        assert not foreign, f"{f.relative_to(ROOT)} importa dependencias externas: {sorted(foreign)}"


def test_domain_does_not_depend_on_simulator() -> None:
    for f in (ROOT / "packages" / "escudo-domain" / "src").rglob("*.py"):
        assert "escudo_sim" not in imported_modules(f), f"{f.name}: el dominio no puede conocer al simulador"
