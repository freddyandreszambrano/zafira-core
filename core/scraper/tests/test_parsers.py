from datetime import datetime, timezone
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from core.scraper.parsers import (
    extract_category_path,
    extract_images,
    normalize_price,
    now_iso,
)


class TestNormalizePrice(SimpleTestCase):
    """Test suite for normalize_price function."""

    def test_simple_integer(self):
        """Test conversion of simple integer string."""
        result = normalize_price('100')
        self.assertEqual(result, 100.0)

    def test_decimal_with_dot(self):
        """Test conversion of decimal number with dot separator."""
        result = normalize_price('12.99')
        self.assertEqual(result, 12.99)

    def test_decimal_with_comma(self):
        """Test conversion of decimal number with comma separator."""
        result = normalize_price('12,99')
        self.assertEqual(result, 12.99)

    def test_price_with_dollar_sign(self):
        """Test conversion of price with dollar sign."""
        result = normalize_price('$12.99')
        self.assertEqual(result, 12.99)

    def test_price_with_spaces(self):
        """Test conversion of price with spaces."""
        result = normalize_price('$ 45.50')
        self.assertEqual(result, 45.50)

    def test_non_string_input_returns_none(self):
        """Test that non-string input returns None."""
        self.assertIsNone(normalize_price(123))
        self.assertIsNone(normalize_price(None))
        self.assertIsNone(normalize_price(45.67))

    def test_invalid_string_returns_none(self):
        """Test that invalid string returns None."""
        self.assertIsNone(normalize_price('abc'))
        self.assertIsNone(normalize_price(''))


class TestExtractCategoryPath(SimpleTestCase):
    """Test suite for extract_category_path function."""

    def test_basic_breadcrumb(self):
        """Test basic breadcrumb list conversion."""
        breadcrumb = ['Hombres', 'Moda Hombre', 'Camisas']
        result = extract_category_path(breadcrumb)
        self.assertEqual(result, 'Hombres/Moda Hombre/Camisas')

    def test_single_item(self):
        """Test single item breadcrumb."""
        result = extract_category_path(['Electronics'])
        self.assertEqual(result, 'Electronics')

    def test_empty_list(self):
        """Test empty breadcrumb list."""
        result = extract_category_path([])
        self.assertEqual(result, '')

    def test_breadcrumb_with_empty_strings(self):
        """Test breadcrumb with empty strings (should be filtered)."""
        breadcrumb = ['Home', '', 'Category', None, 'Subcategory']
        result = extract_category_path(breadcrumb)
        self.assertEqual(result, 'Home/Category/Subcategory')

    def test_breadcrumb_with_whitespace(self):
        """Test breadcrumb items with whitespace are stripped."""
        breadcrumb = ['  Home  ', 'Category ', '  Subcategory  ']
        result = extract_category_path(breadcrumb)
        self.assertEqual(result, 'Home/Category/Subcategory')


class TestExtractImages(SimpleTestCase):
    """Test suite for extract_images function."""

    def test_extract_single_image_with_src(self):
        """Test extraction of single image with src attribute."""
        mock_img = Mock()
        mock_img.get.side_effect = lambda attr: 'https://example.com/image.jpg' if attr == 'src' else None

        container = Mock()
        container.find_all.return_value = [mock_img]

        result = extract_images(container)
        self.assertEqual(result, ['https://example.com/image.jpg'])

    def test_extract_image_with_data_src(self):
        """Test extraction of image with data-src attribute."""
        mock_img = Mock()
        mock_img.get.side_effect = lambda attr: 'https://example.com/lazy.jpg' if attr == 'data-src' else None

        container = Mock()
        container.find_all.return_value = [mock_img]

        result = extract_images(container)
        self.assertEqual(result, ['https://example.com/lazy.jpg'])

    def test_extract_multiple_images(self):
        """Test extraction of multiple images."""
        mock_img1 = Mock()
        mock_img1.get.side_effect = lambda attr: 'https://example.com/image1.jpg' if attr == 'src' else None

        mock_img2 = Mock()
        mock_img2.get.side_effect = lambda attr: 'https://example.com/image2.jpg' if attr == 'src' else None

        container = Mock()
        container.find_all.return_value = [mock_img1, mock_img2]

        result = extract_images(container)
        self.assertEqual(len(result), 2)
        self.assertIn('https://example.com/image1.jpg', result)
        self.assertIn('https://example.com/image2.jpg', result)

    def test_skip_data_uri(self):
        """Test that data: URIs are skipped."""
        mock_img = Mock()
        mock_img.get.side_effect = lambda attr: 'data:image/png;base64,ABC123' if attr == 'src' else None

        container = Mock()
        container.find_all.return_value = [mock_img]

        result = extract_images(container)
        self.assertEqual(result, [])

    def test_remove_duplicates(self):
        """Test that duplicate images are removed while maintaining order."""
        mock_img1 = Mock()
        mock_img1.get.side_effect = lambda attr: 'https://example.com/image.jpg' if attr == 'src' else None

        mock_img2 = Mock()
        mock_img2.get.side_effect = lambda attr: 'https://example.com/image.jpg' if attr == 'src' else None

        container = Mock()
        container.find_all.return_value = [mock_img1, mock_img2]

        result = extract_images(container)
        self.assertEqual(result, ['https://example.com/image.jpg'])

    def test_none_container_returns_empty_list(self):
        """Test that None container returns empty list."""
        result = extract_images(None)
        self.assertEqual(result, [])

    def test_mixed_src_and_data_src(self):
        """Test extraction with mix of src and data-src attributes."""
        mock_img1 = Mock()
        mock_img1.get.side_effect = lambda attr: 'https://example.com/image1.jpg' if attr == 'src' else None

        mock_img2 = Mock()
        mock_img2.get.side_effect = lambda attr: None if attr == 'src' else 'https://example.com/image2.jpg'

        container = Mock()
        container.find_all.return_value = [mock_img1, mock_img2]

        result = extract_images(container)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 'https://example.com/image1.jpg')
        self.assertEqual(result[1], 'https://example.com/image2.jpg')


class TestNowIso(SimpleTestCase):
    """Test suite for now_iso function."""

    def test_returns_string(self):
        """Test that now_iso returns a string."""
        result = now_iso()
        self.assertIsInstance(result, str)

    def test_iso_format(self):
        """Test that returned string is in ISO 8601 format."""
        result = now_iso()
        # ISO format includes T separator and timezone
        self.assertIn('T', result)
        self.assertTrue(result.endswith('+00:00'))
