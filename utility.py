from __future__ import annotations
from typing import Any, ClassVar, Literal

def all_same(items: list[Any]) -> bool:
    if not(items): return True
    first = items[0]
    for item in items:
        if item != first:
            return False
    return True

def three_way_max(value1: int|float, value2: int|float, value3: int|float) -> tuple[int|float, Literal[1, 2, 3]]:
    """
    Returns the biggest value and the index of the biggest value i.e. 1, 2 or 3.
    Preferres left hand values on a tie.
    """
    if value1 >= value2:
        return (value1, 1) if value1 >= value3 else (value3, 3)
    elif value2 >= value3:
        return (value2, 2)
    else:
        return (value3, 3)

class SaveInstances:
    instances: ClassVar[list[SaveInstances]]
    def __init_subclass__(cls):
        cls.instances = []

    def __post_init__(self) -> None:
        type(self).instances.append(self)

__all__ = ["all_same", "SaveInstances"]
