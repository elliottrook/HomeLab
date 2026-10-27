"""Validate the declarative clean-client replay order for AsterTV v2."""
from __future__ import annotations

from release_inventory import require


ACTIONS = {
    "install-base-archives", "install-family-base", "install-kodi-package",
    "apply-successor", "install-system-integration", "verify-release",
}


def validate(plan: dict, recipe: dict) -> dict:
    require(recipe.get("schema") == 1
            and recipe.get("kind") == "aster-recovery-recipe.v1",
            "recipe-contract")
    declared = {row["path"] for row in plan.get("sources", [])}
    require(declared, "recipe-plan-sources")
    prerequisites = recipe.get("prerequisites")
    require(isinstance(prerequisites, list) and prerequisites,
            "recipe-prerequisites")
    identities = set()
    for row in prerequisites:
        require(isinstance(row, dict), "recipe-prerequisite")
        identity = row.get("id")
        require(isinstance(identity, str) and identity and identity not in identities,
                "recipe-prerequisite-id")
        require(row.get("kind") in ("platform", "kodi-addon", "private-service",
                                    "restricted-provisioning"),
                "recipe-prerequisite-kind")
        require(isinstance(row.get("requirement"), str)
                and 1 <= len(row["requirement"]) <= 240,
                "recipe-prerequisite-requirement")
        identities.add(identity)

    steps = recipe.get("steps")
    require(isinstance(steps, list) and steps, "recipe-steps")
    used = set(); names = set()
    restart_points = []
    for number, step in enumerate(steps, 1):
        require(isinstance(step, dict) and step.get("order") == number,
                "recipe-step-order")
        name = step.get("id")
        require(isinstance(name, str) and name and name not in names,
                "recipe-step-id")
        require(step.get("action") in ACTIONS, "recipe-step-action")
        sources = step.get("sources", [])
        require(isinstance(sources, list), "recipe-step-sources")
        for source in sources:
            require(source in declared and source not in used,
                    "recipe-step-source")
            used.add(source)
        restart = step.get("kodi_restart", False)
        require(type(restart) is bool, "recipe-step-restart")
        if restart:
            restart_points.append(number)
        names.add(name)
    require(used == declared, "recipe-source-coverage")
    require(steps[-1].get("action") == "verify-release"
            and not steps[-1].get("sources"), "recipe-final-verify")
    require(len(restart_points) <= 3, "recipe-restart-bound")
    return {"valid": True, "steps": len(steps), "sources": len(used),
            "prerequisites": len(prerequisites),
            "kodi_restarts": restart_points}
