from agilina_api.shared_kernel import DomainError


class InvalidTokenHashError(DomainError):
    """A token hash must be a SHA-256 digest in hexadecimal."""
