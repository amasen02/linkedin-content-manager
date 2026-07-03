"""Exceptions raised by linkedin_content_manager."""

from __future__ import annotations


class ContentManagerError(Exception):
    """Base class for every error this package raises."""


class DraftNotFoundError(ContentManagerError):
    """No staged draft exists with the given id."""


class InvalidTransitionError(ContentManagerError):
    """The requested status change is not a legal transition for this draft."""


class DraftValidationError(ContentManagerError):
    """The draft content violates a LinkedIn platform constraint."""
