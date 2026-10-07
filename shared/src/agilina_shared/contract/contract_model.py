from pydantic import BaseModel, ConfigDict


class ContractModel(BaseModel):
    """Common base: forbids unknown fields so that an incompatibility between
    worker and API fails right away instead of silently."""

    model_config = ConfigDict(extra="forbid", frozen=True)
