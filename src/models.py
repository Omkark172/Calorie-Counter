import dataclasses
import datetime
import json
from typing import List, Type, TypeVar

T = TypeVar("T", bound="FoodItem")


class CalorieCounterError(Exception):
    """Base exception for Calorie Counter domain errors."""


class ImageValidationError(CalorieCounterError):
    """Raised when an image fails validation checks."""


class ImageLoadError(CalorieCounterError):
    """Raised when an image cannot be loaded from disk or memory."""


class AnalysisError(CalorieCounterError):
    """Raised when dish analysis fails or returns invalid results."""


@dataclasses.dataclass(frozen=False)
class FoodItem:
    """Represents a single food item detected in an image analysis."""

    name: str
    calories_per_100g: float
    estimated_grams: float
    total_calories: float
    confidence: float

    def __post_init__(self) -> None:
        """Validate fields and calculate total calories when not explicitly provided."""
        if self.calories_per_100g < 0:
            raise ValueError("calories_per_100g must be non-negative")

        if self.estimated_grams <= 0:
            raise ValueError("estimated_grams must be greater than zero")

        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if self.total_calories == 0:
            self.total_calories = (self.calories_per_100g * self.estimated_grams) / 100.0

    def to_dict(self) -> dict:
        """Serialize the FoodItem to a dictionary representation."""
        return {
            "name": self.name,
            "calories_per_100g": self.calories_per_100g,
            "estimated_grams": self.estimated_grams,
            "total_calories": self.total_calories,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls: Type[T], data: dict) -> T:
        """Create a FoodItem instance from a dictionary."""
        return cls(
            name=data["name"],
            calories_per_100g=float(data["calories_per_100g"]),
            estimated_grams=float(data["estimated_grams"]),
            total_calories=float(data.get("total_calories", 0.0)),
            confidence=float(data["confidence"]),
        )


@dataclasses.dataclass(frozen=False)
class DishAnalysis:
    """Represents the calorie analysis result for a dish image."""

    dish_name: str
    food_items: List[FoodItem]
    total_calories: float
    analysis_timestamp: str
    image_path: str
    model_used: str
    notes: str = ""

    def to_dict(self) -> dict:
        """Serialize the DishAnalysis and its food items to a dictionary."""
        return {
            "dish_name": self.dish_name,
            "food_items": [item.to_dict() for item in self.food_items],
            "total_calories": self.total_calories,
            "analysis_timestamp": self.analysis_timestamp,
            "image_path": self.image_path,
            "model_used": self.model_used,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DishAnalysis":
        """Create a DishAnalysis instance from a dictionary."""
        return cls(
            dish_name=data["dish_name"],
            food_items=[FoodItem.from_dict(item) for item in data.get("food_items", [])],
            total_calories=float(data["total_calories"]),
            analysis_timestamp=data["analysis_timestamp"],
            image_path=data["image_path"],
            model_used=data["model_used"],
            notes=data.get("notes", ""),
        )

    @property
    def calorie_level(self) -> str:
        """Return a descriptive calorie level based on the total calories."""
        if self.total_calories < 300:
            return "Low"

        if 300 <= self.total_calories <= 600:
            return "Medium"

        return "High"
