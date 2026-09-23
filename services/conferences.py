import re

# Canonical labels used everywhere in the UI/database. This keeps conference
# names consistent when public sources return slugs, abbreviations or long names.
CONFERENCE_ALIASES = {
    'acc': 'ACC',
    'atlantic coast': 'ACC',
    'atlantic coast conference': 'ACC',
    'big ten': 'Big Ten',
    'big-ten': 'Big Ten',
    'big 10': 'Big Ten',
    'b1g': 'Big Ten',
    'big east': 'Big East',
    'big-east': 'Big East',
    'big west': 'Big West',
    'big-west': 'Big West',
    'big south': 'Big South',
    'big-south': 'Big South',
    'america east': 'America East',
    'america-east': 'America East',
    'american': 'American Athletic',
    'american athletic': 'American Athletic',
    'american athletic conference': 'American Athletic',
    'aac': 'American Athletic',
    'atlantic 10': 'Atlantic 10',
    'atlantic-10': 'Atlantic 10',
    'a-10': 'Atlantic 10',
    'a10': 'Atlantic 10',
    'asun': 'ASUN',
    'atlantic sun': 'ASUN',
    'atlantic sun conference': 'ASUN',
    'conference usa': 'CUSA',
    'c usa': 'CUSA',
    'cusa': 'CUSA',
    'coastal athletic association': 'CAA',
    'colonial athletic association': 'CAA',
    'caa': 'CAA',
    'horizon': 'Horizon League',
    'horizon league': 'Horizon League',
    'ivy': 'Ivy League',
    'ivy league': 'Ivy League',
    'maac': 'MAAC',
    'metro atlantic athletic': 'MAAC',
    'metro atlantic athletic conference': 'MAAC',
    'mid-american': 'MAC',
    'mid american': 'MAC',
    'mac': 'MAC',
    'missouri valley': 'Missouri Valley',
    'missouri valley conference': 'Missouri Valley',
    'mvc': 'Missouri Valley',
    'northeast': 'NEC',
    'northeast conference': 'NEC',
    'nec': 'NEC',
    'ohio valley': 'OVC',
    'ohio valley conference': 'OVC',
    'ovc': 'OVC',
    'patriot': 'Patriot League',
    'patriot league': 'Patriot League',
    'southern': 'SoCon',
    'southern conference': 'SoCon',
    'socon': 'SoCon',
    'summit': 'Summit League',
    'summit league': 'Summit League',
    'sun belt': 'Sun Belt',
    'sun-belt': 'Sun Belt',
    'west coast': 'WCC',
    'west coast conference': 'WCC',
    'wcc': 'WCC',
    'western athletic': 'WAC',
    'western athletic conference': 'WAC',
    'wac': 'WAC',
    'independent': 'Independent',
    'independents': 'Independent',
}

# Small verified-current fallback map for nationally visible D-I teams. Live 2026
# NCAA standings always take precedence; this only prevents blanks while those
# standings are still loading or when a public endpoint is temporarily down.
D1_SCHOOL_CONFERENCE_FALLBACK = {
    'stanford': 'ACC',
    'smu': 'ACC',
    'louisville': 'ACC',
    'clemson': 'ACC',
    'notre dame': 'ACC',
    'duke': 'ACC',
    'nc state': 'ACC',
    'north carolina': 'ACC',
    'virginia': 'ACC',
    'virginia tech': 'ACC',
    'wake forest': 'ACC',
    'syracuse': 'ACC',
    'pitt': 'ACC',
    'boston college': 'ACC',
    'california': 'ACC',
    'cal': 'ACC',
    'indiana': 'Big Ten',
    'ohio state': 'Big Ten',
    'ohio st': 'Big Ten',
    'wisconsin': 'Big Ten',
    'maryland': 'Big Ten',
    'michigan state': 'Big Ten',
    'michigan st': 'Big Ten',
    'washington': 'Big Ten',
    'ucla': 'Big Ten',
    'penn state': 'Big Ten',
    'rutgers': 'Big Ten',
    'michigan': 'Big Ten',
    'northwestern': 'Big Ten',
    'georgetown': 'Big East',
    'akron': 'Big East',
    'creighton': 'Big East',
    'marquette': 'Big East',
    'providence': 'Big East',
    'villanova': 'Big East',
    'san diego': 'WCC',
    'oregon state': 'WCC',
    'portland': 'WCC',
    'saint marys ca': 'WCC',
    'south carolina': 'Sun Belt',
    'old dominion': 'Sun Belt',
    'marshall': 'Sun Belt',
    'west virginia': 'Sun Belt',
    'ucf': 'Sun Belt',
    'princeton': 'Ivy League',
    'cornell': 'Ivy League',
    'vermont': 'America East',
    'bryant': 'America East',
    'missouri state': 'American Athletic',
    'charlotte': 'American Athletic',
    'florida atlantic': 'American Athletic',
    'memphis': 'American Athletic',
    'south florida': 'American Athletic',
    'tulsa': 'American Athletic',
    'temple': 'American Athletic',
    'uab': 'American Athletic',
    'florida international': 'American Athletic',
    'fiu': 'American Athletic',
    'umkc': 'Summit League',
    'kansas city': 'Summit League',
    'uc santa barbara': 'Big West',
    'ucsb': 'Big West',
    'high point': 'Big South',
    'hofstra': 'CAA',
    'unc wilmington': 'CAA',
    'uncw': 'CAA',
    'utah valley': 'WAC',
    'florida gulf coast': 'ASUN',
    'florida gulf coast university': 'ASUN',
}


def _clean(value):
    text = str(value or '').strip().lower().replace('&', ' and ')
    text = text.replace('_', ' ').replace('/', ' ')
    text = re.sub(r'[-–—]+', ' ', text)
    text = re.sub(r'\bconference\b', ' ', text)
    text = re.sub(r'[^a-z0-9 ]+', ' ', text)
    return ' '.join(text.split())


def canonicalize_conference(value):
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    key = _clean(raw)
    if key in CONFERENCE_ALIASES:
        return CONFERENCE_ALIASES[key]
    # normalize common suffix/prefix variants without inventing a new league
    if key.startswith('the '):
        key = key[4:]
        if key in CONFERENCE_ALIASES:
            return CONFERENCE_ALIASES[key]
    # Preserve a clean human-readable name when we do not know an alias yet.
    return raw.replace('-', ' ').strip()


def normalize_school(value):
    text = str(value or '').strip().lower().replace('&', ' and ')
    replacements = {
        r'\bst\.?\b': 'state',
        r'\buniv\.?\b': 'university',
        r'\bcal st\.?\b': 'california state',
    }
    for pat, repl in replacements.items():
        text = re.sub(pat, repl, text)
    text = re.sub(r'\b(the|university|college|of|at)\b', ' ', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return ' '.join(text.split())


def fallback_conference_for_school(school, division='D1'):
    if division != 'D1':
        return None
    key = normalize_school(school)
    if key in D1_SCHOOL_CONFERENCE_FALLBACK:
        return D1_SCHOOL_CONFERENCE_FALLBACK[key]
    # A few entries contain "university" in the fallback source label while
    # normalize_school removes it; try substring matching only for long names.
    for known, conf in D1_SCHOOL_CONFERENCE_FALLBACK.items():
        k = normalize_school(known)
        if key == k or (len(key) >= 6 and len(k) >= 6 and (key in k or k in key)):
            return conf
    return None
