"""Prove that every inventoried AsterTV layer has a recovery disposition.

This does not restore anything.  It prevents a release assembler from silently
forgetting a later successor while composing a recovery package.
"""
from __future__ import annotations

from release_inventory import InventoryError, require


DISPOSITIONS = {"source", "evidence-only", "identity-only"}


def assess(inventory: dict, plan: dict) -> dict:
    require(inventory.get("kind") == "aster-release-inventory.v1"
            and inventory.get("complete") is True, "recovery-inventory")
    require(plan.get("schema") == 1
            and plan.get("kind") == "aster-recovery-plan.v1",
            "recovery-plan")
    components = {row.get("name") for row in inventory.get("components", [])
                  if row.get("status") == "verified"}
    require(None not in components and components, "recovery-components")
    rows = plan.get("coverage")
    require(isinstance(rows, list) and len(rows) <= 128, "recovery-coverage")
    seen: set[str] = set()
    result = []
    for row in rows:
        require(isinstance(row, dict), "recovery-row")
        name = row.get("component")
        disposition = row.get("disposition")
        require(name in components and name not in seen,
                "recovery-component-identity")
        require(disposition in DISPOSITIONS, "recovery-disposition")
        source = row.get("source")
        if disposition == "source":
            require(isinstance(source, str) and source.startswith("/storage/.aster-staging/")
                    and ".." not in source.split("/"), "recovery-source")
        else:
            require(source is None, "recovery-source-unexpected")
        seen.add(name)
        result.append({"component": name, "disposition": disposition,
                       **({"source": source} if source else {})})
    missing = sorted(components - seen)
    identity_only = sorted(row["component"] for row in result
                           if row["disposition"] == "identity-only")
    return {
        "schema": 1,
        "kind": "aster-recovery-coverage.v1",
        "ready": not missing and not identity_only,
        "verified_components": len(components),
        "covered_components": len(seen),
        "missing": missing,
        "identity_only": identity_only,
        "coverage": result,
    }
