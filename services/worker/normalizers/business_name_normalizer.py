"""
FastUI Business Name Normalizer
===============================
Production-grade, conservative business name normalization component.

Design Principles:
- Conservative: Cleans formatting and obvious SEO/location noise without stripping
  legitimate business descriptors (e.g., 'Dental Clinic', 'Medical Group').
- Deterministic: Immutable result object with raw, display, and search-normalized forms.
- Brand Preservation: Protects intentional casing, abbreviations, and doctor prefixes.
"""

import re
from dataclasses import dataclass
from typing import Optional, Set


@dataclass(frozen=True)
class NormalizedBusinessName:
    """
    Immutable value object encapsulating raw, display, and search-normalized name representations.
    """

    raw_name: str
    display_name: str
    normalized_name: str

    def __str__(self) -> str:
        return self.display_name


class BusinessNameNormalizer:
    """
    Conservative normalizer for business names discovered through web scraping.
    """

    # Minor words kept in lowercase in title casing (unless at beginning of phrase)
    MINOR_WORDS: Set[str] = {
        "a", "an", "and", "as", "at", "but", "by", "for", "in", "nor", "of",
        "on", "or", "so", "the", "to", "up", "yet", "with", "via"
    }

    # Known brand acronyms and title prefixes preserved in uppercase/specific casing
    PRESERVED_ACRONYMS: Set[str] = {
        "USA", "UK", "UAE", "IBM", "BMW", "LLC", "INC", "LTD", "PVT", "CORP",
        "MD", "DDS", "DMD", "BDS", "MDS", "ENT", "IVF", "MRI", "CT", "ICU", "3M"
    }

    # Common delimiter patterns used in SEO-stuffed title strings
    MAJOR_SEPARATORS = re.compile(r"\s*(?:\|\||\||//|--|—|–|•|·)\s*")

    # SEO descriptive suffix patterns
    SEO_SUFFIX_PATTERN = re.compile(
        r"^(?:best|top|famous|leading|trusted)?\s*(?:dentist|dental clinic|doctor|clinic|hospital|lawyer|plumber|bakery|restaurant|services|shop|store)\s+in\s+[\w\s,]+$",
        re.IGNORECASE
    )

    @classmethod
    def normalize(cls, raw_name: Optional[str]) -> NormalizedBusinessName:
        """
        Main entry point. Takes a raw business name string and returns a NormalizedBusinessName.
        """
        if not raw_name or not isinstance(raw_name, str):
            return NormalizedBusinessName(
                raw_name="" if raw_name is None else str(raw_name),
                display_name="",
                normalized_name=""
            )

        original_raw = raw_name
        text = raw_name.strip()

        if not text:
            return NormalizedBusinessName(raw_name=original_raw, display_name="", normalized_name="")

        text = cls._collapse_whitespace(text)
        text = cls._fix_punctuation_spacing(text)
        text = cls._clean_delimiters_and_seo_suffixes(text)
        text = cls._deduplicate_repeated_fragments(text)
        display_name = cls._apply_smart_casing(text)
        display_name = cls._clean_surrounding_punctuation(display_name)
        normalized_name = cls._generate_search_key(display_name)

        return NormalizedBusinessName(
            raw_name=original_raw,
            display_name=display_name,
            normalized_name=normalized_name
        )

    @classmethod
    def _collapse_whitespace(cls, text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _fix_punctuation_spacing(cls, text: str) -> str:
        text = re.sub(r"([,;:])([^\s\d])", r"\1 \2", text)
        text = re.sub(r"(\w)&(\w)", r"\1 & \2", text)
        text = re.sub(r"\s*&\s*", " & ", text)
        text = re.sub(r",\s*,+", ", ", text)
        text = re.sub(r"\.\s*\.+", ".", text)
        return cls._collapse_whitespace(text)

    @classmethod
    def _clean_delimiters_and_seo_suffixes(cls, text: str) -> str:
        parts = [cls._collapse_whitespace(p) for p in cls.MAJOR_SEPARATORS.split(text) if p.strip()]

        if len(parts) <= 1:
            return text

        primary = parts[0]
        remaining = parts[1:]
        filtered_parts = [primary]

        for seg in remaining:
            if seg.lower() == primary.lower():
                continue
            if cls.SEO_SUFFIX_PATTERN.match(seg):
                continue
            if re.search(r"\b(?:in|at|near)\s+[A-Za-z]+(?:\s+[A-Za-z]+)*$", seg, re.IGNORECASE) and len(seg.split()) <= 6:
                continue
            filtered_parts.append(seg)

        if len(filtered_parts) == 1:
            return filtered_parts[0]

        return " | ".join(filtered_parts)

    @classmethod
    def _deduplicate_repeated_fragments(cls, text: str) -> str:
        pattern = re.compile(r"^(.+?)\s*(?:[-–—|:,]\s*)\1$", re.IGNORECASE)
        match = pattern.match(text)
        if match:
            return match.group(1).strip()
        return text

    @classmethod
    def _apply_smart_casing(cls, text: str) -> str:
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)

        if has_upper and has_lower:
            return cls._normalize_mixed_case_spacing(text)

        words = text.split(" ")
        cased_words = []

        for i, word in enumerate(words):
            match = re.match(r"^([^a-zA-Z0-9]*)(.*?)([^a-zA-Z0-9]*)$", word)
            if not match:
                cased_words.append(word)
                continue

            prefix, core, suffix = match.groups()
            if not core:
                cased_words.append(word)
                continue

            core_upper = core.upper()

            if core_upper in cls.PRESERVED_ACRONYMS:
                cased_core = core_upper
            elif core_upper in {"DR", "MR", "MS", "MRS", "PROF"}:
                cased_core = core_upper.capitalize()
            elif i > 0 and core.lower() in cls.MINOR_WORDS:
                cased_core = core.lower()
            else:
                cased_core = core.capitalize()

            cased_words.append(f"{prefix}{cased_core}{suffix}")

        return " ".join(cased_words)

    @classmethod
    def _normalize_mixed_case_spacing(cls, text: str) -> str:
        return cls._collapse_whitespace(text)

    @classmethod
    def _clean_surrounding_punctuation(cls, text: str) -> str:
        text = re.sub(r"^[\s,;:\-–—|/]+", "", text)
        text = re.sub(r"[\s,;:\-–—|/]+$", "", text)
        return text.strip()

    @classmethod
    def _generate_search_key(cls, display_name: str) -> str:
        text = display_name.lower().replace("&", " and ")
        text = re.sub(r"[^\w\s]", " ", text)
        return cls._collapse_whitespace(text)
