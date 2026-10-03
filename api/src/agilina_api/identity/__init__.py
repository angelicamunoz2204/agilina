"""Identity context: invitations, account activation, the link with Keycloak and
the visible label of a role. First story: HU-02 (account activation by invitation).

Layers: ``domain`` · ``application`` · ``presentation`` · ``infrastructure``.
Keycloak owns credentials and sessions; this context owns who may enter which team.
"""
