"""Test environments, read from testdata/environments.yaml."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ENVIRONMENTS_FILE = Path(__file__).resolve().parent.parent / "testdata" / "environments.yaml"


@dataclass(frozen=True)
class Environment:
    name: str
    description: str
    appium_url: str
    udid: str              # adb serial of the device
    app_package: str
    app_activity: str


def names() -> list[str]:
    return list(_load()["environments"])


def load(name: str) -> Environment:
    data = _load()
    env = data["environments"][name]
    return Environment(name=name, description=env["description"], appium_url=env["appium_url"],
                       udid=env["udid"], app_package=data["app"]["package"],
                       app_activity=data["app"]["activity"])


def _load() -> dict:
    return yaml.safe_load(ENVIRONMENTS_FILE.read_text())
