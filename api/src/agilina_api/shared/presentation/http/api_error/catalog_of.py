from agilina_api.shared.presentation.http.api_error.api_error import ApiError


def catalog_of(errors: type) -> tuple[ApiError, ...]:
    """Every entry a catalog class declares."""
    return tuple(value for value in vars(errors).values() if isinstance(value, ApiError))
