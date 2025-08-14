"""Type guards for RTF components to handle Union types safely."""
from typing import TypeGuard
from .input import RTFColumnHeader, RTFBody


def is_single_header(
    header: RTFColumnHeader | list[RTFColumnHeader | None] | None,
) -> TypeGuard[RTFColumnHeader]:
    """Check if header is a single RTFColumnHeader instance."""
    return header is not None and not isinstance(header, list)


def is_single_body(body: RTFBody | list[RTFBody] | None) -> TypeGuard[RTFBody]:
    """Check if body is a single RTFBody instance."""
    return body is not None and not isinstance(body, list)


def is_list_header(
    header: RTFColumnHeader | list[RTFColumnHeader | None] | None,
) -> TypeGuard[list[RTFColumnHeader | None]]:
    """Check if header is a list of RTFColumnHeader instances."""
    return isinstance(header, list)


def is_list_body(body: RTFBody | list[RTFBody] | None) -> TypeGuard[list[RTFBody]]:
    """Check if body is a list of RTFBody instances."""
    return isinstance(body, list)