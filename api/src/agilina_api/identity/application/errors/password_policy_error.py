from agilina_api.shared_kernel import DomainError


class PasswordPolicyError(DomainError):
    """The identity provider refused the password.

    ``reasons`` are stable codes the interface turns into messages (``min_length``,
    ``not_username``, ``not_email``, ``other``).
    """

    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__("The password does not meet the policy: " + ", ".join(reasons))
        self.reasons = reasons
