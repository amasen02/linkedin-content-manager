"""linkedin-content-manager — stage LinkedIn post drafts for manual review and posting.

This package never posts to LinkedIn, and never will: LinkedIn's Terms of
Service prohibit automating actions on a personal account. It exists purely
to draft, store, and track the review lifecycle of post content that a human
copies into LinkedIn's own composer by hand. See ``tests/test_no_network.py``
for the enforcement of that constraint.
"""

__version__ = "1.0.0"
