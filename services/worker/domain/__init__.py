from domain.identity import (
    GENERIC_DOMAINS,
    are_addresses_matching,
    are_coordinates_matching,
    extract_postal_code,
    is_duplicate_candidate,
    same_business,
)
from domain.normalization import (
    NormalizedBusinessName,
    normalize_address,
    normalize_business_name,
    normalize_website,
    resolve_canonical_name,
)

__all__ = [
    "GENERIC_DOMAINS",
    "are_addresses_matching",
    "are_coordinates_matching",
    "extract_postal_code",
    "is_duplicate_candidate",
    "same_business",
    "NormalizedBusinessName",
    "normalize_business_name",
    "resolve_canonical_name",
    "normalize_address",
    "normalize_website",
]
