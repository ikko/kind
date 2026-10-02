"""This module checks that a callable has the shape of a Kind mixin method.

It inspects the signature only: the first parameter must be `self`. It does not
judge what the code does — a mixin is trusted code, like any method of the class.
"""
import inspect
from typing import Any, Callable, Dict, List, Optional


class MixinValidationResult:
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self) -> bool:
        return self.is_valid

    def __repr__(self) -> str:
        status = "Valid" if self.is_valid else "Invalid"
        return f"<MixinValidationResult: {status}, Errors: {len(self.errors)}, Warnings: {len(self.warnings)}>"

    def to_dict(self) -> Dict[str, Any]:
        return {"is_valid": self.is_valid, "errors": self.errors, "warnings": self.warnings}


def validate_mixin_callable(func: Callable[..., Any]) -> MixinValidationResult:
    """Validates that `func` can be bound as a Kind method."""
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError) as error:
        return MixinValidationResult(False, errors=[f"cannot read the signature of {func!r}: {error}"])

    errors, warnings = [], []
    parameters = list(signature.parameters)
    if not parameters or parameters[0] != 'self':
        errors.append(f"mixin {getattr(func, '__name__', func)!r} must take 'self' as its first parameter")
    if signature.return_annotation is inspect.Signature.empty:
        warnings.append("no return type annotation")
    return MixinValidationResult(not errors, errors=errors, warnings=warnings)
