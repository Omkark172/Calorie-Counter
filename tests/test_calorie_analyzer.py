import json
from unittest.mock import MagicMock, patch

import pytest

from src import AnalysisError, CalorieAnalyzer


def test_parse_response_clean_json():
    analyzer = CalorieAnalyzer(api_key="test_key")
    data = {
        "dish_name": "Test",
        "food_items": [
            {
                "name": "Rice",
                "calories_per_100g": 130,
                "estimated_grams": 150,
                "total_calories": 195,
                "confidence": 0.9,
            }
        ],
        "total_calories": 195,
        "notes": "None",
    }
    parsed = analyzer._parse_response(json.dumps(data))
    assert parsed["food_items"]


def test_parse_response_markdown_wrapped_json():
    analyzer = CalorieAnalyzer(api_key="test_key")
    payload = """```json
{"dish_name": "Test", "food_items": [], "total_calories": 0, "notes": "None"}
```"""
    parsed = analyzer._parse_response(payload)
    assert parsed["total_calories"] == 0


def test_parse_response_invalid_string_raises():
    analyzer = CalorieAnalyzer(api_key="test_key")
    with pytest.raises(AnalysisError):
        analyzer._parse_response("not valid json")


def test_parse_response_missing_food_items_raises():
    analyzer = CalorieAnalyzer(api_key="test_key")
    with pytest.raises(AnalysisError):
        analyzer._parse_response(json.dumps({"dish_name": "Test", "total_calories": 0}))


def test_analyze_dish_retries_on_api_failure(tmp_path, sample_image_path: str):
    analyzer = CalorieAnalyzer(api_key="test_key")
    mock_result = MagicMock()
    mock_result.text = json.dumps({
        "dish_name": "Test",
        "food_items": [
            {
                "name": "Rice",
                "calories_per_100g": 130,
                "estimated_grams": 150,
                "total_calories": 195,
                "confidence": 0.9,
            }
        ],
        "total_calories": 195,
        "notes": "None",
    })

    with patch.object(analyzer, "_enforce_rate_limit", return_value=None), patch.object(analyzer.model, "generate_content", side_effect=[Exception("fail1"), Exception("fail2"), mock_result]):
        analysis = analyzer.analyze_dish(sample_image_path)
        assert analysis.dish_name == "Test"
        assert len(analysis.food_items) == 1
