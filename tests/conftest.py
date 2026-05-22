import pytest
from pathlib import Path
from PIL import Image, ImageDraw

from src.models import DishAnalysis, FoodItem


@pytest.fixture
def sample_image_path(tmp_path: Path) -> str:
    image = Image.new("RGB", (300, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 20, 140, 140], fill="red")
    draw.rectangle([160, 40, 280, 160], fill="yellow")
    draw.rectangle([80, 180, 220, 280], fill="green")
    path = tmp_path / "test_food.png"
    image.save(path, format="PNG")
    return str(path)


@pytest.fixture
def sample_food_item() -> FoodItem:
    return FoodItem(
        name="Rice",
        calories_per_100g=130.0,
        estimated_grams=150.0,
        total_calories=195.0,
        confidence=0.9,
    )


@pytest.fixture
def sample_dish_analysis(sample_food_item: FoodItem) -> DishAnalysis:
    return DishAnalysis(
        dish_name="Test Dish",
        food_items=[
            sample_food_item,
            FoodItem("Curry", 150.0, 100.0, 150.0, 0.8),
        ],
        total_calories=345.0,
        analysis_timestamp="2025-01-01T12:00:00",
        image_path="test.jpg",
        model_used="gemini-1.5-flash",
        notes="Test notes",
    )
