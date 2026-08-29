"""
Unit Tests for BusinessNameNormalizer
=====================================
Validates conservative business name normalization, noise stripping, and casing rules.
"""

import pytest
from worker.normalizers.business_name_normalizer import BusinessNameNormalizer, NormalizedBusinessName


class TestBusinessNameNormalizer:
    """Test suite covering required and real-world business name normalization patterns."""

    def test_all_caps_with_punctuation_spacing(self):
        """
        Input: 'THE SMILE MAKERS,DENTAL AND IMPLANT CENTRE'
        Expected: 'The Smile Makers, Dental and Implant Centre'
        """
        result = BusinessNameNormalizer.normalize("THE SMILE MAKERS,DENTAL AND IMPLANT CENTRE")
        assert result.display_name == "The Smile Makers, Dental and Implant Centre"
        assert result.raw_name == "THE SMILE MAKERS,DENTAL AND IMPLANT CENTRE"
        assert "smile makers" in result.normalized_name

    def test_seo_and_location_delimiter_removal(self):
        """
        Input: 'Maxsmile Dental Clinic || Dental Clinic in Sodepur'
        Expected: 'Maxsmile Dental Clinic'
        """
        result = BusinessNameNormalizer.normalize("Maxsmile Dental Clinic || Dental Clinic in Sodepur")
        assert result.display_name == "Maxsmile Dental Clinic"
        assert result.raw_name == "Maxsmile Dental Clinic || Dental Clinic in Sodepur"
        assert result.normalized_name == "maxsmile dental clinic"

    def test_excessive_whitespace_collapse(self):
        """
        Input: 'Maxsmile  Dental   Clinic'
        Expected: 'Maxsmile Dental Clinic'
        """
        result = BusinessNameNormalizer.normalize("Maxsmile  Dental   Clinic")
        assert result.display_name == "Maxsmile Dental Clinic"
        assert result.raw_name == "Maxsmile  Dental   Clinic"

    def test_legitimate_descriptors_and_ampersand_preservation(self):
        """
        Input: 'Smile Dental & Implant Centre'
        Expected: 'Smile Dental & Implant Centre'
        """
        result = BusinessNameNormalizer.normalize("Smile Dental & Implant Centre")
        assert result.display_name == "Smile Dental & Implant Centre"
        assert result.raw_name == "Smile Dental & Implant Centre"
        assert result.normalized_name == "smile dental and implant centre"

    def test_ampersand_spacing_repair(self):
        """
        Input: 'Smile Dental&Implant Centre'
        Expected: 'Smile Dental & Implant Centre'
        """
        result = BusinessNameNormalizer.normalize("Smile Dental&Implant Centre")
        assert result.display_name == "Smile Dental & Implant Centre"

    def test_pipe_delimiter_with_category_repetition(self):
        """
        Input: 'Care Dental Care | Dentist in Kolkata'
        Expected: 'Care Dental Care'
        """
        result = BusinessNameNormalizer.normalize("Care Dental Care | Dentist in Kolkata")
        assert result.display_name == "Care Dental Care"

    def test_acronym_preservation(self):
        """
        Input: 'APEX ENT AND ICU HOSPITAL'
        Expected: 'Apex ENT and ICU Hospital'
        """
        result = BusinessNameNormalizer.normalize("APEX ENT AND ICU HOSPITAL")
        assert result.display_name == "Apex ENT and ICU Hospital"

    def test_dangling_punctuation_cleanup(self):
        """
        Input: ' - Dr. Roy's Dental Clinic || '
        Expected: 'Dr. Roy's Dental Clinic'
        """
        result = BusinessNameNormalizer.normalize(" - Dr. Roy's Dental Clinic || ")
        assert result.display_name == "Dr. Roy's Dental Clinic"

    def test_empty_and_none_handling(self):
        """Validates robustness against empty strings or None values."""
        assert BusinessNameNormalizer.normalize("").display_name == ""
        assert BusinessNameNormalizer.normalize(None).display_name == ""
        assert BusinessNameNormalizer.normalize("   ").display_name == ""

    def test_deduplication_of_repeated_fragment(self):
        """
        Input: 'Apex Dental Care - Apex Dental Care'
        Expected: 'Apex Dental Care'
        """
        result = BusinessNameNormalizer.normalize("Apex Dental Care - Apex Dental Care")
        assert result.display_name == "Apex Dental Care"
