import datetime
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai

try:
    from src.image_processor import ImageProcessor
    from src.models import AnalysisError, DishAnalysis, FoodItem
except ImportError:
    from image_processor import ImageProcessor
    from models import AnalysisError, DishAnalysis, FoodItem


class CalorieAnalyzer:
    """Analyzes food images using Google Generative AI to estimate calories and ingredients."""

    def __init__(self, api_key: str, model_name: str = "models/gemini-flash-latest") -> None:
        """Initialize the analyzer, configure the API, and prepare supporting services."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.image_processor = ImageProcessor()
        self.last_request_time = 0.0
        self.min_request_gap = 4.0
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialized CalorieAnalyzer with model_name=%s", self.model_name)

    def _enforce_rate_limit(self) -> None:
        """Wait as needed to enforce a minimum gap between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_gap:
            wait_seconds = self.min_request_gap - elapsed
            self.logger.debug("Rate limit active, sleeping for %.2f seconds", wait_seconds)
            time.sleep(wait_seconds)
        self.last_request_time = time.time()

    def _build_prompt(self) -> str:
        """Return the exact prompt used for calorie analysis."""
        return (
            "You are a professional nutritionist and food scientist with expertise in calorie estimation.\n"
            "Analyze this food image carefully and identify every food item visible.\n\n"
            "Return ONLY a valid JSON object with this exact structure, no other text:\n"
            "{\n"
            "  \"dish_name\": \"name of the overall dish or meal\",\n"
            "  \"food_items\": [\n"
            "    {\n"
            "      \"name\": \"specific food item name\",\n"
            "      \"calories_per_100g\": 150,\n"
            "      \"estimated_grams\": 200,\n"
            "      \"total_calories\": 300,\n"
            "      \"confidence\": 0.9\n"
            "    }\n"
            "  ],\n"
            "  \"total_calories\": 300,\n"
            "  \"notes\": \"any nutritional notes or caveats\"\n"
            "}\n\n"
            "Important rules:\n"
            "- Include ALL visible food items including sauces, garnishes, drinks\n"
            "- estimated_grams is your best visual estimate of portion size\n"
            "- confidence is how certain you are about identification (0.0 to 1.0)\n"
            "- total_calories for each item = (calories_per_100g * estimated_grams) / 100\n"
            "- total_calories at root level = sum of all items\n"
            "- Return ONLY the JSON object, no markdown fences, no explanation"
        )

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the model response text into a JSON dictionary."""
        self.logger.debug("Parsing response text: %s", response_text)
        parsed: Optional[Dict[str, Any]] = None

        try:
            parsed = json.loads(response_text.strip())
            self.logger.debug("Parsed JSON successfully on first attempt")
        except json.JSONDecodeError:
            self.logger.debug("First JSON parse failed, attempting regex extraction")
            match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    self.logger.debug("Parsed JSON successfully from regex extraction")
                except json.JSONDecodeError:
                    self.logger.debug("Regex JSON extraction failed, attempting markdown cleanup")

            if parsed is None:
                cleaned = response_text.replace("```json", "").replace("```", "").strip()
                try:
                    parsed = json.loads(cleaned)
                    self.logger.debug("Parsed JSON successfully after markdown cleanup")
                except json.JSONDecodeError:
                    self.logger.error("Could not parse response text into JSON")
                    raise AnalysisError(f"Could not parse response: {response_text[:200]}")

        if not isinstance(parsed, dict):
            self.logger.error("Parsed response is not a dictionary")
            raise AnalysisError(f"Could not parse response: {response_text[:200]}")

        if "food_items" not in parsed:
            self.logger.error("Parsed response missing food_items key")
            raise AnalysisError("Parsed response missing 'food_items' key")

        return parsed

    def _response_to_analysis(self, parsed: Dict[str, Any], image_path: str) -> DishAnalysis:
        """Convert parsed model output into a DishAnalysis object."""
        self.logger.debug("Converting parsed response to DishAnalysis: %s", parsed)
        food_items = []

        raw_items = parsed.get("food_items", [])
        if not isinstance(raw_items, list):
            raise AnalysisError("'food_items' must be a list")

        for item_data in raw_items:
            try:
                if not isinstance(item_data, dict):
                    raise ValueError("Each food item must be a dictionary")

                food_item = FoodItem(
                    name=str(item_data["name"]),
                    calories_per_100g=float(item_data["calories_per_100g"]),
                    estimated_grams=float(item_data["estimated_grams"]),
                    total_calories=float(item_data["total_calories"]),
                    confidence=float(item_data["confidence"]),
                )
                food_items.append(food_item)
            except Exception as exc:
                self.logger.warning("Skipping invalid food item entry: %s; error: %s", item_data, exc)

        if not food_items:
            raise AnalysisError("No valid food items were produced by analysis")

        total_calories = float(parsed.get("total_calories", sum(item.total_calories for item in food_items)))
        analysis = DishAnalysis(
            dish_name=str(parsed.get("dish_name", "unknown dish")),
            food_items=food_items,
            total_calories=total_calories,
            analysis_timestamp=datetime.datetime.now().isoformat(),
            image_path=image_path,
            model_used=self.model_name,
            notes=str(parsed.get("notes", "")),
        )
        self.logger.info("Constructed DishAnalysis for image %s", image_path)
        return analysis

    def analyze_dish(self, image_path: str) -> DishAnalysis:
        """Analyze a dish image and return structured calorie analysis."""
        self.logger.debug("Starting dish analysis for %s", image_path)
        try:
            pil_image, _ = self.image_processor.load_and_encode(image_path)
        except Exception as exc:
            self.logger.exception("Image loading failed")
            raise AnalysisError(str(exc))

        prompt = self._build_prompt()
        last_error: Optional[Exception] = None

        for attempt in range(1, 4):
            self.logger.info("Analysis attempt %d for image %s", attempt, image_path)
            try:
                self._enforce_rate_limit()
                result = self.model.generate_content([prompt, pil_image])
                response_text = getattr(result, "text", None)
                if response_text is None:
                    raise AnalysisError("API returned no text response")

                parsed = self._parse_response(response_text)
                analysis = self._response_to_analysis(parsed, image_path)
                self.logger.info("Dish analysis succeeded for %s", image_path)
                return analysis
            except Exception as exc:
                last_error = exc
                self.logger.warning("Analysis attempt %d failed: %s", attempt, exc)
                if attempt < 3:
                    backoff = 2 ** (attempt - 1)
                    self.logger.debug("Sleeping for %d seconds before retry", backoff)
                    time.sleep(backoff)

        raise AnalysisError(f"Analysis failed after 3 attempts: {last_error}")
