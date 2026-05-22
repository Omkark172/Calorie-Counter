import logging
import os
from pathlib import Path
from typing import Dict, Tuple

from PIL import Image

try:
    from src.models import ImageLoadError, ImageValidationError
except ImportError:
    from models import ImageLoadError, ImageValidationError


class ImageProcessor:
    """Handles image validation, loading, inspection, and resizing."""

    def __init__(self, max_size_mb: float = 10.0, supported_formats: list = None) -> None:
        """Initialize the image processor with size and format settings."""
        self.max_size_mb = max_size_mb
        self.supported_formats = supported_formats or ["jpg", "jpeg", "png", "webp", "gif"]
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialized ImageProcessor with max_size_mb=%s supported_formats=%s", self.max_size_mb, self.supported_formats)

    def validate_image(self, image_path: str) -> Tuple[bool, str]:
        """Validate an image file path and return a tuple describing validity."""
        self.logger.debug("Validating image path: %s", image_path)
        path = Path(image_path)

        if not path.exists():
            message = f"File not found: {image_path}"
            self.logger.warning(message)
            return False, message

        if not path.is_file():
            message = f"Path is not a file: {image_path}"
            self.logger.warning(message)
            return False, message

        extension = path.suffix.lower().lstrip('.')
        self.logger.debug("Detected file extension: %s", extension)
        if extension not in [fmt.lower() for fmt in self.supported_formats]:
            message = f"Unsupported format: {extension}. Supported formats: {', '.join(self.supported_formats)}"
            self.logger.warning(message)
            return False, message

        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        self.logger.debug("File size: %.2f MB", file_size_mb)
        if file_size_mb > self.max_size_mb:
            message = f"File too large: {file_size_mb:.2f} MB. Maximum allowed size is {self.max_size_mb:.2f} MB"
            self.logger.warning(message)
            return False, message

        self.logger.info("Image validation succeeded for %s", image_path)
        return True, ""

    def load_and_encode(self, image_path: str) -> Tuple[Image.Image, bytes]:
        """Load an image from disk and return the PIL image object and raw bytes."""
        self.logger.debug("Loading and encoding image: %s", image_path)
        is_valid, message = self.validate_image(image_path)
        if not is_valid:
            self.logger.error("Image validation failed: %s", message)
            raise ImageValidationError(message)

        try:
            pil_image = Image.open(image_path)
            self.logger.debug("Opened image with mode %s and format %s", pil_image.mode, pil_image.format)

            if pil_image.mode != "RGB":
                self.logger.debug("Converting image mode from %s to RGB", pil_image.mode)
                pil_image = pil_image.convert("RGB")

            raw_bytes = Path(image_path).read_bytes()
            self.logger.info("Successfully loaded image and read raw bytes for %s", image_path)
            return pil_image, raw_bytes
        except Exception as exc:
            message = f"Failed to load image '{image_path}': {exc}"
            self.logger.exception(message)
            raise ImageLoadError(message)

    def get_image_info(self, image_path: str) -> Dict[str, object]:
        """Return metadata about the image at the provided path."""
        self.logger.debug("Collecting image info for: %s", image_path)
        path = Path(image_path)

        if not path.exists() or not path.is_file():
            message = f"File not found or invalid path: {image_path}"
            self.logger.error(message)
            raise ImageValidationError(message)

        try:
            with Image.open(path) as image:
                file_size_mb = round(path.stat().st_size / (1024 * 1024), 2)
                info = {
                    "filename": path.name,
                    "size_mb": file_size_mb,
                    "width": image.width,
                    "height": image.height,
                    "format": image.format,
                    "mode": image.mode,
                }
                self.logger.info("Image info collected for %s: %s", image_path, info)
                return info
        except Exception as exc:
            message = f"Failed to inspect image '{image_path}': {exc}"
            self.logger.exception(message)
            raise ImageLoadError(message)

    def resize_if_needed(self, image: Image.Image, max_dimension: int = 1024) -> Image.Image:
        """Resize an image if its dimensions exceed the maximum allowed dimension."""
        self.logger.debug("Checking resize need for image size %sx%s", image.width, image.height)
        if image.width <= max_dimension and image.height <= max_dimension:
            self.logger.debug("No resize needed for image")
            return image

        scale = min(max_dimension / image.width, max_dimension / image.height)
        new_width = int(image.width * scale)
        new_height = int(image.height * scale)
        self.logger.info("Resizing image from %sx%s to %sx%s", image.width, image.height, new_width, new_height)

        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        return resized_image
