"""Deterministic guardrails and cue detectors. No model is involved here, so no prompt can switch them off.

- mask_sensitive(): hides full card numbers (Luhn-valid), OTPs and CVVs before text reaches a model or a log.
- looks_like_injection(): instructions hidden inside a customer message or a forwarded email.
- fraud_cues() / vulnerable_cues(): keyword rules that set priority, in Arabic (incl. Gulf and Arabizi),
  English and French.
- asks_for_secrets(): finds sentences in a draft that ask the customer for a PIN, OTP, CVV, password or
  full card number (a sentence that says "we will never ask for..." is fine).
"""

from __future__ import annotations

import re
import unicodedata

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
APOSTROPHES = str.maketrans("’‘ʼ`", "'" * 4)


def normalise(text: str) -> str:
    """Lower case, Arabic-Indic digits to 0-9, accents and marks removed, so one keyword list fits more spellings.

    Removing combining marks turns é into e, and also أ/إ/آ into ا (a usual Arabic normalisation).
    """
    # Typographic apostrophes (don’t) become plain ones (don't). Missing this made the output check block
    # drafts that said "please don’t share your OTP" (found in the first live run, see README).
    text = str(text).translate(ARABIC_DIGITS).translate(APOSTROPHES).lower()
    return "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))


def _norm_patterns(patterns: list[str]) -> list[str]:
    """Normalise regex patterns the same way as the text (only lower-case escapes like \\b \\s \\d are used)."""
    return [normalise(pattern) for pattern in patterns]


def detect_language(text: str) -> str:
    """'ar', 'en' or 'fr'. Arabizi (Arabic in Latin letters, e.g. '3ndi mushkila') counts as Arabic."""
    letters = [ch for ch in text if ch.isalpha()]
    if letters and sum("؀" <= ch <= "ۿ" for ch in letters) / len(letters) > 0.3:
        return "ar"
    words = re.findall(r"[a-z0-9']+", normalise(text))
    arabizi = sum(bool(re.search(r"[a-z][2375]|[2375][a-z]", w)) for w in words) + sum(w in ARABIZI_WORDS for w in words)
    french = sum(w in FRENCH_WORDS for w in words) + len(re.findall(r"[éèêàçùâîôû]", text.lower()))
    if arabizi >= 2 and arabizi > french:
        return "ar"
    return "fr" if french >= 2 else "en"


ARABIZI_WORDS = {"ana", "inta", "enta", "mafi", "abi", "aby", "wain", "wayn", "shu", "lesh", "leish", "ya3ni", "mob",
                 "msh", "mish", "3ndi", "3indi", "7ag", "6ayeb", "zain", "bs", "bas", "yalla", "w", "el", "il", "fi",
                 "kartat", "karti", "flousi", "floos", "7sabi", "hasabi", "lamma", "ba3d", "ma3", "lazem", "akhuy"}
FRENCH_WORDS = {"je", "j'ai", "mon", "ma", "mes", "est", "pas", "le", "la", "les", "des", "une", "un", "carte",
                "compte", "pour", "avec", "sur", "vous", "votre", "vos", "bonjour", "merci", "virement", "frais",
                "depuis", "toujours", "rien", "j'", "qu'", "c'est", "n'ai", "pourquoi", "comment", "suis", "ai"}

# ---------- masking: what never reaches a model or a log ----------
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
# A secret word, a short gap that is not a currency (so "PIN blocked, AED 300" keeps its amount), then 3-8 digits.
OTP_RE = re.compile(r"\b(otp|code|pin|cvv|cvc|password|passcode|رمز|الرمز|الرقم السري|كلمة المرور|mot de passe)"
                    r"((?:(?!aed|dhs|dirham|درهم)[^0-9\n]){0,25})(\d{3,8})\b", re.IGNORECASE)


def luhn_ok(digits: str) -> bool:
    total, double = 0, False
    for ch in reversed(digits):
        value = int(ch) * 2 if double else int(ch)
        total += value - 9 if value > 9 else value
        double = not double
    return total % 10 == 0


def mask_sensitive(text: str) -> tuple[str, list[str]]:
    """Return (masked text, list of what was masked). Arabic-Indic digits are converted first."""
    text = str(text).translate(ARABIC_DIGITS)
    found = []

    def card(match: re.Match) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            found.append("card_number")
            return f"[card ending {digits[-4:]}]"
        return match.group(0)

    def secret(match: re.Match) -> str:
        found.append("secret_code")
        return f"{match.group(1)}{match.group(2)}[removed]"

    text = CARD_RE.sub(card, text)
    text = OTP_RE.sub(secret, text)
    return text, found


# ---------- prompt injection ----------
INJECTION_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|your|earlier)? ?(instructions|rules|guidelines|prompt)",
    r"disregard (all |the |your )?(previous |above )?(instructions|rules)",
    r"(new|updated|override) (system )?instructions", r"\bsystem\s*(prompt|message)?\s*:", r"<\s*/?\s*system",
    r"you are now", r"developer mode", r"\bas the (ai|assistant|bot)\b", r"(ai|assistant|bot|model)\s*:\s*",
    r"(route|send|forward|escalate) (this|the case|it) to (the )?(vip|director|ceo|priority)",
    r"mark (this|it|the case) as (resolved|closed|urgent|approved)", r"approve (the |my |this )?refund",
    r"تجاهل (جميع |كل |)(التعليمات|القواعد|الأوامر)", r"تعليمات جديدة", r"أنت الآن", r"وافق على (الاسترداد|استرداد)",
    r"ignorez? (toutes |les |tes |vos )*(instructions|regles|consignes)", r"oublie[zs]? (tes|vos|les) (regles|instructions)",
    r"nouvelles instructions", r"tu es maintenant", r"approuve[zr]? (le |mon )?remboursement",
]


INJECTION_PATTERNS = _norm_patterns(INJECTION_PATTERNS)


def looks_like_injection(text: str) -> bool:
    lowered = normalise(text)
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)


# ---------- priority cues (rules in code: fraud -> security team at once; vulnerable -> human, priority) ----------
FRAUD_CUES = [
    # English
    "stolen", "lost my card", "lost my wallet", "lost my phone", "didn't make", "did not make", "not me",
    "don't recognise", "don't recognize", "do not recognise", "never heard of", "unauthori", "hacked", "fraud",
    "scam", "phishing", "compromised", "someone used", "someone took", "pretending to be", "fake sms", "suspicious",
    # Arabic (MSA and Gulf)
    "سرق", "مسروق", "ضاعت بطاقتي", "فقدت بطاقتي", "فقدت محفظتي", "ضاع", "احتيال", "نصب", "اختراق", "مخترق",
    "لم أقم", "ما سويت", "مب أنا", "مو أنا", "ما أعرف", "لا أعرف هذه", "لا أعرفها", "رسالة مزيفة", "انتحل",
    "مشبوه", "لم أجر",
    # Arabizi
    "msroo", "sirqat", "ma sawait", "mob ana", "7arami", "e7tiyal", "sare8", "ma a3rif",
    # French
    "vole", "perdu ma carte", "perdu mon portefeuille", "perdu mon telephone", "pas moi", "je ne reconnais pas",
    "jamais entendu", "fraude", "arnaque", "pirate", "piratage", "hameconnage", "frauduleu", "usurp", "se faisant passer",
    "suspect",
]
VULNERABLE_CUES = [
    # English
    "passed away", "died", "death of", "funeral", "bereave", "hospital", "cancer", "chemotherapy", "terminal",
    "lost my job", "lost his job", "lost her job", "unemployed", "can't afford", "cannot afford", "struggling to pay",
    "dementia", "disabled", "disability", "visually impaired", "blind", "wheelchair", "divorce", "domestic",
    "mental health", "depression",
    # Arabic
    "توفي", "توفى", "وفاة", "المرحوم", "المرحومة", "مستشفى", "المستشفى", "سرطان", "فقدت وظيفتي", "فقدت عملي",
    "خسرت شغلي", "ما عندي راتب", "لا أستطيع الدفع", "ما أقدر أدفع", "الخرف", "زهايمر", "كفيف", "إعاقة", "طلاق",
    "ضعيف البصر", "ضعف البصر",
    # Arabizi
    "twaffa", "tuwfi", "mustashfa", "khasart sheghli", "ma 3ndi ratib", "6alaq",
    # French
    "decede", "deces", "obseques", "hopital", "cancer", "chimiotherapie", "perdu mon emploi", "perdu mon travail",
    "chomage", "pas les moyens", "du mal a payer", "demence", "alzheimer", "handicap", "malvoyant", "aveugle",
    "divorce",
]


def _has_any(text: str, cues: list[str]) -> list[str]:
    lowered = normalise(text)
    return [cue for cue in cues if normalise(cue) in lowered]


def fraud_cues(text: str) -> list[str]:
    return _has_any(text, FRAUD_CUES)


def vulnerable_cues(text: str) -> list[str]:
    return _has_any(text, VULNERABLE_CUES)


# ---------- output check: never ask for secrets ----------
SECRET_TERMS = [
    r"\bpin\b", r"\botp\b", "one-time password", "one time password", "verification code", r"\bcvv\b", r"\bcvc\b",
    "security code", "password", "passcode", "full card number", "card number", "online banking login",
    "الرقم السري", "الرمز السري", "رمز التحقق", "رمز otp", "كلمة المرور", "كلمة السر", "رقم البطاقة", "رمز الأمان",
    "code pin", "code secret", "code confidentiel", "mot de passe", "code otp", "code de verification",
    "code a usage unique", "cryptogramme", "numero de carte", "numero complet",
]
NEGATIONS = [
    r"\bnever\b", r"\bnot\b", r"n't\b", r"\bno one\b", r"\bnobody\b", r"\bdo not\b", r"\bavoid\b",
    # Arabic negations, also with the "and" prefix و (ولا، ولن، ولم), added after the first live run.
    "لن", r"(^|\s)و?لا(\s|$)", "أبدا", "ابدا", "ليس", r"(^|\s)و?لم(\s|$)", "تجنب", "إياك", "عدم",
    r"\bjamais\b", r"\bne\b", r"\bn'", r"\baucun", r"\bpas\b",
]


SECRET_TERMS, NEGATIONS = _norm_patterns(SECRET_TERMS), _norm_patterns(NEGATIONS)

# Asking for the last 4 digits of a card is allowed (they are not a secret), so these phrases are removed first.
SAFE_PHRASES = [r"(last|final) (4|four) digits( of (your|the) card( number)?)?", r"card ending( in)?",
                r"(اخر|آخر) (4|اربع|أربع|اربعة|أربعة) (ارقام|أرقام)( من رقم البطاقة| لرقم البطاقة)?",
                r"(4|quatre) derniers chiffres( de (votre|la) carte| du numero de carte)?"]
SAFE_PHRASES = _norm_patterns(SAFE_PHRASES)


def asks_for_secrets(draft: str) -> list[str]:
    """Sentences that mention a secret (PIN, OTP, CVV, password, card number) without a negation."""
    flagged = []
    text = normalise(draft)
    for phrase in SAFE_PHRASES:
        text = re.sub(phrase, " ", text)
    for sentence in re.split(r"(?<=[.!?؟\n])\s*", text):
        mentions = any(re.search(term, sentence) for term in SECRET_TERMS)
        negated = any(re.search(neg, sentence) for neg in NEGATIONS)
        if mentions and not negated:
            flagged.append(sentence.strip()[:160])
    return flagged


# ---------- keyword complaint detector (the rules baseline) ----------
COMPLAINT_CUES = [
    "complain", "complaint", "unacceptable", "disappointed", "disgrace", "terrible", "awful", "worst", "rip-off",
    "rip off", "ridiculous", "fed up", "angry", "furious", "cheated", "rude", "refund", "reverse", "i want it back",
    "my money back", "still not", "still haven't", "still hasn't", "still no", "still nothing", "never arrived",
    "never received", "never delivered", "nobody", "no one", "again", "charged twice", "twice", "wrong amount",
    "didn't make", "did not make", "fix this", "compensation", "explain why", "explanation", "hung up",
    "شكوى", "أشتكي", "اشتكي", "غير مقبول", "سيء", "سيئة", "أسوأ", "زعلان", "مستاء", "محبط", "استرداد", "أرجعوا",
    "رجعوا", "لم يصل", "ما وصل", "لم تصل", "ما وصلت", "مرتين", "حتى الآن", "للحين", "إلى الآن", "تعويض", "وقح",
    "مب معقول", "مو معقول", "خدمة سيئة", "ليش", "لماذا لم", "ما أحد", "لا أحد", "مرة ثانية", "مرة أخرى",
    "shakwa", "ashtiki", "mob ma3qool", "kharban", "ma wasal", "marratain", "lil7een", "ta3weedh",
    "plainte", "reclamation", "inacceptable", "decu", "honteux", "scandaleux", "pire", "nul", "rembourse",
    "toujours pas", "jamais recu", "jamais arrive", "jamais livre", "personne", "deux fois", "encore",
    "mauvais montant", "compensation", "explication", "arnaque", "raccroche", "impoli",
]


def complaint_cues(text: str) -> list[str]:
    return _has_any(text, COMPLAINT_CUES)


# ---------- output check: an acknowledgement never promises an outcome ----------
PROMISE_PATTERNS = _norm_patterns([
    r"refund (has been|is|was) (approved|processed|issued|completed)", r"(approved|processed|issued) (your|the) refund",
    r"we (will|shall|have) (refund|credit|reverse|waive)", r"(has|have) been (credited|refunded|reversed|waived)",
    r"(case|complaint|dispute) (has been|is) (resolved|closed)", r"pre-?approved",
    r"تمت الموافقة على (الاسترداد|استرداد)", r"(سيتم|تم) (استرداد|إيداع|ارجاع|إرجاع|إلغاء الرسوم)", r"سنقوم (باسترداد|بإيداع|بإرجاع)",
    r"(تم|سيتم) (حل|إغلاق) (الحالة|الشكوى)", r"معتمد مسبقا",
    r"remboursement (a ete|est|sera) (approuve|effectue|valide)", r"nous (allons|avons) (rembourse|credite|annule)",
    r"nous vous rembourserons", r"(sera|a ete) (credite|rembourse|annule)", r"(dossier|reclamation) (est|a ete) (resolu|clos|cloture)",
    r"pre-?approuve",
])


def promises_outcome(draft: str) -> list[str]:
    text = normalise(draft)
    return [pattern for pattern in PROMISE_PATTERNS if re.search(pattern, text)]
