"""Simple affordability screening for fictional AMD consumer loans."""
import math

POLICY_VERSION = 'demo-am-2.0'
# Illustrative portfolio thresholds, not Armenian regulation or bank policy.
DTI_REVIEW = .35
DTI_HIGH_RISK = .50
MIN_REMAINDER = .15
OVERDUE_HIGH_RISK = 30
FIELDS = {
    'income': (1, 100_000_000), 'expenses': (0, 100_000_000),
    'existing_debt': (0, 100_000_000), 'amount': (1, 100_000_000),
    'annual_rate': (0, 60), 'months': (1, 360), 'late_days': (0, 3650),
}
LABELS = {
    'income': 'Զուտ եկամուտ', 'expenses': 'Ընտանիքի ծախսեր',
    'existing_debt': 'Գործող վարկերի ամսական վճարներ', 'amount': 'Վարկի գումար',
    'annual_rate': 'Անվանական տոկոսադրույք', 'months': 'Ժամկետ',
    'late_days': 'Ընթացիկ ժամկետանց օրեր',
}

def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Անհրաժեշտ է JSON օբյեկտ։')
    if set(data) != set(FIELDS):
        raise ValueError('Պարտադիր դաշտերը՝ ' + ', '.join(FIELDS))
    result = {}
    for key, (low, high) in FIELDS.items():
        value = data[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'{LABELS[key]}․ մուտքագրեք վավեր թիվ։')
        if not low <= value <= high:
            raise ValueError(f'{LABELS[key]}․ թույլատրելի միջակայքը՝ {low}–{high}։')
        if key in ('months', 'late_days') and int(value) != value:
            raise ValueError(f'{LABELS[key]}․ մուտքագրեք ամբողջ թիվ։')
        result[key] = value
    return result

def payment(amount, annual_rate, months):
    rate = annual_rate / 1200
    if rate == 0:
        return amount / months
    return amount * rate / -math.expm1(-months * math.log1p(rate))

def evaluate(data):
    x = validate(data)
    monthly = payment(x['amount'], x['annual_rate'], x['months'])
    debt = monthly + x['existing_debt']
    dti = debt / x['income']
    remainder = x['income'] - x['expenses'] - debt
    high_risk, review = [], []
    if dti > DTI_HIGH_RISK:
        high_risk.append('Վարկերի ամսական վճարները գերազանցում են զուտ եկամտի 50%-ը։')
    elif dti > DTI_REVIEW:
        review.append('Վարկերի ամսական վճարները կազմում են զուտ եկամտի ավելի քան 35%-ը։')
    if remainder < 0:
        high_risk.append('Եկամուտը չի բավարարում ընտանիքի ծախսերն ու վարկերի վճարները ծածկելու համար։')
    elif remainder < x['income'] * MIN_REMAINDER:
        review.append('Ծախսերից ու վարկերից հետո մնում է եկամտի 15%-ից պակաս։ Պահուստը փոքր է։')
    if x['late_days'] > OVERDUE_HIGH_RISK:
        high_risk.append('Ընթացիկ ժամկետանց պարտավորությունը գերազանցում է 30 օրը։')
    elif x['late_days'] > 0:
        review.append('Կա ընթացիկ ժամկետանց պարտավորություն․ անհրաժեշտ է պարզել պատճառը։')
    decision = 'HIGH_RISK' if high_risk else 'REVIEW' if review else 'PASS'
    return {
        'decision': decision,
        'monthly_payment': round(monthly, 2),
        'total_monthly_debt': round(debt, 2),
        'dti_percent': round(dti * 100, 2),
        'disposable_income': round(remainder, 2),
        'total_repayment': round(monthly * x['months'], 2),
        'reasons': high_risk + review or ['Մուտքագրված տվյալներով վճարունակության ցուցադրական պայմանները բավարարված են։'],
        'policy_version': POLICY_VERSION,
    }
