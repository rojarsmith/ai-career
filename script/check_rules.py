#!/usr/bin/env python3
"""Structural check for the common rules file (rules/common.toml).

Checks what code can decide on its own: required fields and types, ID formats,
duplicate IDs, undefined, unused or circular terms, level and statement wording,
yields_to references and cycles, scope mode names, declared paths, and vague words.

Whether rules contradict each other, or mean two things, is a judgement about
meaning. /ai-career rules-check runs this script first and then reviews that.

Exit codes: 0 = no errors (warnings allowed), 1 = errors found, 2 = could not run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_REL = Path("rules") / "common.toml"
SKILL_REL = Path(".claude") / "skills" / "ai-career" / "SKILL.md"

RULE_ID = re.compile(r"^[A-Z]+-[1-9][0-9]*$")
TERM_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
TERM_REF = re.compile(r"\{([^{}\s]+)\}")
MODE_ROW = re.compile(r"^\|\s*([a-z][a-z-]*)\s*\|", re.MULTILINE)

LEVELS = {"must", "must-not"}
ENFORCERS = {"prompt", "script", "git"}
RULE_REQUIRED = {
    "id": str, "title": str, "level": str, "statement": str, "scope": (str, list),
    "overridable": bool, "enforced_by": list, "rationale": str, "source": str,
}
RULE_OPTIONAL = {"yields_to": list, "paths": list}
TERM_REQUIRED = {"id": str, "definition": str}
NEGATIVE_OPENERS = ("Do not ", "Never ")

# Words that usually leave the reader to guess. Reported as warnings, because some
# uses are precise in context.
VAGUE = [
    "should", "may", "might", "could", "appropriate", "appropriately", "reasonable",
    "reasonably", "as needed", "if needed", "if possible", "when necessary",
    "where necessary", "if necessary", "usually", "generally", "typically", "normally",
    "often", "sometimes", "etc", "and so on", "properly", "relevant", "important",
    "try to", "as soon as possible", "large", "small", "significant", "some", "various",
    "similar", "and/or",
]
VAGUE_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in VAGUE) + r")\b", re.IGNORECASE)


class Report:
    def __init__(self) -> None:
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def error(self, where: str, code: str, message: str) -> None:
        self.errors.append({"where": where, "code": code, "message": message})

    def warn(self, where: str, code: str, message: str) -> None:
        self.warnings.append({"where": where, "code": code, "message": message})


def load(path: Path) -> dict:
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except FileNotFoundError:
        fail(f"rules file not found: {path}")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        fail(f"{path} is not valid TOML: {exc}")


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def check_fields(item: dict, where: str, required: dict, optional: dict, rep: Report) -> None:
    for name, typ in required.items():
        if name not in item:
            rep.error(where, "missing-field", f"required field '{name}' is missing")
        elif not isinstance(item[name], typ):
            rep.error(where, "field-type", f"field '{name}' has the wrong type")
        elif isinstance(item[name], str) and not item[name].strip():
            rep.error(where, "empty-field", f"field '{name}' is empty")
    for name, typ in optional.items():
        if name in item and not isinstance(item[name], typ):
            rep.error(where, "field-type", f"field '{name}' has the wrong type")
    for name in item:
        if name not in required and name not in optional:
            rep.warn(where, "unknown-field", f"unknown field '{name}' (typo?)")


def find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    WHITE, GREY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        color[node] = GREY
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in color:
                continue
            if color[nxt] == GREY:
                return stack[stack.index(nxt):] + [nxt]
            if color[nxt] == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            found = visit(node)
            if found:
                return found
    return None


def known_modes(root: Path) -> set[str] | None:
    skill = root / SKILL_REL
    if not skill.is_file():
        return None
    text = skill.read_text(encoding="utf-8-sig")
    return {m for m in MODE_ROW.findall(text) if m != "mode"}


def check(data: dict, root: Path) -> tuple[Report, int, int]:
    rep = Report()

    if data.get("schema_version") != 1:
        rep.error("schema_version", "schema-version", "schema_version must be 1")

    terms = data.get("terms", [])
    rules = data.get("rules", [])
    if not isinstance(terms, list) or not isinstance(rules, list):
        rep.error("file", "structure", "terms and rules must be arrays of tables ([[terms]], [[rules]])")
        return rep, 0, 0
    if not rules:
        rep.error("file", "no-rules", "the file defines no rules")

    # ----- terms
    term_ids: dict[str, dict] = {}
    for i, term in enumerate(terms):
        tid = term.get("id") if isinstance(term, dict) else None
        where = f"terms[{i}]" + (f" ({tid})" if tid else "")
        if not isinstance(term, dict):
            rep.error(where, "structure", "each term must be a table")
            continue
        check_fields(term, where, TERM_REQUIRED, {}, rep)
        if isinstance(tid, str):
            if not TERM_ID.match(tid):
                rep.error(where, "term-id", f"term id '{tid}' must be lowercase-kebab-case")
            if tid in term_ids:
                rep.error(where, "duplicate-term", f"term '{tid}' is defined more than once")
            term_ids[tid] = term

    # ----- rules
    rule_ids: dict[str, dict] = {}
    for i, rule in enumerate(rules):
        rid = rule.get("id") if isinstance(rule, dict) else None
        where = rid if isinstance(rid, str) else f"rules[{i}]"
        if not isinstance(rule, dict):
            rep.error(where, "structure", "each rule must be a table")
            continue
        check_fields(rule, where, RULE_REQUIRED, RULE_OPTIONAL, rep)
        if isinstance(rid, str):
            if not RULE_ID.match(rid):
                rep.error(where, "rule-id", f"rule id '{rid}' must look like ABC-1")
            if rid in rule_ids:
                rep.error(where, "duplicate-rule", f"rule id '{rid}' is used more than once")
            rule_ids[rid] = rule

    # ----- term references: every {ref} must be defined; definitions must not loop
    used_terms: set[str] = set()
    term_graph: dict[str, list[str]] = {}

    def refs_in(text: str, where: str, field: str) -> list[str]:
        found = []
        for ref in TERM_REF.findall(text):
            if ref not in term_ids:
                rep.error(where, "undefined-term", f"{field} uses {{{ref}}}, which is not defined in [[terms]]")
            else:
                found.append(ref)
        return found

    for tid, term in term_ids.items():
        definition = term.get("definition")
        if isinstance(definition, str):
            refs = refs_in(definition, tid, "definition")
            term_graph[tid] = refs
            used_terms.update(refs)
            if tid in refs:
                rep.error(tid, "circular-term", f"term '{tid}' is defined using itself")
            for match in sorted({m.lower() for m in VAGUE_RE.findall(definition)}):
                rep.warn(tid, "vague-word", f"definition uses '{match}'; say exactly when and what")
    cycle = find_cycle(term_graph)
    if cycle and len(cycle) > 2:
        rep.error("terms", "circular-term", "term definitions form a loop: " + " -> ".join(cycle))

    for rid, rule in rule_ids.items():
        for field in ("title", "statement"):
            if isinstance(rule.get(field), str):
                used_terms.update(refs_in(rule[field], rid, field))

    for tid in term_ids:
        if tid not in used_terms:
            rep.warn(tid, "unused-term", f"term '{tid}' is defined but never used")

    # ----- per-rule semantics that code can check
    modes = known_modes(root)
    statements: dict[str, str] = {}
    titles: dict[str, str] = {}
    yields_graph: dict[str, list[str]] = {}

    for rid, rule in rule_ids.items():
        level = rule.get("level")
        statement = rule.get("statement") if isinstance(rule.get("statement"), str) else ""

        if isinstance(level, str) and level not in LEVELS:
            rep.error(rid, "level", f"level '{level}' must be one of: must, must-not")
        if level == "must-not" and statement and not statement.startswith(NEGATIVE_OPENERS):
            rep.error(rid, "level-wording", "a must-not statement must start with 'Do not' or 'Never'")
        if level == "must" and statement.startswith(NEGATIVE_OPENERS):
            rep.error(rid, "level-wording", "a must statement starts with 'Do not'/'Never'; use level must-not")

        for field in ("statement",):
            text = rule.get(field)
            if isinstance(text, str):
                for match in sorted({m.lower() for m in VAGUE_RE.findall(text)}):
                    rep.warn(rid, "vague-word", f"{field} uses '{match}'; say exactly when and what")

        key = " ".join(statement.split()).lower()
        if key:
            if key in statements:
                rep.warn(rid, "duplicate-statement", f"same statement as {statements[key]}")
            statements[key] = rid
        title = rule.get("title")
        if isinstance(title, str):
            tkey = title.strip().lower()
            if tkey in titles:
                rep.warn(rid, "duplicate-title", f"same title as {titles[tkey]}")
            titles[tkey] = rid

        enforced = rule.get("enforced_by")
        if isinstance(enforced, list):
            if not enforced:
                rep.error(rid, "enforced-by", "enforced_by must list at least one of: prompt, script, git")
            for value in enforced:
                if value not in ENFORCERS:
                    rep.error(rid, "enforced-by", f"enforced_by value '{value}' must be one of: prompt, script, git")

        scope = rule.get("scope")
        if isinstance(scope, str) and scope != "all":
            rep.error(rid, "scope", "scope must be \"all\" or a list of mode names")
        if isinstance(scope, list):
            if not scope:
                rep.error(rid, "scope", "scope list is empty")
            if modes is None:
                rep.warn(rid, "scope-unverified", f"cannot check mode names: {SKILL_REL} not found")
            else:
                for mode in scope:
                    if mode not in modes:
                        rep.error(rid, "scope", f"scope names mode '{mode}', which is not in the SKILL.md Modes table")

        for path in rule.get("paths", []) if isinstance(rule.get("paths"), list) else []:
            p = Path(str(path))
            if p.is_absolute() or ".." in p.parts:
                rep.error(rid, "path", f"path '{path}' must be relative to the repository and must not contain '..'")
            elif not (root / p).exists():
                rep.error(rid, "path", f"path '{path}' does not exist in the repository")

        targets = rule.get("yields_to", []) if isinstance(rule.get("yields_to"), list) else []
        yields_graph[rid] = []
        for target in targets:
            if target == rid:
                rep.error(rid, "yields-to", "a rule cannot yield to itself")
            elif target not in rule_ids:
                rep.error(rid, "yields-to", f"yields_to names '{target}', which does not exist")
            else:
                yields_graph[rid].append(target)
                other = rule_ids[target]
                if rule.get("overridable") is False and other.get("overridable") is True:
                    rep.error(
                        rid, "yields-to",
                        f"non-overridable rule yields to overridable {target}: when the user lifts "
                        f"{target}, the outcome is undecided",
                    )
                if isinstance(scope, list) and isinstance(other.get("scope"), list):
                    if not set(scope) & set(other["scope"]):
                        rep.warn(rid, "yields-to", f"yields to {target}, but their scopes never overlap")

    cycle = find_cycle(yields_graph)
    if cycle:
        rep.error("rules", "yields-cycle", "yields_to forms a loop, so neither rule decides: " + " -> ".join(cycle))

    return rep, len(rule_ids), len(term_ids)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--file", type=Path, default=None, help=f"rules file (default: {RULES_REL})")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args()

    path = args.file if args.file else ROOT / RULES_REL
    rep, n_rules, n_terms = check(load(path), ROOT)

    if args.json:
        print(json.dumps({
            "file": str(path), "rules": n_rules, "terms": n_terms,
            "errors": rep.errors, "warnings": rep.warnings,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"{path}: {n_rules} rules, {n_terms} terms")
        print(f"errors: {len(rep.errors)}")
        for e in rep.errors:
            print(f"  E  {e['where']:<14} {e['code']:<20} {e['message']}")
        print(f"warnings: {len(rep.warnings)}")
        for w in rep.warnings:
            print(f"  W  {w['where']:<14} {w['code']:<20} {w['message']}")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
