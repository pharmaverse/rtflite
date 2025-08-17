"""Type guards for RTF components to handle Union types safely."""

from collections.abc import Sequence
from typing import Any, TypeGuard

from .input import RTFBody, RTFColumnHeader


def is_single_header(
    header: RTFColumnHeader | Sequence[RTFColumnHeader | None] | None,
) -> TypeGuard[RTFColumnHeader]:
    """Check if header is a single RTFColumnHeader instance."""
    return header is not None and not isinstance(header, (list, tuple))


def is_single_body(body: RTFBody | Sequence[RTFBody] | None) -> TypeGuard[RTFBody]:
    """Check if body is a single RTFBody instance."""
    return body is not None and not isinstance(body, (list, tuple))


def is_list_header(
    header: RTFColumnHeader | Sequence[RTFColumnHeader | None] | None,
) -> TypeGuard[Sequence[RTFColumnHeader | None]]:
    """Check if header is a sequence of RTFColumnHeader instances."""
    return isinstance(header, (list, tuple))


def is_list_body(
    body: RTFBody | Sequence[RTFBody] | None,
) -> TypeGuard[Sequence[RTFBody]]:
    """Check if body is a sequence of RTFBody instances."""
    return isinstance(body, (list, tuple))


def is_nested_header_list(
    header: Any,
) -> TypeGuard[list[list[RTFColumnHeader | None]]]:
    """Check if header is a nested list of RTFColumnHeader instances."""
    return isinstance(header, list) and len(header) > 0 and isinstance(header[0], list)


def is_flat_header_list(
    header: Any,
) -> TypeGuard[list[RTFColumnHeader | None]]:
    """Check if header is a flat list of RTFColumnHeader instances."""
    return isinstance(header, list) and (
        len(header) == 0 or not isinstance(header[0], list)
    )
