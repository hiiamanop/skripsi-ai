#!/usr/bin/env python3
"""Pintasan pengembangan: python run.py (dari repo). Pemakai akhir: uvx skripsi-ai."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from skripsi_ai.cli import main  # noqa: E402

main()
