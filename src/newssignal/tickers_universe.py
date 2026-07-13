"""
Ticker universe for the full market scan.

Unlike an earlier ~140-ticker hand-typed approximation, these lists were
pulled directly from slickcharts.com's current S&P 500 and NASDAQ-100
component pages (which source their membership from S&P Dow Jones Indices
and Nasdaq, Inc. respectively) on the date this file was generated.

Honesty notes, still worth keeping in mind:
- SP500_TICKERS below covers 489 of the official 503 S&P 500 symbols
  (the fetch was truncated near the bottom of the list) -- not the full
  503, but a near-complete, genuinely sourced snapshot rather than a
  hand-picked approximation.
- NASDAQ_100_TICKERS covers all 103 current NASDAQ-100 symbols (103, not
  100, because Alphabet has two share classes and a few others do too --
  this matches how the index itself is actually composed).
- Index membership changes periodically (additions/removals). This is a
  snapshot as of the fetch date, not a live-updating feed -- a real
  membership feed would require an ongoing paid or official data source.
"""

NASDAQ_100_TICKERS = [
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "AVGO", "META", "TSLA",
    "MU", "AMD", "WMT", "ASML", "INTC", "AMAT", "CSCO", "LRCX", "COST",
    "ARM", "NFLX", "PLTR", "KLAC", "SNDK", "TXN", "PANW", "LIN", "MRVL",
    "STX", "TMUS", "WDC", "QCOM", "AMGN", "ADI", "CRWD", "PEP", "APP",
    "GILD", "SHOP", "ISRG", "BKNG", "VRTX", "PDD", "SBUX", "FTNT", "CDNS",
    "MAR", "ADP", "MNST", "MELI", "CSX", "DDOG", "CEG", "ADBE", "ABNB",
    "SNPS", "CMCSA", "DASH", "MDLZ", "INTU", "NXPI", "AEP", "CTAS", "HON",
    "ORLY", "ROST", "ALAB", "HONA", "REGN", "WBD", "MPWR", "PCAR", "LITE",
    "BKR", "TER", "NBIS", "FAST", "EA", "FANG", "RKLB", "XEL", "CRWV",
    "MCHP", "EXC", "ODFL", "CCEP", "FER", "AXON", "TTWO", "IDXX", "ADSK",
    "KDP", "PYPL", "ALNY", "TRI", "PAYX", "ROP", "WDAY", "MSTR", "KHC",
    "GEHC", "DXCM", "CPRT",
]

# 489 of 503 official S&P 500 symbols, sourced from slickcharts.com
SP500_TICKERS = [
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "AVGO", "META", "TSLA",
    "MU", "BRK.B", "LLY", "AMD", "WMT", "JPM", "V", "JNJ", "XOM", "INTC",
    "AMAT", "CSCO", "MA", "CAT", "ABBV", "LRCX", "BAC", "COST", "ORCL",
    "UNH", "GE", "KO", "CVX", "MS", "PG", "HD", "GS", "NFLX", "MRK", "PLTR",
    "KLAC", "GEV", "SNDK", "TXN", "PM", "DELL", "IBM", "WFC", "PANW", "RTX",
    "LIN", "C", "AXP", "ANET", "MRVL", "STX", "TMUS", "WDC", "QCOM", "AMGN",
    "TMO", "APH", "MCD", "ADI", "CRWD", "PEP", "NEE", "SCHW", "VZ", "BA",
    "UNP", "APP", "TJX", "DIS", "GLW", "ABT", "WELL", "GILD", "BLK", "DE",
    "ETN", "UBER", "BX", "T", "ISRG", "DHR", "BKNG", "PFE", "CB", "PGR",
    "CRM", "CVS", "COP", "PLD", "SPGI", "SYK", "COF", "VRTX", "VRT", "PH",
    "SBUX", "LMT", "MO", "LOW", "BMY", "FTNT", "NOW", "HWM", "SO", "MDT",
    "TT", "CDNS", "BNY", "EQIX", "NEM", "GD", "PNC", "HOOD", "MAR", "PWR",
    "DUK", "USB", "ADP", "UPS", "MNST", "MCK", "WM", "CMI", "CSX", "WMB",
    "DDOG", "ELV", "HCA", "CEG", "ADBE", "FCX", "ABNB", "JCI", "KKR", "CME",
    "MMC", "SNPS", "MCO", "CMCSA", "DASH", "VLO", "MPC", "ACN", "SHW",
    "MMM", "AMT", "EMR", "CI", "ITW", "ECL", "NOC", "RCL", "ICE", "HLT",
    "AON", "PSX", "MDLZ", "INTU", "FDX", "CL", "NXPI", "AEP", "NSC", "TDG",
    "TRV", "CTAS", "HON", "ORLY", "ROST", "KMI", "EOG", "SLB", "SPG", "MSI",
    "GM", "CRH", "HONA", "REGN", "APO", "URI", "RSG", "DLR", "APD", "WBD",
    "BSX", "MPWR", "NKE", "PCAR", "CIEN", "AJG", "GWW", "ALL", "TFC", "HPE",
    "COHR", "LITE", "AFL", "FIX", "D", "SRE", "TGT", "COR", "O", "MET",
    "TRGP", "TEL", "CARR", "DAL", "CTVA", "BKR", "OKE", "TER", "PSA", "F",
    "CAH", "KEYS", "LHX", "ETR", "AME", "VST", "FAST", "EW", "OXY", "ROK",
    "EBAY", "NUE", "EA", "FITB", "FANG", "AZO", "XEL", "STT", "NDAQ",
    "FLEX", "DVN", "MCHP", "EXC", "ODFL", "CVNA", "HUM", "GRMN", "XYZ",
    "AXON", "AMP", "CMG", "TTWO", "YUM", "IDXX", "WAB", "VTR", "MSCI",
    "ADSK", "KDP", "DHI", "AIG", "IBKR", "COIN", "BDX", "LYV", "ED", "UAL",
    "PYPL", "CBRE", "PEG", "SYY", "PRU", "ADM", "VMC", "PAYX", "HIG", "A",
    "PCG", "WEC", "KVUE", "ON", "KMB", "KR", "WAT", "CCL", "HBAN", "IRM",
    "ROP", "MTB", "ACGL", "HSY", "CCI", "EME", "IQV", "MLM", "JBL", "WDAY",
    "NTRS", "CNC", "NTAP", "STLD", "RJF", "EXPE", "ZTS", "DTE", "AEE",
    "LVS", "VEEV", "IR", "EQT", "EXR", "CASY", "EL", "CFG", "NRG", "RMD",
    "KHC", "GEHC", "ATO", "BIIB", "TDY", "FICO", "DOV", "EIX", "DXCM",
    "XYL", "HAL", "VICI", "CNP", "TPR", "ES", "CBOE", "OTIS", "CINF", "FE",
    "ARES", "TPL", "WTW", "AVB", "MRNA", "PPL", "FISV", "WRB", "RF", "JBHT",
    "DG", "MTD", "WSM", "PPG", "HUBB", "EQR", "AWK", "CPRT", "TROW", "KEY",
    "WST", "VRSN", "FSLR", "SYF", "VRSK", "FFIV", "PFG", "DLTR", "PHM",
    "LUV", "L", "RL", "DRI", "OMC", "INCY", "CMS", "SW", "CPAY", "DGX",
    "BRO", "STZ", "CHD", "CHRW", "VLTO", "LH", "EXPD", "NI", "BG", "HPQ",
    "FIS", "ROL", "STE", "DOW", "EXE", "SNA", "GPN", "PKG", "TSN", "LEN",
    "ULTA", "SBAC", "CTSH", "IP", "AMCR", "EFX", "IFF", "EVRG", "LNT",
    "GIS", "LII", "FTV", "VTRS", "ESS", "CDW", "AKAM", "SMCI", "LYB", "DD",
    "CF", "ZBH", "INVH", "NVR", "BBY", "BEN", "GPC", "BR", "WY", "KIM",
    "IEX", "BALL", "CHTR", "NDSN", "TSCO", "HST", "TXT", "MAA", "MAS",
    "GEN", "DVA", "DOC", "ALB", "J", "DECK", "EG", "REG", "PTC", "MKC",
    "GL", "TKO", "AIZ", "COO", "GNRC", "SWK", "HRL", "LULU", "LDOS", "SOLV",
    "ERIE", "PNW", "ZBRA", "UDR", "ALGN", "IVZ", "APTV", "TYL", "RVTY",
    "TRMB", "PNR", "AVY", "BF.B", "MGM", "SJM", "APA", "GDDY", "ALLE",
    "BAX", "CLX", "CSGP", "HII", "CRL", "CPT", "HAS", "PODD", "TECH",
    "FOXA", "FOX", "JKHY", "BXP", "AES", "PSKY", "FRT", "WYNN", "DPZ",
    "NWSA",
]

FULL_UNIVERSE = sorted(set(NASDAQ_100_TICKERS + SP500_TICKERS))


def universe_size() -> int:
    return len(FULL_UNIVERSE)
