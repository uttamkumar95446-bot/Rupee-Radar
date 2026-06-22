"""Category definitions and fallback keyword maps for transaction categorization."""

from typing import Dict, List

# All supported categories
ALL_CATEGORIES = [
    "Food",
    "Travel",
    "Shopping",
    "Bills",
    "EMI",
    "Subscriptions",
    "Salary",
    "Rent",
    "Investments",
    "Other",
]

# Fallback keyword → category mapping (case-insensitive match)
# Used when AI categorization is unavailable or confidence is low
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Food": [
        "swiggy", "zomato", "restaurant", "cafe", "dine", "food",
        "pizza", "burger", "dominos", "mcdonald", "kfc", "subway",
        "dosa", "biryani", "tiffin", "canteen", "lunch", "dinner",
        "breakfast", "zomato order", "swiggy order", "eat", "mcd",
        "starbucks", "coffee", "tea", "bakery", " sweets", "haldiram",
        "bikaner", "barbecue", "barbeque", "chaat", "paneer",
    ],
    "Travel": [
        "uber", "ola", "metro", "cab", "flight", "irctc", "bus",
        "train", "taxi", "rapido", "auto", "rickshaw", "air india",
        "indigo", "spicejet", "goair", "redbus", "makemytrip",
        "goibibo", "mmt", "ola cab", "uber cab", "petrol", "fuel",
        "indian oil", "hp petrol", "bharat petroleum", "toll",
        "parking", "highway", "shuttle",
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "meesho", "shopping", "mall",
        "store", "amazon pay", "amazon.in", "ajio", "nykaa",
        "zivame", "lenskart", "tata cliq", "shopclues", "snapdeal",
        "lifestyl", "max", "pantaloons", "shoppers stop", "reliance trends",
        "dmart", "big bazaar", "more", "spencers",
    ],
    "Bills": [
        "electricity", "water bill", "broadband", "phone bill",
        "recharge", "bsnl", "airtel", "jio", "vodafone", "idea",
        "vi", "act broadband", "hathway", "tata sky", "dish tv",
        "bill", "utility", "gas", "lpg", "property tax",
        "maintenance", "society", "electric", "power",
    ],
    "EMI": [
        "emi", "loan", "loan repayment", "personal loan",
        "home loan", "car loan", "auto loan", "education loan",
        "loan emi", "gold loan",
    ],
    "Subscriptions": [
        "netflix", "prime", "prime video", "hotstar", "disney+",
        "spotify", "youtube premium", "youtube music", "icloud",
        "google one", "apple music", "amazon music", "gaana", "wynk",
        "sony liv", "voot", "zee5", "altbalaji", "eros now",
        "subscri", "membership", "patreon", "medium", "chatgpt plus",
        "github copilot", "notion", "canva pro", "adobe",
    ],
    "Salary": [
        "salary", "credit salary", "payroll", "wages", "monthly salary",
        "salary credit", "salary deposit", "hra",
    ],
    "Rent": [
        "rent", "rental", "house rent", "office rent", "rent payment",
        "monthly rent", "flat rent",
    ],
    "Investments": [
        "sip", "mutual fund", "stock", "nifty", "ppf", "nps", "epf",
        "investment", "equity", "bond", "fixed deposit", "rd",
        "recurring deposit", "fd", "share", "dividend", "etf",
        "demat", "zerodha", "groww", "angel broking", "upstox",
        "icici direct", "hdfc sec", "kotak sec",
    ],
}

# Keywords that indicate transfers (not real income/spend)
TRANSFER_KEYWORDS = [
    "transfer", "imps", "neft", "rtgs", "upi transfer", "self transfer",
    "credit card payment", "cc payment", "card payment", "wallet top",
    "paytm wallet", "phonepe wallet", "googlepay", "gpay",
    "own account", "fund transfer", "internal transfer",
]

# Keywords that indicate failed/declined transactions (should be excluded)
DECLINED_KEYWORDS = [
    "failed", "declined", "reversed", "cancelled", "canceled",
    "returned", "refund", "chargeback",
]

# Known Indian bank format identifiers (for CSV auto-detection)
BANK_FORMAT_KEYWORDS = {
    "hdfc": ["hdfc bank", "hdfc ltd"],
    "icici": ["icici bank", "icici ltd"],
    "sbi": ["state bank of india", "sbi", "sbicard"],
    "axis": ["axis bank", "axis ltd"],
    "kotak": ["kotak mahindra", "kotak bank"],
    "yes": ["yes bank"],
    "idfc": ["idfc bank"],
}
