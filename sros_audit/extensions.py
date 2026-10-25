"""Reserved interfaces only: no configuration execution is implemented."""
from typing import Protocol

class NetconfReader(Protocol):
    def get_state(self, filter_xml: str) -> str: ...

class ConfigurationValidator(Protocol):
    def validate(self, candidate: str) -> list[str]: ...

class MOPGenerator(Protocol):
    def render(self, plan: dict) -> str: ...
