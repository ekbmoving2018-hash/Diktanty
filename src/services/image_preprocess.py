"""Предобработка изображения рукописного текста перед OCR."""

import logging
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter

from src.utils.exceptions import DictationProcessingError

logger = logging.getLogger(__name__)

# Маркер неразборчивого фрагмента (должен совпадать с промптом OCR)
UNREADABLE_MARKER = "[[неразборчиво]]"


def preprocess_handwritten_image(image_bytes: bytes) -> bytes:
    """
    Предобработка фото рукописного диктанта для улучшения качества OCR:
    масштаб 2x, grayscale, контраст, резкость. Возвращает PNG в bytes.
    """
    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception as e:
        logger.warning("Failed to open image for preprocess: %s", e)
        raise DictationProcessingError("Не удалось обработать изображение. Отправьте фото в формате JPG или PNG.") from e
    with img:
        img = img.convert("RGB")

        # Увеличить в 2 раза
        w, h = img.size
        img = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)

        # Grayscale
        img = img.convert("L")

        # Повысить контраст
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)

        # Повысить резкость
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))

        out = BytesIO()
        img.save(out, format="PNG", optimize=True)
        return out.getvalue()
