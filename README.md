# 🥗 Calorie Counter AI Agent

AI-powered food calorie analyzer — upload any dish photo and get instant calorie breakdown.

## Features
- Detects all food items in a photo
- Estimates portion sizes visually
- Shows calories per item and total
- Confidence scores for each detection
- Save results as JSON
- 100% FREE (uses Google Gemini free tier)

## Setup

### 1.

### 2. Install
```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Open .env and paste your API key
```

## Usage
```bash
# Analyze a food photo
python src/agent.py your_food_photo.jpg

# Save results to JSON
python src/agent.py your_food_photo.jpg --output results/my_meal.json

# Verbose/debug mode
python src/agent.py your_food_photo.jpg --verbose
```

## Run Tests
```bash
python -m pytest tests/ -v
```

## Free Tier Limits
- Google Gemini 1.5 Flash: 1,500 requests/day, 15/minute
- GitHub Copilot: Free with GitHub account
