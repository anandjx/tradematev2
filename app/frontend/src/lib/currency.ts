/**
 * Currency symbol utility — infers currency from ticker suffix.
 * Used by TechnicalAnalysisCard, OracleForecastCard, and PriceTimeseriesCard.
 * Completely isolated — no agent, no state, no LLM.
 *
 * Covers top 25+ global exchanges (Yahoo Finance suffixes).
 */

// ── Currency Code → Display Symbol ──────────────────────────────────
const SYMBOL_MAP: Record<string, string> = {
    USD: "$", INR: "₹", GBP: "£", EUR: "€", JPY: "¥",
    CNY: "¥", KRW: "₩", HKD: "HK$", SGD: "S$", AUD: "A$",
    CAD: "C$", CHF: "CHF ", TWD: "NT$", ZAR: "R", SAR: "SR ",
    SEK: "kr ", NOK: "kr ", DKK: "kr ", BRL: "R$", MXN: "MX$",
    IDR: "Rp ", MYR: "RM ", THB: "฿", ILS: "₪", TRY: "₺",
    PLN: "zł ", NZD: "NZ$",
};

// ── Yahoo Finance Suffix → Currency Code ────────────────────────────
// Data-driven lookup: easier to maintain than if-else chains.
const SUFFIX_MAP: Record<string, string> = {
    // 🇮🇳 India
    ".NS": "INR", ".BO": "INR",
    // 🇬🇧 London Stock Exchange
    ".L": "GBP",
    // 🇪🇺 Euronext & Eurozone
    ".PA": "EUR", ".AS": "EUR", ".BR": "EUR", ".LS": "EUR",  // Paris, Amsterdam, Brussels, Lisbon
    ".MI": "EUR", ".MC": "EUR", ".HE": "EUR", ".VI": "EUR",  // Milan, Madrid, Helsinki, Vienna
    ".DE": "EUR",                                                 // Deutsche Börse (Xetra)
    // 🇯🇵 Tokyo Stock Exchange
    ".T": "JPY",
    // 🇨🇳 China
    ".SS": "CNY", ".SZ": "CNY",                                 // Shanghai, Shenzhen
    // 🇭🇰 Hong Kong
    ".HK": "HKD",
    // 🇸🇬 Singapore
    ".SI": "SGD",
    // 🇦🇺 Australia
    ".AX": "AUD",
    // 🇨🇦 Toronto Stock Exchange
    ".TO": "CAD",
    // 🇨🇭 SIX Swiss Exchange
    ".SW": "CHF",
    // 🇰🇷 Korea (KSE & KOSDAQ)
    ".KS": "KRW", ".KQ": "KRW",
    // 🇹🇼 Taiwan
    ".TW": "TWD", ".TWO": "TWD",
    // 🇿🇦 Johannesburg Stock Exchange
    ".JO": "ZAR",
    // 🇸🇦 Saudi (Tadawul)
    ".SR": "SAR",
    // 🇸🇪 Stockholm (Nasdaq Nordic)
    ".ST": "SEK",
    // 🇳🇴 Oslo
    ".OL": "NOK",
    // 🇩🇰 Copenhagen
    ".CO": "DKK",
    // 🇧🇷 B3 (São Paulo)
    ".SA": "BRL",
    // 🇲🇽 Mexico
    ".MX": "MXN",
    // 🇮🇩 Jakarta
    ".JK": "IDR",
    // 🇲🇾 Kuala Lumpur
    ".KL": "MYR",
    // 🇹🇭 Bangkok
    ".BK": "THB",
    // 🇮🇱 Tel Aviv
    ".TA": "ILS",
    // 🇹🇷 Istanbul
    ".IS": "TRY",
    // 🇵🇱 Warsaw
    ".WA": "PLN",
    // 🇳🇿 New Zealand
    ".NZ": "NZD",
};

/** Resolve currency symbol from a currency code (e.g. "INR" → "₹") */
export function getCurrencySymbol(code: string): string {
    return SYMBOL_MAP[code] || `${code} `;
}

/** Infer currency code from a ticker string (e.g. "MISHT.NS" → "INR", "AAPL" → "USD") */
export function inferCurrencyFromTicker(ticker?: string): string {
    if (!ticker) return "USD";
    const t = ticker.toUpperCase();

    // Try longest suffix first (.TWO = 4 chars), then shorter ones
    for (const len of [4, 3, 2]) {
        const dot = t.lastIndexOf(".");
        if (dot !== -1) {
            const suffix = t.substring(dot);
            if (suffix.length === len + 1 && SUFFIX_MAP[suffix]) {
                return SUFFIX_MAP[suffix];
            }
        }
    }
    return "USD";
}

/** Convenience: ticker → symbol (e.g. "RPOWER.NS" → "₹") */
export function currencySymbolForTicker(ticker?: string): string {
    return getCurrencySymbol(inferCurrencyFromTicker(ticker));
}

/** Format a number with the right currency symbol */
export function formatPrice(value: number | undefined | null, ticker?: string): string {
    if (value == null) return "---";
    const sym = currencySymbolForTicker(ticker);
    return `${sym}${value.toLocaleString()}`;
}
