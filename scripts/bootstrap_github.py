#!/usr/bin/env python3
"""Create the GitHub repository, Project and Phase 1 epic/sub-issue backlog.

Requires Git, GitHub CLI (gh), Python 3.11+ and an authenticated gh session.
This script performs real remote writes only when explicitly executed by the user.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "project" / "backlog_phase1.json"


def run(command: list[str], *, cwd: Path = ROOT, capture: bool = True) -> str:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=capture)
    if proc.returncode != 0:
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(command)}\n{stdout}\n{stderr}"
        )
    return (proc.stdout or "").strip()


def has_command(name: str) -> bool:
    from shutil import which
    return which(name) is not None


def ensure_git_commit() -> None:
    if not (ROOT / ".git").exists():
        run(["git", "init", "-b", "main"])
    status = run(["git", "status", "--porcelain"])
    if status:
        run(["git", "add", "."])
        try:
            run(["git", "commit", "-m", "Initial FitEvidence AI project structure"])
        except RuntimeError as exc:
            # Git may need local user.name/user.email configured.
            raise RuntimeError(
                "No se pudo crear el commit inicial. Configura git user.name y user.email "
                "y vuelve a ejecutar el script.\n" + str(exc)
            ) from exc
    else:
        # An empty local repository cannot be pushed; create an empty first commit.
        try:
            run(["git", "rev-parse", "HEAD"])
        except RuntimeError:
            run(["git", "commit", "--allow-empty", "-m", "Initial FitEvidence AI commit"])


def get_owner() -> str:
    return run(["gh", "api", "user", "--jq", ".login"])


def ensure_remote_repo(repo_name: str, visibility: str, owner: str) -> str:
    repo_full = f"{owner}/{repo_name}"
    try:
        run(["gh", "repo", "view", repo_full])
        # Ensure local repo points to the intended remote.
        remotes = run(["git", "remote", "-v"])
        if not remotes.strip():
            run(["git", "remote", "add", "origin", f"https://github.com/{repo_full}.git"])
        elif "github.com" not in remotes or repo_name not in remotes:
            raise RuntimeError(
                f"El repositorio {repo_full} ya existe, pero el remoto local apunta a otro destino. "
                "Comprueba `git remote -v` antes de continuar."
            )
        run(["git", "push", "-u", "origin", "HEAD"])
        return repo_full
    except RuntimeError as exc:
        # Only create when gh repo view failed because repo does not exist.
        msg = str(exc).lower()
        if "not found" not in msg and "could not resolve" not in msg and "404" not in msg:
            raise
    vis_flag = "--private" if visibility == "private" else "--public"
    run([
        "gh", "repo", "create", repo_name, vis_flag,
        "--source=.", "--remote=origin", "--push",
        "--description", "TFM: generación y evaluación de planes de entrenamiento personalizados basada en evidencia científica"
    ])
    return repo_full


def parse_number_from_url(output: str) -> int:
    match = re.search(r"/(?:issues|projects)/(\d+)(?:\s|$)", output.strip())
    if not match:
        # gh issue create typically prints the issue URL; project create JSON is parsed separately.
        match = re.search(r"(\d+)\s*$", output.strip())
    if not match:
        raise RuntimeError(f"No se pudo extraer el número de la salida: {output}")
    return int(match.group(1))


def create_or_reuse_project(owner: str, title: str, description: str) -> int:
    existing = json.loads(run(["gh", "project", "list", "--owner", owner, "--format", "json"]))
    items = existing if isinstance(existing, list) else existing.get("projects", [])
    for item in items:
        if item.get("title") == title:
            number = int(item["number"])
            print(f"Proyecto existente reutilizado: #{number}")
            return number
    created = json.loads(run([
        "gh", "project", "create", "--owner", owner, "--title", title, "--format", "json"
    ]))
    number = int(created.get("number") or created.get("project", {}).get("number"))
    run(["gh", "project", "edit", str(number), "--owner", owner,
         "--visibility", "PRIVATE", "--description", description])
    return number


def create_fields(owner: str, project_number: int, fields: list[dict[str, Any]]) -> None:
    existing_raw = run(["gh", "project", "field-list", str(project_number), "--owner", owner, "--format", "json"])
    existing_obj = json.loads(existing_raw)
    existing = existing_obj if isinstance(existing_obj, list) else existing_obj.get("fields", [])
    existing_names = {f.get("name") for f in existing}
    for field in fields:
        if field["name"] in existing_names:
            continue
        cmd = ["gh", "project", "field-create", str(project_number), "--owner", owner,
               "--name", field["name"], "--data-type", field["type"], "--format", "json"]
        if field["type"] == "SINGLE_SELECT":
            cmd += ["--single-select-options", ",".join(field["options"])]
        run(cmd)


def create_labels(repo_full: str, labels: list[dict[str, str]]) -> None:
    for label in labels:
        run([
            "gh", "label", "create", label["name"], "--repo", repo_full,
            "--color", label["color"], "--description", label["description"], "--force"
        ])


def create_issue(repo_full: str, project_title: str, title: str, body: str,
                 labels: list[str], parent: int | None = None) -> tuple[int, str]:
    import tempfile
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as tmp:
        tmp.write(body)
        body_path = Path(tmp.name)
    try:
        cmd = ["gh", "issue", "create", "--repo", repo_full, "--title", title,
               "--body-file", str(body_path), "--project", project_title]
        for label in labels:
            cmd += ["--label", label]
        if parent is not None:
            cmd += ["--parent", str(parent)]
        url = run(cmd)
    finally:
        body_path.unlink(missing_ok=True)
    number = parse_number_from_url(url)
    return number, url


def epic_body(epic: dict[str, Any]) -> str:
    lines = [f"## Objetivo\n{epic['objective']}", "## Definition of Done"]
    lines += [f"- [ ] {x}" for x in epic["definition_of_done"]]
    lines += ["## Subtareas"]
    lines += [f"- [ ] **{s['id']}** — {s['title']}" for s in epic["subtasks"]]
    lines += ["\nDocumentar avances, comentarios, bloqueos y evidencias en cada issue."]
    return "\n\n".join(lines)


def subtask_body(sub: dict[str, Any], parent_id: str) -> str:
    lines = [f"## Objetivo\n{sub['body']}", "## Definition of Done"]
    lines += [f"- [ ] {x}" for x in sub["dod"]]
    lines += ["## Evidencias / comentarios\nAñadir enlaces a commits, notebooks, resultados o decisiones relevantes.",
              f"\nÉpica padre: {parent_id}."]
    return "\n\n".join(lines)


def priority_label(priority: str) -> str:
    return {"P0": "priority-p0", "P1": "priority-p1", "P2": "priority-p2"}.get(priority, "priority-p1")


def set_project_item_fields(project_number: int, owner: str, issue_url: str,
                            priority: str, workstream: str) -> None:
    priority_value = {"P0": "P0 - Crítica", "P1": "P1 - Alta", "P2": "P2 - Media"}.get(priority, "P1 - Alta")
    for field, value in (("Phase", "Fase 1"), ("Priority", priority_value), ("Workstream", workstream)):
        run(["gh", "project", "item-edit", str(project_number), "--owner", owner,
             "--url", issue_url, "--field", field, "--value", value])


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap GitHub repository and Phase 1 Project backlog")
    parser.add_argument("--visibility", choices=["private", "public"], default="private",
                        help="Visibility of the repository (default: private). The Project remains private.")
    parser.add_argument("--skip-push", action="store_true",
                        help="Do not create/push the repository; assumes a configured remote already exists.")
    args = parser.parse_args()

    if not has_command("git") or not has_command("gh"):
        print("ERROR: instala Git y GitHub CLI (gh) antes de continuar.", file=sys.stderr)
        return 2
    try:
        run(["gh", "auth", "status"])
    except RuntimeError:
        print("Ejecuta primero: gh auth login", file=sys.stderr)
        return 2

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ensure_git_commit()
    owner = get_owner()
    if args.skip_push:
        repo_full = f"{owner}/{manifest['repo_name']}"
        run(["gh", "repo", "view", repo_full])
    else:
        repo_full = ensure_remote_repo(manifest["repo_name"], args.visibility, owner)

    # Project operations require the 'project' token scope.
    project_number = create_or_reuse_project(owner, manifest["project_title"], manifest["project_description"])
    try:
        run(["gh", "project", "link", str(project_number), "--owner", owner, "--repo", repo_full])
    except RuntimeError as exc:
        if "already" not in str(exc).lower() and "linked" not in str(exc).lower():
            raise
    create_fields(owner, project_number, manifest["fields"])
    create_labels(repo_full, manifest["labels"])

    # Avoid duplicates on a resumed run by matching exact issue titles.
    existing_raw = run(["gh", "issue", "list", "--repo", repo_full, "--state", "all",
                        "--limit", "1000", "--json", "number,title,url"])
    existing_issues = json.loads(existing_raw)
    by_title = {issue["title"]: issue for issue in existing_issues}

    epic_numbers: dict[str, int] = {}
    for epic in manifest["epics"]:
        if epic["title"] in by_title:
            existing = by_title[epic["title"]]
            epic_numbers[epic["id"]] = int(existing["number"])
            url = existing["url"]
            run(["gh", "issue", "edit", str(epic_numbers[epic["id"]]), "--repo", repo_full,
                 "--add-project", manifest["project_title"]])
            print(f"Épica existente: {epic['id']} #{epic_numbers[epic['id']]}")
        else:
            labels = list(dict.fromkeys(epic["labels"] + ["phase-1", priority_label(epic["priority"])]))
            number, url = create_issue(repo_full, manifest["project_title"], epic["title"],
                                       epic_body(epic), labels)
            epic_numbers[epic["id"]] = number
            print(f"Creada épica {epic['id']}: {url}")
        set_project_item_fields(project_number, owner, url, epic["priority"], epic["workstream"])

    created_subtasks = 0
    for epic in manifest["epics"]:
        parent_number = epic_numbers[epic["id"]]
        for sub in epic["subtasks"]:
            if sub["title"] in by_title:
                existing = by_title[sub["title"]]
                existing_number = int(existing["number"])
                url = existing["url"]
                run(["gh", "issue", "edit", str(existing_number), "--repo", repo_full,
                     "--parent", str(parent_number), "--add-project", manifest["project_title"]])
                print(f"Subtarea existente: {sub['id']} #{existing_number}")
            else:
                area_label = ("evaluation" if sub["workstream"] == "Evaluation" else
                              ("safety" if sub["workstream"] == "Safety" else
                               ("data" if sub["workstream"] == "Data" else
                                ("model" if sub["workstream"] == "Model" else
                                 ("documentation" if sub["workstream"] == "Documentation" else "research")))) )
                labels = ["phase-1", "task", priority_label(sub["priority"]), area_label]
                number, url = create_issue(repo_full, manifest["project_title"], sub["title"],
                                           subtask_body(sub, epic["id"]), labels, parent=parent_number)
                created_subtasks += 1
                print(f"Creada subtarea {sub['id']}: {url}")
            set_project_item_fields(project_number, owner, url, sub["priority"], sub["workstream"])

    print(f"Subtareas creadas en esta ejecución: {created_subtasks}")
    print("\nBootstrap terminado.")
    print(f"Repositorio: https://github.com/{repo_full}")
    print(f"Proyecto: https://github.com/users/{owner}/projects/{project_number}")
    print("Consejo: cread una vista Board agrupada por Status y filtrad Phase = Fase 1.")
    print("Si la creación se interrumpió, revisad los issues existentes antes de reintentar.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
