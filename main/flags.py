"""Maps a team's FIFA abbreviation to a flag code understood by flagcdn.com
(ISO 3166-1 alpha-2, plus gb-eng/gb-sct/gb-wls/gb-nir for the home nations).

Used to show a small country flag next to team names. Placeholder teams (e.g.
group-winner slots) simply have no entry and render without a flag."""

# FIFA three-letter code -> flagcdn region code.
ABBR_TO_CODE = {
    # WorldCup 2026 pool
    "ALG": "dz", "ARG": "ar", "AUS": "au", "AUT": "at", "BEL": "be",
    "BIH": "ba", "BRA": "br", "CAN": "ca", "CPV": "cv", "COL": "co",
    "CRO": "hr", "CUW": "cw", "CZE": "cz", "COD": "cd", "ECU": "ec",
    "EGY": "eg", "ENG": "gb-eng", "FRA": "fr", "GER": "de", "GHA": "gh",
    "HAI": "ht", "IRN": "ir", "IRQ": "iq", "CIV": "ci", "JPN": "jp",
    "JOR": "jo", "MEX": "mx", "MAR": "ma", "NED": "nl", "NZL": "nz",
    "NOR": "no", "PAN": "pa", "PAR": "py", "POR": "pt", "QAT": "qa",
    "KSA": "sa", "SCO": "gb-sct", "SEN": "sn", "RSA": "za", "KOR": "kr",
    "ESP": "es", "SWE": "se", "SUI": "ch", "TUN": "tn", "TUR": "tr",
    "USA": "us", "URU": "uy", "UZB": "uz",
    # Other nations that may appear (past tournaments / qualifiers)
    "RUS": "ru", "NGA": "ng", "POL": "pl", "DEN": "dk", "PER": "pe",
    "CRC": "cr", "SRB": "rs", "ISL": "is", "SVK": "sk", "GRE": "gr",
    "WAL": "gb-wls", "NIR": "gb-nir", "IRL": "ie", "UKR": "ua", "ROU": "ro",
    "HUN": "hu", "CHN": "cn", "IND": "in", "THA": "th", "VIE": "vn",
    "CHI": "cl", "VEN": "ve", "BOL": "bo", "CMR": "cm", "ANG": "ao",
    "MLI": "ml", "BFA": "bf", "GUI": "gn", "GAB": "ga", "CGO": "cg",
    "ZAM": "zm", "ZIM": "zw", "KEN": "ke", "UGA": "ug", "BHR": "bh",
    "KUW": "kw", "OMA": "om", "UAE": "ae", "SYR": "sy", "LBN": "lb",
    "PLE": "ps", "PRK": "kp", "MAS": "my", "IDN": "id", "PHI": "ph",
    "SGP": "sg", "HKG": "hk", "TPE": "tw", "ISR": "il", "GEO": "ge",
    "ARM": "am", "AZE": "az", "KAZ": "kz", "MNE": "me", "MKD": "mk",
    "ALB": "al", "SVN": "si", "BLR": "by", "MDA": "md", "LVA": "lv",
    "LTU": "lt", "EST": "ee", "FIN": "fi", "LUX": "lu", "CYP": "cy",
    "MLT": "mt", "FRO": "fo", "HON": "hn", "GUA": "gt", "SLV": "sv",
    "NCA": "ni", "JAM": "jm", "TRI": "tt", "CUB": "cu", "DOM": "do",
    "BUL": "bg",
}


def code_for(abbreviation):
    """Returns a flagcdn region code for a FIFA abbreviation, or None."""
    if not abbreviation:
        return None
    return ABBR_TO_CODE.get(abbreviation.strip().upper())
