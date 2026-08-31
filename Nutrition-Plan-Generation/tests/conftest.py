"""Pytest configuration and shared fixtures."""

# pyrefly: ignore [missing-import]
import pytest

# pyrefly: ignore [missing-import]
import sys

# pyrefly: ignore [missing-import]
import os

# Ensure the project root is on sys.path so `app` is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
