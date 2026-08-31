"""Unit tests for the robust JSON extractor."""

# pyrefly: ignore [missing-import]
import pytest
from app.core.json_parser import extract_json


def test_clean_json():
    raw = '{"name": "test", "val": 123}'
    assert extract_json(raw) == {"name": "test", "val": 123}


def test_json_with_think_block():
    raw = """<think>
Let's analyze the user's nutritional requirements and create a meal plan.
First, we check calories and macros...
</think>
{
  "breakfast": {"meal_name": "Breakfast", "foods": [], "total_calories": 300, "total_protein_g": 20, "total_carbs_g": 30, "total_fat_g": 10},
  "lunch": {"meal_name": "Lunch", "foods": [], "total_calories": 500, "total_protein_g": 40, "total_carbs_g": 50, "total_fat_g": 15},
  "dinner": {"meal_name": "Dinner", "foods": [], "total_calories": 400, "total_protein_g": 30, "total_carbs_g": 40, "total_fat_g": 12},
  "snack": null,
  "total_daily_calories": 1200,
  "total_daily_protein_g": 90,
  "total_daily_carbs_g": 120,
  "total_daily_fat_g": 37
}"""
    data = extract_json(raw)
    assert data["total_daily_calories"] == 1200


def test_json_in_markdown_fences_with_chatter():
    raw = """Sure! Here is the JSON output for the meal plan:
```json
{"notes": "Enjoy your meal!"}
```
Hope this helps!"""
    assert extract_json(raw) == {"notes": "Enjoy your meal!"}


def test_json_extracted_from_braces_only():
    raw = 'Here is the result: {"status": "ok", "items": [1, 2]} thanks.'
    assert extract_json(raw) == {"status": "ok", "items": [1, 2]}


def test_empty_raises_error():
    with pytest.raises(ValueError, match="Cannot extract JSON from empty response"):
        extract_json("")
