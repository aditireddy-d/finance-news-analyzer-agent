"""
Ticker-to-sector map for filtering and theme analysis. Hand-maintained,
covers the tickers in tickers_universe.py. Same honesty note as that
module: this is a reasonable approximation, not an official GICS
classification feed.
"""

SECTOR_MAP = {
    # Technology
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Technology", "GOOG": "Technology",
    "META": "Technology", "ORCL": "Technology", "CRM": "Technology", "ADBE": "Technology",
    "IBM": "Technology", "NOW": "Technology", "INTU": "Technology", "WDAY": "Technology",
    "TEAM": "Technology", "SNPS": "Technology", "CDNS": "Technology", "ANSS": "Technology",
    "CSGP": "Technology", "PLTR": "Technology", "SNOW": "Technology", "DDOG": "Technology",
    "ZS": "Technology", "CRWD": "Technology", "PANW": "Technology", "FTNT": "Technology",

    # Semiconductors
    "NVDA": "Semiconductors", "AVGO": "Semiconductors", "AMD": "Semiconductors",
    "INTC": "Semiconductors", "QCOM": "Semiconductors", "TXN": "Semiconductors",
    "MU": "Semiconductors", "ADI": "Semiconductors", "LRCX": "Semiconductors",
    "KLAC": "Semiconductors", "NXPI": "Semiconductors", "MRVL": "Semiconductors",
    "AMAT": "Semiconductors", "SMCI": "Semiconductors",

    # Consumer & Retail
    "AMZN": "Consumer & Retail", "TSLA": "Consumer & Retail", "COST": "Consumer & Retail",
    "WMT": "Consumer & Retail", "HD": "Consumer & Retail", "LOW": "Consumer & Retail",
    "MCD": "Consumer & Retail", "SBUX": "Consumer & Retail", "BKNG": "Consumer & Retail",
    "ABNB": "Consumer & Retail", "MAR": "Consumer & Retail", "ORLY": "Consumer & Retail",
    "MELI": "Consumer & Retail", "PEP": "Consumer & Retail", "KO": "Consumer & Retail",
    "MDLZ": "Consumer & Retail", "MNST": "Consumer & Retail", "KDP": "Consumer & Retail",
    "SHOP": "Consumer & Retail", "DASH": "Consumer & Retail", "ROKU": "Consumer & Retail",

    # Financials & Banking
    "JPM": "Financials & Banking", "V": "Financials & Banking", "MA": "Financials & Banking",
    "BAC": "Financials & Banking", "WFC": "Financials & Banking", "GS": "Financials & Banking",
    "MS": "Financials & Banking", "C": "Financials & Banking", "SCHW": "Financials & Banking",
    "AXP": "Financials & Banking", "BLK": "Financials & Banking", "SPGI": "Financials & Banking",
    "FI": "Financials & Banking", "MMC": "Financials & Banking", "CB": "Financials & Banking",
    "COIN": "Financials & Banking", "PYPL": "Financials & Banking", "SQ": "Financials & Banking",

    # Healthcare
    "UNH": "Healthcare", "JNJ": "Healthcare", "MRK": "Healthcare", "ABBV": "Healthcare",
    "PFE": "Healthcare", "TMO": "Healthcare", "ABT": "Healthcare", "DHR": "Healthcare",
    "AMGN": "Healthcare", "GILD": "Healthcare", "VRTX": "Healthcare", "REGN": "Healthcare",
    "ISRG": "Healthcare", "BIIB": "Healthcare", "IDXX": "Healthcare", "DXCM": "Healthcare",
    "ZTS": "Healthcare", "SYK": "Healthcare", "MDT": "Healthcare", "BSX": "Healthcare",
    "CI": "Healthcare", "ELV": "Healthcare",

    # Energy & Oil
    "XOM": "Energy & Oil", "CVX": "Energy & Oil",

    # Industrials
    "HON": "Industrials", "CAT": "Industrials", "GE": "Industrials", "BA": "Industrials",
    "RTX": "Industrials", "DE": "Industrials", "LMT": "Industrials", "UPS": "Industrials",
    "CTAS": "Industrials", "ADP": "Industrials", "PAYX": "Industrials", "FAST": "Industrials",
    "ODFL": "Industrials", "PCAR": "Industrials", "ROP": "Industrials", "CPRT": "Industrials",
    "VRSK": "Industrials", "CSCO": "Industrials",

    # Telecom & Media
    "TMUS": "Telecom & Media", "CMCSA": "Telecom & Media", "CHTR": "Telecom & Media",
    "T": "Telecom & Media", "NFLX": "Telecom & Media", "EA": "Telecom & Media",
    "CTSH": "Telecom & Media",

    # Utilities
    "AEP": "Utilities", "EXC": "Utilities", "XEL": "Utilities", "NEE": "Utilities",
    "SO": "Utilities", "DUK": "Utilities",

    # Other / Uber-style platforms
    "UBER": "Consumer & Retail", "LIN": "Industrials", "PG": "Consumer & Retail",
    "PM": "Consumer & Retail", "BRK.B": "Financials & Banking", "ACN": "Technology",
    "PLD": "Industrials",
}


def sector_for(ticker: str) -> str:
    return SECTOR_MAP.get(ticker.upper(), "Other")


def tickers_in_sector(sector: str) -> list[str]:
    return [t for t, s in SECTOR_MAP.items() if s == sector]


def all_sectors() -> list[str]:
    return sorted(set(SECTOR_MAP.values()))
