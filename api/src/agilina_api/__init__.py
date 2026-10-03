"""Agilina API.

Source of truth of the domain: teams, sprints, roles, ceremonies and action
items. It issues the room tokens, runs the post-processing when a ceremony
closes, runs the scheduler and concentrates the integration adapters. It does
not take part in the room or handle audio.

Layout: one package per bounded context (``identity``, ``teams``,
``ceremonies``…), each one with the layers ``domain``, ``application``,
``presentation`` and ``infrastructure``; ``shared`` holds the cross-cutting
pieces and ``bootstrap`` is the composition root. Dependencies point inward:
presentation / infrastructure → application → domain.
"""

__version__ = "0.1.0"
