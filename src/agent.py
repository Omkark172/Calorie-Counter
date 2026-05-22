import argparse
import json
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

try:
    from src import (
        CalorieCounterError,
        DishAnalysis,
        ensure_directory,
        format_calories,
        get_calorie_emoji,
        get_confidence_label,
        setup_logging,
    )
    from src.calorie_analyzer import CalorieAnalyzer
except ImportError:
    from calorie_analyzer import CalorieAnalyzer
    from models import DishAnalysis, CalorieCounterError
    from utils import ensure_directory, format_calories, get_calorie_emoji, get_confidence_label, setup_logging


class CalorieCounterAgent:
    """Main application agent for analyzing food images and displaying results."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the agent, load environment variables, and configure logging."""
        load_dotenv()
        setup_logging(verbose)
        self.logger = logging.getLogger("calorie_counter")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Please:\n"
                "1. Copy .env.example to .env\n"
                "2. Add your free API key from https://aistudio.google.com/app/apikey"
            )

        self.analyzer = CalorieAnalyzer(api_key=api_key)
        self.console = Console()

    def run(self, image_path: str) -> DishAnalysis:
        """Run the analysis workflow for the provided image path."""
        title_text = Text(f"Analyzing image: {image_path}", style="bold white")
        self.console.print(Panel(title_text, title="🥗 Calorie Counter AI Agent", expand=False))

        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            transient=True,
            console=self.console,
        ) as progress:
            task = progress.add_task("Analyzing dish with Gemini AI...", start=False)
            progress.start_task(task)
            analysis = self.analyzer.analyze_dish(image_path)

        return analysis

    def display_results(self, analysis: DishAnalysis) -> None:
        """Display the calorie analysis results in a rich table and summary panel."""
        table = Table(title=f"📊 Analysis: {analysis.dish_name}")
        table.add_column("Food Item", style="bold", no_wrap=True)
        table.add_column("Est. Weight", justify="right")
        table.add_column("Cal/100g", justify="right")
        table.add_column("Total Cal", justify="right")
        table.add_column("Confidence", justify="right")

        for item in analysis.food_items:
            confidence_style = "green"
            if item.confidence < 0.5:
                confidence_style = "red"
            elif item.confidence < 0.8:
                confidence_style = "yellow"

            table.add_row(
                item.name,
                f"{item.estimated_grams:.0f} g",
                f"{item.calories_per_100g:.0f}",
                f"{item.total_calories:.0f}",
                f"[{confidence_style}]{item.confidence:.2f}[/{confidence_style}]",
            )

        self.console.print(table)

        calorie_emoji = get_calorie_emoji(analysis.total_calories)
        total_calories_text = f"{format_calories(analysis.total_calories)} {calorie_emoji}"
        level_style = "bold green" if analysis.calorie_level == "Low" else "bold yellow" if analysis.calorie_level == "Medium" else "bold red"

        summary = Text()
        summary.append(f"Dish: ", style="bold")
        summary.append(f"{analysis.dish_name}\n")
        summary.append(f"Total Calories: ", style="bold")
        summary.append(f"{total_calories_text}\n")
        summary.append(f"Calorie Level: ", style="bold")
        summary.append(f"{analysis.calorie_level}\n", style=level_style)
        summary.append(f"Items Detected: ", style="bold")
        summary.append(f"{len(analysis.food_items)}\n")
        summary.append(f"Analyzed At: ", style="bold")
        summary.append(f"{analysis.analysis_timestamp}\n")
        summary.append(f"Notes: ", style="bold")
        summary.append(f"{analysis.notes or 'None'}")

        self.console.print(Panel(summary, title="Summary", expand=False))

    def save_results(self, analysis: DishAnalysis, output_path: str) -> None:
        """Save the analysis results as a JSON file to the specified path."""
        path = Path(output_path)
        ensure_directory(str(path.parent or Path(".")))

        with path.open("w", encoding="utf-8") as handler:
            json.dump(analysis.to_dict(), handler, indent=2)

        self.console.print(f"Results saved to [bold green]{path.resolve()}[/bold green]")


def main() -> None:
    """Parse command-line arguments and execute the calorie counter agent."""
    parser = argparse.ArgumentParser(description="AI-powered calorie counter from food photos")
    parser.add_argument("image_path", help="Path to your food photo")
    parser.add_argument("--output", help="Save results as JSON to this path")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    try:
        agent = CalorieCounterAgent(verbose=args.verbose)
        analysis = agent.run(args.image_path)
        agent.display_results(analysis)

        if args.output:
            agent.save_results(analysis, args.output)
    except CalorieCounterError as exc:
        Console().print(Text(str(exc), style="bold red"))
        raise SystemExit(1)
    except ValueError as exc:
        Console().print(Text(str(exc), style="bold red"))
        raise SystemExit(1)
    except KeyboardInterrupt:
        Console().print(Text("Cancelled by user", style="bold yellow"))
        raise SystemExit(0)


if __name__ == "__main__":
    main()
