# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Model cost registry module."""

from typing import Any, ClassVar, TypedDict

from litellm import model_cost
from typing_extensions import Self


class ModelCosts(TypedDict):
    """Model costs."""

    input_cost_per_token: float
    output_cost_per_token: float


class ModelCostRegistry:
    """Registry for model costs."""

    _instance: ClassVar["Self | None"] = None
    _model_costs: dict[str, ModelCosts]

    def __new__(cls, *args: Any, **kwargs: Any) -> Self:
        """Create a new instance of ModelCostRegistry if it does not exist."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._model_costs = model_cost
            self._model_costs.setdefault(
                "gpt-5.4-mini",
                {
                    "input_cost_per_token": 0.750 / 1_000_000,
                    "output_cost_per_token": 4.500 / 1_000_000,
                },
            )
            self._initialized = True

    def register_model_costs(self, model: str, costs: ModelCosts) -> None:
        """Register the cost per unit for a given model.

        Args
        ----
            model: str
                The model id, e.g., "openai/gpt-4o".
            costs: ModelCosts
                The costs associated with the model.
        """
        self._model_costs[model] = costs

    def get_model_costs(self, model: str) -> ModelCosts | None:
        """Retrieve the cost per unit for a given model.

        Args
        ----
            model: str
                The model id, e.g., "openai/gpt-4o".

        Returns
        -------
            ModelCosts | None
                The costs associated with the model, or None if not found.

        """
        costs = self._model_costs.get(model)
        if costs is not None:
            return costs

        if "/" in model:
            return self._model_costs.get(model.split("/", 1)[1])

        return None


model_cost_registry = ModelCostRegistry()
