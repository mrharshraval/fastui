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

    # SEO descriptive suffix patterns, e.g. "Dental Clinic in Sodepur", "Best Plumber in Mumbai"
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

        # 1. Normalize unicode characters and basic whitespace
        text = cls._collapse_whitespace(text)

        # 2. Fix punctuation spacing (e.g. "MAKERS,DENTAL" -> "MAKERS, DENTAL", "Dental&Implant" -> "Dental & Implant")
        text = cls._fix_punctuation_spacing(text)

        # 3. Strip obvious SEO and location noise from multi-part delimiter titles
        text = cls._clean_delimiters_and_seo_suffixes(text)

        # 4. Deduplicate repeated name fragments
        text = cls._deduplicate_repeated_fragments(text)

        # 5. Apply smart title-casing (conservative: only when all-caps or all-lowercase)
        display_name = cls._apply_smart_casing(text)

        # 6. Final trim of trailing/leading separators
        display_name = cls._clean_surrounding_punctuation(display_name)

        # 7. Generate canonical normalized search string
        normalized_name = cls._generate_search_key(display_name)

        return NormalizedBusinessName(
            raw_name=original_raw,
            display_name=display_name,
            normalized_name=normalized_name
        )

    @classmethod
    def _collapse_whitespace(cls, text: str) -> str:
        """Replaces consecutive whitespace, tabs, and newlines with a single space."""
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _fix_punctuation_spacing(cls, text: str) -> str:
        """
        Ensures standard spacing around commas, colons, ampersands, and slashes.
        Example: 'THE SMILE MAKERS,DENTAL' -> 'THE SMILE MAKERS, DENTAL'
        """
        # Ensure space after comma, colon, semicolon if directly followed by word character
        text = re.sub(r"([,;:])([^\s\d])", r"\1 \2", text)

        # Ensure balanced spacing around standalone ampersands
        text = re.sub(r"(\w)&(\w)", r"\1 & \2", text)
        text = re.sub(r"\s*&\s*", " & ", text)

        # Clean duplicate punctuation (e.g., '..' -> '.', ',,' -> ',')
        text = re.sub(r",\s*,+", ", ", text)
        text = re.sub(r"\.\s*\.+", ".", text)

        return cls._collapse_whitespace(text)

    @classmethod
    def _clean_delimiters_and_seo_suffixes(cls, text: str) -> str:
        """
        Inspects multi-segment titles separated by ||, |, //, etc.
        Removes obvious SEO promo segments while preserving legitimate sub-brands.
        """
        parts = [cls._collapse_whitespace(p) for p in cls.MAJOR_SEPARATORS.split(text) if p.strip()]

        if len(parts) <= 1:
            return text

        primary = parts[0]
        remaining = parts[1:]

        filtered_parts = [primary]

        for seg in remaining:
            # Check if segment is redundant repetition of primary or an SEO location pattern
            if seg.lower() == primary.lower():
                continue
            if cls.SEO_SUFFIX_PATTERN.match(seg):
                continue
            # If segment is just repeating the category + location, skip it
            if re.search(r"\b(?:in|at|near)\s+[A-Za-z]+(?:\s+[A-Za-z]+)*$", seg, re.IGNORECASE) and len(seg.split()) <= 6:
                continue

            filtered_parts.append(seg)

        # If all secondary parts were SEO noise, return the clean primary part
        if len(filtered_parts) == 1:
            return filtered_parts[0]

        return " | ".join(filtered_parts)

    @classmethod
    def _deduplicate_repeated_fragments(cls, text: str) -> str:
        """
        Removes immediate consecutive duplicate phrases (e.g. 'Clinic Name - Clinic Name').
        """
        # Remove patterns like "Foo Bar - Foo Bar" or "Foo Bar, Foo Bar"
        pattern = re.compile(r"^(.+?)\s*(?:[-–—|:,]\s*)\1$", re.IGNORECASE)
        match = pattern.match(text)
        if match:
            return match.group(1).strip()
        return text

    @classmethod
    def _apply_smart_casing(cls, text: str) -> str:
        """
        Applies smart, grammar-aware title casing.
        - If ALL-CAPS or all-lowercase: applies proper title casing with minor-word preservation.
        - If mixed-case: preserves original author/brand casing.
        """
        # If already mixed-cased (contains both upper and lower), preserve intentional brand casing
        has_upper = any(c.isupper() for c in text)
        has_lower = any(c.islower() for c in text)

        if has_upper and has_lower:
            # Fix minor capitalization issues around punctuation (e.g., after comma or &)
            return cls._normalize_mixed_case_spacing(text)

        # Split into words and tokens, preserving punctuation
        words = text.split(" ")
        cased_words = []

        for i, word in enumerate(words):
            # Split off leading/trailing punctuation for casing analysis
            match = re.match(r"^([^a-zA-Z0-9]*)(.*?)([^a-zA-Z0-9]*)$", word)
            if not match:
                cased_words.append(word)
                continue

            prefix, core, suffix = match.groups()

            if not core:
                cased_words.append(word)
                continue

            core_upper = core.upper()

            # Preserve known medical / legal / technical acronyms
            if core_upper in cls.PRESERVED_ACRONYMS:
                cased_core = core_upper
            # Check for Dr. / Mr. / Ms.
            elif core_upper in {"DR", "MR", "MS", "MRS", "PROF"}:
                cased_core = core_upper.capitalize()
            # Minor words in lowercase unless first word
            elif i > 0 and core.lower() in cls.MINOR_WORDS:
                cased_core = core.lower()
            else:
                cased_core = core.capitalize()

            cased_words.append(f"{prefix}{cased_core}{suffix}")

        return " ".join(cased_words)

    @classmethod
    def _normalize_mixed_case_spacing(cls, text: str) -> str:
        """Cleans spacing around punctuation for mixed-case text without altering brand letters."""
        return cls._collapse_whitespace(text)

    @classmethod
    def _clean_surrounding_punctuation(cls, text: str) -> str:
        """Strips dangling hyphens, commas, pipes, or colons from start and end."""
        text = re.sub(r"^[\s,;:\-–—|/]+", "", text)
        text = re.sub(r"[\s,;:\-–—|/]+$", "", text)
        return text.strip()

    @classmethod
    def _generate_search_key(cls, display_name: str) -> str:
        """
        Generates a simplified, lowercase string for indexing and search matching.
        """
        # Replace & with and
        text = display_name.lower().replace("&", " and ")
        # Remove all punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        # Collapse whitespace
        return cls._collapse_whitespace(text)
