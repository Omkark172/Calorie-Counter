import pytest

from src.models import DishAnalysis, FoodItem


def test_food_item_creation_valid():
    FoodItem("Rice", 130.0, 150.0, 195.0, 0.9)


@pytest.mark.parametrize(
    "confidence,raises",
    [(-0.1, True), (0.0, False), (0.5, False), (1.0, False), (1.1, True)],
)
def test_food_item_confidence_boundaries(confidence, raises):
    if raises:
        with pytest.raises(ValueError):
            FoodItem("Test", 100.0, 100.0, 100.0, confidence)
    else:
        FoodItem("Test", 100.0, 100.0, 100.0, confidence)


def test_food_item_negative_calories_raises():
    with pytest.raises(ValueError):
        FoodItem("Rice", -10.0, 150.0, 0.0, 0.9)


def test_food_item_zero_estimated_grams_raises():
    with pytest.raises(ValueError):
        FoodItem("Rice", 130.0, 0.0, 0.0, 0.9)


def test_food_item_confidence_too_high_raises():
    with pytest.raises(ValueError):
        FoodItem("Rice", 130.0, 150.0, 0.0, 1.5)


def test_food_item_confidence_too_low_raises():
    with pytest.raises(ValueError):
        FoodItem("Rice", 130.0, 150.0, 0.0, -0.1)


def test_food_item_to_dict():
    item = FoodItem("Rice", 130.0, 150.0, 195.0, 0.9)
    result = item.to_dict()
    assert result == {
        "name": "Rice",
        "calories_per_100g": 130.0,
        "estimated_grams": 150.0,
        "total_calories": 195.0,
        "confidence": 0.9,
    }


def test_food_item_from_dict_round_trip():
    original = FoodItem("Rice", 130.0, 150.0, 195.0, 0.9)
    round_trip = FoodItem.from_dict(original.to_dict())
    assert round_trip == original


def test_dish_analysis_calorie_level():
    assert DishAnalysis("Dish", [], 200.0, "2025-01-01T12:00:00", "test.jpg", "model").calorie_level == "Low"
    assert DishAnalysis("Dish", [], 450.0, "2025-01-01T12:00:00", "test.jpg", "model").calorie_level == "Medium"
    assert DishAnalysis("Dish", [], 750.0, "2025-01-01T12:00:00", "test.jpg", "model").calorie_level == "High"


def test_dish_analysis_to_dict_includes_food_items(sample_food_item):
    analysis = DishAnalysis(
        dish_name="Dish",
        food_items=[sample_food_item],
        total_calories=195.0,
        analysis_timestamp="2025-01-01T12:00:00",
        image_path="test.jpg",
        model_used="model",
    )
    result = analysis.to_dict()
    assert isinstance(result["food_items"], list)
    assert result["food_items"][0]["name"] == "Rice"


def test_dish_analysis_from_dict_recreates_food_items(sample_food_item):
    analysis = DishAnalysis(
        dish_name="Dish",
        food_items=[sample_food_item],
        total_calories=195.0,
        analysis_timestamp="2025-01-01T12:00:00",
        image_path="test.jpg",
        model_used="model",
    )
    recreated = DishAnalysis.from_dict(analysis.to_dict())
    assert recreated.food_items[0] == sample_food_item
