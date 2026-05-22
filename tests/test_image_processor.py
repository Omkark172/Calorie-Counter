import os
from pathlib import Path

import pytest
from PIL import Image

from src import ImageProcessor, ImageValidationError


def test_validate_image_nonexistent_path():
    processor = ImageProcessor()
    valid, message = processor.validate_image("missing_file.jpg")
    assert not valid
    assert "not found" in message.lower()


def test_validate_image_unsupported_format(tmp_path: Path):
    path = tmp_path / "image.bmp"
    Image.new("RGB", (10, 10), "blue").save(path)
    processor = ImageProcessor()
    valid, message = processor.validate_image(str(path))
    assert not valid
    assert "unsupported" in message.lower()


def test_validate_image_valid_png(sample_image_path: str):
    processor = ImageProcessor()
    valid, message = processor.validate_image(sample_image_path)
    assert valid
    assert message == ""


def test_get_image_info(sample_image_path: str):
    processor = ImageProcessor()
    info = processor.get_image_info(sample_image_path)
    assert set(info.keys()) == {"filename", "size_mb", "width", "height", "format", "mode"}
    assert info["filename"].endswith("test_food.png")
    assert info["format"] == "PNG"
    assert info["mode"] == "RGB"


def test_load_and_encode_valid_image(sample_image_path: str):
    processor = ImageProcessor()
    image, raw_bytes = processor.load_and_encode(sample_image_path)
    assert image is not None
    assert isinstance(raw_bytes, (bytes, bytearray))


def test_load_and_encode_invalid_path_raises():
    processor = ImageProcessor()
    with pytest.raises(ImageValidationError):
        processor.load_and_encode("missing_file.png")


def test_resize_if_needed_resizes_large_image():
    processor = ImageProcessor()
    large_image = Image.new("RGB", (2000, 1500), "white")
    resized = processor.resize_if_needed(large_image, max_dimension=1024)
    assert max(resized.width, resized.height) == 1024


def test_resize_if_needed_no_resize_small_image():
    processor = ImageProcessor()
    small_image = Image.new("RGB", (500, 400), "white")
    result = processor.resize_if_needed(small_image, max_dimension=1024)
    assert result.width == 500
    assert result.height == 400
