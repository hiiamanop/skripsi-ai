#!/usr/bin/env python3
"""Buat proyek SLR baru: slr/<nama>/protocol.json template.

Pakai:  .venv/bin/python slr_init.py <nama | path>
"""
import argparse
import json
import os

import config

TEMPLATE = {
    "research_questions": [],
    "inclusion": [],
    "exclusion": [],
    "qa_checklist": [{"id": "qa1", "question": "", "weight": 1}],
}


def slr_init(project):
    path = project if os.path.isabs(project) or "/" in project else f"{config.SLR_DIR}/{project}"
    os.makedirs(path, exist_ok=True)
    with open(f"{path}/protocol.json", "w") as f:
        json.dump(TEMPLATE, f, indent=2)
    return path


def main():
    a = argparse.ArgumentParser()
    a.add_argument("project")
    a = a.parse_args()
    print(slr_init(a.project))


if __name__ == "__main__":
    main()
