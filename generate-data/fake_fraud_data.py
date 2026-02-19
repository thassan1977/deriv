# generate fake fraud data
import random
import string
import hashlib
from datetime import datetime, timedelta
from faker import Faker
import psycopg2
from psycopg2.extras import execute_values
import json
import uuid


fake = Faker()
Faker.seed(42)
random.seed(42)

# Database connection
conn = psycopg2.connect(
    dbname="frauddb",
    user="user",
    password="123456",
    host="localhost",
    port="5432"
)
cur = conn.cursor()

# =====================================================
# CONFIGURATION
# =====================================================

NUM_LEGITIMATE_USERS = 500
NUM_FRAUD_USERS = 50
NUM_FRAUD_RINGS = 5
NUM_DEVICES = 300
NUM_IPS = 200
TRANSACTIONS_PER_USER = (10, 100)  # Random range

# Country risk levels
HIGH_RISK_COUNTRIES = ['NG', 'IR', 'KP', 'SY', 'VE', 'MM', 'AF']
SANCTIONED_COUNTRIES = ['KP', 'IR', 'SY', 'CU']
SAFE_COUNTRIES = ['US', 'GB', 'SG', 'DE', 'FR', 'AU', 'CA', 'JP', 'NL', 'CH']

# =====================================================
# HELPER FUNCTIONS
# =====================================================

GENERATED_USER_IDS = set()

def generate_user_id():
    while True:
        uid = f"USR-{random.randint(100000, 999999)}"
        if uid not in GENERATED_USER_IDS:
            GENERATED_USER_IDS.add(uid)
            return uid

def generate_device_id():
    """Realistic device fingerprint"""
    components = [
        fake.user_agent(),
        str(random.randint(1920, 3840)),
        str(random.randint(1080, 2160)),
        fake.language_code()
    ]
    return hashlib.md5(''.join(components).encode()).hexdigest()[:24]

def generate_ip():
    """Generate realistic IP address"""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 255)}"

def is_vpn_ip(ip):
    """Simulate VPN detection (some IPs are VPNs)"""
    return random.random() < 0.15  # 15% chance

def is_high_risk_country(country):
    return country in HIGH_RISK_COUNTRIES

def is_sanctioned_country(country):
    return country in SANCTIONED_COUNTRIES

# =====================================================
# 1. GENERATE DEVICES
# =====================================================

print("Generating devices...")
devices_data = []

device_types = ['MOBILE', 'DESKTOP', 'TABLET']
os_list = ['iOS', 'Android', 'Windows', 'macOS', 'Linux']
browsers = ['Chrome', 'Safari', 'Firefox', 'Edge']

for _ in range(NUM_DEVICES):
    device_id = generate_device_id()
    device_type = random.choice(device_types)
    os = random.choice(os_list)
    browser = random.choice(browsers)
    
    # Some devices are emulators (fraud indicator)
    is_emulator = random.random() < 0.05
    
    devices_data.append((
        device_id,
        datetime.now() - timedelta(days=random.randint(1, 365)),  # first_seen_at
        datetime.now() - timedelta(days=random.randint(0, 30)),   # last_seen_at
        device_type,
        os,
        browser,
        f"{random.randint(80, 120)}.0",  # browser_version
        fake.user_agent(),
        f"{random.randint(1920, 3840)}x{random.randint(1080, 2160)}",  # screen_resolution
        random.choice(['UTC-8', 'UTC-5', 'UTC+0', 'UTC+1', 'UTC+8']),
        fake.language_code(),
        is_emulator,
        False,  # is_vpn (will update based on IP)
        False,  # is_proxy
        False,  # is_tor
        1,      # total_users_count (will update)
        0       # flagged_users_count (will update)
    ))

execute_values(cur, """
    INSERT INTO devices (
        device_id, first_seen_at, last_seen_at, device_type, os, browser, browser_version,
        user_agent, screen_resolution, timezone, language, is_emulator, is_vpn, is_proxy,
        is_tor, total_users_count, flagged_users_count
    ) VALUES %s
""", devices_data)

print(f"✓ Inserted {len(devices_data)} devices")

# =====================================================
# 2. GENERATE IP ADDRESSES
# =====================================================

print("Generating IP addresses...")
ips_data = []

for _ in range(NUM_IPS):
    ip = generate_ip()
    country = random.choice(SAFE_COUNTRIES + HIGH_RISK_COUNTRIES + SANCTIONED_COUNTRIES)
    
    is_vpn = is_vpn_ip(ip)
    is_sanctioned = country in SANCTIONED_COUNTRIES
    is_high_risk = country in HIGH_RISK_COUNTRIES
    
    # Geolocation
    lat = fake.latitude()
    lon = fake.longitude()
    
    ips_data.append((
        ip,
        datetime.now() - timedelta(days=random.randint(1, 365)),
        datetime.now() - timedelta(days=random.randint(0, 30)),
        country,
        fake.country(),
        fake.city(),
        fake.state(),
        float(lat),
        float(lon),
        fake.company(),  # ISP
        fake.company(),  # Organization
        f"AS{random.randint(1000, 99999)}",
        is_vpn,
        random.random() < 0.05,  # is_proxy
        random.random() < 0.02,  # is_tor
        random.random() < 0.10,  # is_datacenter
        is_vpn or random.random() < 0.05,  # is_anonymous
        is_sanctioned,
        is_high_risk,
        0.8 if is_high_risk else 0.3 if is_vpn else 0.1,  # risk_score
        1,  # total_users_count
        0   # flagged_users_count
    ))

execute_values(cur, """
    INSERT INTO ip_addresses (
        ip_address, first_seen_at, last_seen_at, country_code, country_name, city, region,
        latitude, longitude, isp, organization, asn, is_vpn, is_proxy, is_tor, is_datacenter,
        is_anonymous, is_sanctioned_country, is_high_risk_country, risk_score,
        total_users_count, flagged_users_count
    ) VALUES %s
""", ips_data)

print(f"✓ Inserted {len(ips_data)} IP addresses")

# Get IPs for later use
cur.execute("SELECT ip_address, is_vpn, is_sanctioned_country FROM ip_addresses")
all_ips = cur.fetchall()
vpn_ips = [ip[0] for ip in all_ips if ip[1]]
sanctioned_ips = [ip[0] for ip in all_ips if ip[2]]
normal_ips = [ip[0] for ip in all_ips if not ip[1] and not ip[2]]

# Get devices for later use
cur.execute("SELECT device_id FROM devices")
all_devices = [row[0] for row in cur.fetchall()]

# =====================================================
# 3. GENERATE FRAUD RINGS
# =====================================================

print("Generating fraud rings...")
fraud_rings_data = []

fraud_ring_patterns = [
    {
        'name': 'Nigerian Prince Money Laundering Ring',
        'type': 'MONEY_LAUNDERING',
        'modus_operandi': 'Creates fake profiles with high declared income, deposits small amounts repeatedly, then withdraws via crypto. Uses rotating VPNs and shared devices.',
        'member_count': 12,
        'common_indicators': {
            'rapid_deposits': True,
            'crypto_withdrawals': True,
            'vpn_usage': True,
            'shared_devices': True,
            'income_mismatch': True
        }
    },
    {
        'name': 'Synthetic Identity Fraud Network',
        'type': 'IDENTITY_FRAUD',
        'modus_operandi': 'Uses AI-generated faces and forged documents to create synthetic identities. Builds credit slowly then maxes out accounts.',
        'member_count': 8,
        'common_indicators': {
            'ai_generated_documents': True,
            'new_accounts': True,
            'similar_behavioral_patterns': True,
            'shared_ips': True
        }
    },
    {
        'name': 'Account Takeover Phishing Gang',
        'type': 'ACCOUNT_TAKEOVER',
        'modus_operandi': 'Phishes credentials, takes over accounts, changes withdrawal addresses, drains funds.',
        'member_count': 5,
        'common_indicators': {
            'sudden_location_change': True,
            'device_change': True,
            'password_reset': True,
            'rapid_withdrawal': True
        }
    },
    {
        'name': 'Russian Bot Farm Trading Scheme',
        'type': 'MARKET_MANIPULATION',
        'modus_operandi': 'Coordinates trades across dozens of accounts to manipulate market prices.',
        'member_count': 23,
        'common_indicators': {
            'coordinated_timing': True,
            'shared_datacenter_ips': True,
            'identical_trade_patterns': True
        }
    },
    {
        'name': 'Deepfake Identity Verification Bypass',
        'type': 'IDENTITY_FRAUD',
        'modus_operandi': 'Uses deepfake technology to pass video KYC verification with stolen identities.',
        'member_count': 6,
        'common_indicators': {
            'low_face_match_scores': True,
            'video_artifacts': True,
            'mismatched_metadata': True
        }
    }
]

for i, pattern in enumerate(fraud_ring_patterns):
    fraud_ring_id = f"RING-{i+1:03d}"
    fraud_rings_data.append((
        fraud_ring_id,
        datetime.now() - timedelta(days=random.randint(30, 180)),
        pattern['name'],
        pattern['type'],
        pattern['member_count'],
        pattern['member_count'] * random.randint(2, 5),  # total_accounts
        random.randint(2, 8),  # shared_devices
        random.randint(3, 15),  # shared_ips
        random.uniform(50000, 500000),  # total_fraud_amount
        random.uniform(30000, 300000),  # estimated_losses
        random.choice(['ACTIVE', 'MONITORING', 'NEUTRALIZED']),
        pattern['modus_operandi'],
        json.dumps(pattern['common_indicators'])
    ))

execute_values(cur, """
    INSERT INTO fraud_rings (
        fraud_ring_id, discovered_at, ring_name, fraud_type, member_count, total_accounts,
        shared_devices, shared_ips, total_fraud_amount, estimated_losses, status,
        modus_operandi, common_indicators
    ) VALUES %s
""", fraud_rings_data)

print(f"✓ Inserted {len(fraud_rings_data)} fraud rings")

# =====================================================
# 4. GENERATE USERS (LEGITIMATE + FRAUD)
# =====================================================

print("Generating users...")
users_data = []
user_devices_data = []
user_ip_history_data = []
document_verifications_data = []

# Legitimate users
for i in range(NUM_LEGITIMATE_USERS):
    user_id = generate_user_id()
    created_at = datetime.now() - timedelta(days=random.randint(30, 730))
    
    # Realistic profile
    monthly_income = random.choice([2000, 3500, 5000, 7500, 10000, 15000, 25000])
    monthly_income = float(monthly_income) 
    users_data.append((
        user_id,
        created_at,
        fake.email(),
        fake.name(),
        fake.date_of_birth(minimum_age=18, maximum_age=70),
        random.choice(SAFE_COUNTRIES),
        monthly_income,
        fake.job(),
        random.choice(['EMPLOYED', 'SELF_EMPLOYED', 'RETIRED']),
        'SALARY',
        'ACTIVE',
        'LOW',
        'VERIFIED',
        created_at + timedelta(days=random.randint(1, 7)),
        0, 0, 0,  # Will update with transactions
        datetime.now() - timedelta(hours=random.randint(1, 168))
    ))
    
    # Document verification (all passed for legitimate users)
    document_verifications_data.append((
        user_id,
        created_at + timedelta(days=1),
        random.choice(['PASSPORT', 'DRIVERS_LICENSE', 'NATIONAL_ID']),
        f"{random.choice(['A', 'B', 'C'])}{random.randint(100000, 999999)}",
        random.choice(SAFE_COUNTRIES),
        fake.date_between(start_date='+1y', end_date='+10y'),
        'PASSED',
        random.uniform(0.85, 0.99),
        random.uniform(0.88, 0.99),
        False, False, False,
        random.uniform(0.85, 0.99),
        json.dumps({}),
        'AI_AUTO',
        None
    ))
    
    # Assign 1-3 devices per user
    num_devices = random.randint(1, 3)
    user_devices_list = random.sample(all_devices, num_devices)
    
    for device_id in user_devices_list:
        first_used = created_at + timedelta(days=random.randint(0, 30))
        user_devices_data.append((
            user_id, device_id, first_used,
            datetime.now() - timedelta(days=random.randint(0, 30)),
            random.randint(5, 100)
        ))
    
    # IP history (mostly from safe countries)
    num_ips = random.randint(2, 8)
    for _ in range(num_ips):
        ip = random.choice(normal_ips) if normal_ips else generate_ip()
        device = random.choice(user_devices_list)
        accessed_at = created_at + timedelta(days=random.randint(0, 365))
        
        user_ip_history_data.append((
            user_id, ip, device, accessed_at,
            random.randint(300, 7200)  # session duration
        ))

# Fraud users (distributed across fraud rings)
fraud_user_ids = []
for ring_idx, ring in enumerate(fraud_rings_data):
    fraud_ring_id = ring[0]
    member_count = ring[4]
    
    # Create fraudulent users for this ring
    for _ in range(member_count):
        user_id = generate_user_id()
        fraud_user_ids.append((user_id, fraud_ring_id))
        created_at = datetime.now() - timedelta(days=random.randint(7, 90))
        
        # Suspicious profiles
        declared_income = random.choice([500, 1000, 1500])  # Low declared income
        
        users_data.append((
            user_id,
            created_at,
            fake.email(),
            fake.name(),
            fake.date_of_birth(minimum_age=18, maximum_age=70),
            random.choice(HIGH_RISK_COUNTRIES + SANCTIONED_COUNTRIES),
            declared_income,
            'Student',  # Common fraud cover
            'UNEMPLOYED',
            'OTHER',
            random.choice(['ACTIVE', 'UNDER_REVIEW', 'SUSPENDED']),
            'HIGH',
            random.choice(['PENDING', 'VERIFIED', 'REJECTED']),
            created_at + timedelta(days=random.randint(1, 30)),
            0, 0, 0,
            datetime.now() - timedelta(hours=random.randint(1, 48))
        ))
        
        # Fraudulent documents
        doc_status = random.choice(['PASSED', 'MANUAL_REVIEW', 'FAILED'])
        is_forged = random.random() < 0.3
        is_ai_generated = random.random() < 0.2
        
        document_verifications_data.append((
            user_id,
            created_at + timedelta(days=1),
            random.choice(['PASSPORT', 'NATIONAL_ID']),
            f"{random.choice(['X', 'Y', 'Z'])}{random.randint(100000, 999999)}",
            random.choice(HIGH_RISK_COUNTRIES),
            fake.date_between(start_date='+1y', end_date='+5y'),
            doc_status,
            random.uniform(0.45, 0.75) if is_forged else random.uniform(0.75, 0.95),
            random.uniform(0.40, 0.70) if is_ai_generated else random.uniform(0.75, 0.95),
            is_forged,
            is_ai_generated,
            False,
            random.uniform(0.40, 0.75),
            json.dumps({'blurry_image': is_forged, 'ai_artifacts': is_ai_generated}),
            'AI_AUTO' if doc_status == 'PASSED' else 'MANUAL_REVIEW',
            'Suspicious document quality' if is_forged else None
        ))
        
        # Fraud rings share devices
        shared_device_pool = random.sample(all_devices, min(5, len(all_devices)))
        num_devices = random.randint(1, 4)
        user_devices_list = random.sample(shared_device_pool, min(num_devices, len(shared_device_pool)))
        
        for device_id in user_devices_list:
            first_used = created_at + timedelta(days=random.randint(0, 10))
            user_devices_data.append((
                user_id, device_id, first_used,
                datetime.now() - timedelta(days=random.randint(0, 10)),
                random.randint(2, 30)
            ))
        
        # Use VPN and sanctioned IPs
        num_ips = random.randint(5, 15)
        for _ in range(num_ips):
            if vpn_ips or sanctioned_ips:
                ip = random.choice(vpn_ips + sanctioned_ips) if random.random() < 0.7 else random.choice(normal_ips or [generate_ip()])
            else:
                ip = generate_ip()
            device = random.choice(user_devices_list) if user_devices_list else all_devices[0]
            accessed_at = created_at + timedelta(days=random.randint(0, 60))
            
            user_ip_history_data.append((
                user_id, ip, device, accessed_at,
                random.randint(60, 1800)
            ))

# Insert users
execute_values(cur, """
    INSERT INTO users (
        user_id, created_at, email, full_name, date_of_birth, nationality,
        declared_monthly_income, occupation, employment_status, source_of_funds,
        account_status, risk_level, kyc_status, kyc_verified_at,
        total_deposits, total_withdrawals, transaction_count, last_login_at
    ) VALUES %s
""", users_data)

print(f"✓ Inserted {len(users_data)} users ({NUM_LEGITIMATE_USERS} legitimate, {len(fraud_user_ids)} fraudulent)")

# Insert documents
execute_values(cur, """
    INSERT INTO document_verifications (
        user_id, submitted_at, document_type, document_number, issuing_country, expiry_date,
        verification_status, confidence_score, face_match_score, is_forged, is_ai_generated,
        is_expired, document_quality_score, flags, verified_by, notes
    ) VALUES %s
""", document_verifications_data)

print(f"✓ Inserted {len(document_verifications_data)} document verifications")

# Insert user-device mappings
execute_values(cur, """
    INSERT INTO user_devices (user_id, device_id, first_used_at, last_used_at, usage_count)
    VALUES %s
    ON CONFLICT (user_id, device_id) DO NOTHING
""", user_devices_data)

print(f"✓ Inserted {len(user_devices_data)} user-device mappings")

# Insert IP history
execute_values(cur, """
    INSERT INTO user_ip_history (user_id, ip_address, device_id, accessed_at, session_duration_seconds)
    VALUES %s
""", user_ip_history_data)

print(f"✓ Inserted {len(user_ip_history_data)} IP history records")

# =====================================================
# 5. GENERATE TRANSACTIONS
# =====================================================

print("Generating transactions...")
transactions_data = []

# Get all user IDs
cur.execute("SELECT user_id, declared_monthly_income, risk_level FROM users")
all_users = cur.fetchall()

for user_id, monthly_income, risk_level in all_users:
    monthly_income = float(monthly_income)
    is_fraud_user = risk_level == 'HIGH'
    num_transactions = random.randint(*TRANSACTIONS_PER_USER)
    
    # Get user's devices and IPs
    cur.execute("SELECT device_id FROM user_devices WHERE user_id = %s", (user_id,))
    user_devices = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT ip_address FROM user_ip_history WHERE user_id = %s", (user_id,))
    user_ips = [row[0] for row in cur.fetchall()]
    
    if not user_devices or not user_ips:
        continue
    
    for _ in range(num_transactions):
        # txn_id = f"TXN-{random.randint(1000000, 9999999)}"
        txn_id = f"TXN-{uuid.uuid4().hex}"
        txn_type = random.choice(['DEPOSIT', 'DEPOSIT', 'DEPOSIT', 'WITHDRAWAL', 'TRADE'])
        
        if is_fraud_user:
            # Fraudulent transaction patterns
            if txn_type == 'DEPOSIT':
                # Small deposits, way above declared income
                amount = random.uniform(monthly_income * 5, monthly_income * 20)
            else:
                # Large withdrawals
                amount = random.uniform(monthly_income * 10, monthly_income * 30)
        else:
            # Legitimate patterns
            if txn_type == 'DEPOSIT':
                amount = random.uniform(monthly_income * 0.1, monthly_income * 2)
            else:
                amount = random.uniform(monthly_income * 0.05, monthly_income * 1.5)
        
        created_at = datetime.now() - timedelta(days=random.randint(0, 90))
        
        transactions_data.append((
            txn_id,
            user_id,
            created_at,
            txn_type,
            round(amount, 2),
            'USD',
            random.choice(['BANK_TRANSFER', 'CREDIT_CARD', 'CRYPTO', 'E_WALLET']),
            fake.company(),
            random.choice(user_ips),
            random.choice(user_devices),
            random.choice(SAFE_COUNTRIES + HIGH_RISK_COUNTRIES),
            random.choice(['COMPLETED', 'COMPLETED', 'COMPLETED', 'FLAGGED']) if is_fraud_user else 'COMPLETED',
            created_at + timedelta(minutes=random.randint(1, 30)),
            is_fraud_user and random.random() < 0.5,  # velocity_flag
            is_fraud_user and random.random() < 0.6,  # amount_anomaly_flag
            is_fraud_user and random.random() < 0.4   # geographic_anomaly_flag
        ))

execute_values(cur, """
    INSERT INTO transactions (
        transaction_id, user_id, created_at, transaction_type, amount, currency,
        payment_method, payment_provider, ip_address, device_id, country_code,
        status, completed_at, velocity_flag, amount_anomaly_flag, geographic_anomaly_flag
    ) VALUES %s
""", transactions_data)

print(f"✓ Inserted {len(transactions_data)} transactions")

# Update user totals
cur.execute("""
    UPDATE users u SET
        total_deposits = COALESCE((
            SELECT SUM(amount) FROM transactions 
            WHERE user_id = u.user_id AND transaction_type = 'DEPOSIT' AND status = 'COMPLETED'
        ), 0),
        total_withdrawals = COALESCE((
            SELECT SUM(amount) FROM transactions 
            WHERE user_id = u.user_id AND transaction_type = 'WITHDRAWAL' AND status = 'COMPLETED'
        ), 0),
        transaction_count = COALESCE((
            SELECT COUNT(*) FROM transactions WHERE user_id = u.user_id
        ), 0)
""")

print("✓ Updated user transaction totals")

# =====================================================
# 6. GENERATE HISTORICAL FRAUD CASES
# =====================================================

print("Generating historical fraud cases...")
historical_cases_data = []

for user_id, fraud_ring_id in fraud_user_ids:
    case_id = f"CASE-{random.randint(100000, 999999)}"
    created_at = datetime.now() - timedelta(days=random.randint(7, 60))
    
    # Get user's transactions
    cur.execute("""
        SELECT transaction_id FROM transactions 
        WHERE user_id = %s AND (velocity_flag OR amount_anomaly_flag OR geographic_anomaly_flag)
        LIMIT 5
    """, (user_id,))
    involved_txns = [row[0] for row in cur.fetchall()]
    
    # Get devices and IPs
    cur.execute("SELECT device_id FROM user_devices WHERE user_id = %s", (user_id,))
    involved_devices = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT ip_address FROM user_ip_history WHERE user_id = %s", (user_id,))
    involved_ips = [row[0] for row in cur.fetchall()]
    
    # Get related users from same fraud ring
    cur.execute("SELECT user_id FROM users WHERE risk_level = 'HIGH' AND user_id != %s LIMIT 5", (user_id,))
    related_users = [row[0] for row in cur.fetchall()]
    
    fraud_type = random.choice([
        'MONEY_LAUNDERING', 'IDENTITY_FRAUD', 'ACCOUNT_TAKEOVER', 
        'SYNTHETIC_IDENTITY', 'PAYMENT_FRAUD'
    ])
    
    fraud_indicators = {
        'income_mismatch': random.random() < 0.8,
        'vpn_usage': random.random() < 0.7,
        'rapid_deposits': random.random() < 0.6,
        'document_issues': random.random() < 0.4,
        'shared_devices': len(involved_devices) > 2,
        'sanctioned_country_access': random.random() < 0.3
    }
    
    historical_cases_data.append((
        case_id,
        user_id,
        created_at,
        created_at + timedelta(days=random.randint(1, 14)),
        fraud_type,
        random.choice([True, False]),  # is_confirmed_fraud (some false positives)
        random.choice(['RULE_BASED', 'ML_MODEL', 'MANUAL_REVIEW']),
        random.uniform(0.70, 0.95),
        json.dumps(fraud_indicators),
        involved_txns,
        involved_devices,
        involved_ips,
        fraud_ring_id,
        related_users,
        random.uniform(5000, 50000),
        random.uniform(0, 10000),
        random.choice(['INV-001', 'INV-002', 'AI_AUTO']),
        'Flagged due to multiple suspicious signals',
        random.choice(['Confirmed fraud - account suspended', 'False positive - cleared after review', 'Under investigation'])
    ))

execute_values(cur, """
    INSERT INTO historical_fraud_cases (
        case_id, user_id, created_at, resolved_at, fraud_type, is_confirmed_fraud,
        detection_method, initial_confidence, fraud_indicators, involved_transactions,
        involved_devices, involved_ips, fraud_ring_id, related_user_ids,
        financial_loss, recovered_amount, investigated_by, investigation_notes, resolution_notes
    ) VALUES %s
""", historical_cases_data)

print(f"✓ Inserted {len(historical_cases_data)} historical fraud cases")

# =====================================================
# 7. GENERATE FRAUD PATTERNS
# =====================================================

print("Generating fraud patterns...")
patterns_data = []

pattern_templates = [
    {
        'name': 'Crypto Wallet Rapid Churn',
        'type': 'EMERGING_THREAT',
        'description': 'Users depositing via bank transfer, immediately converting to crypto, and withdrawing to external wallets within hours',
        'features': {'rapid_conversion': True, 'crypto_withdrawal': True, 'new_accounts': True},
        'severity': 'HIGH'
    },
    {
        'name': 'Coordinated Trading Cluster',
        'type': 'NETWORK_PATTERN',
        'description': 'Group of accounts executing identical trades within 60-second windows, suggesting bot coordination',
        'features': {'timing_correlation': 0.95, 'trade_similarity': 0.98, 'shared_ips': True},
        'severity': 'MEDIUM'
    },
    {
        'name': 'Document Verification Bypass',
        'type': 'IDENTITY_FRAUD',
        'description': 'Accounts passing automated KYC but showing AI-generated face artifacts on manual review',
        'features': {'low_face_match': True, 'metadata_missing': True, 'deepfake_indicators': True},
        'severity': 'CRITICAL'
    }
]

for i, template in enumerate(pattern_templates):
    pattern_id = f"PTN-{i+1:03d}"
    discovered_at = datetime.now() - timedelta(days=random.randint(1, 30))
    
    # Get sample user IDs
    cur.execute("SELECT user_id FROM users WHERE risk_level = 'HIGH' LIMIT 10")
    sample_users = [row[0] for row in cur.fetchall()]
    
    patterns_data.append((
        pattern_id,
        discovered_at,
        template['name'],
        template['type'],
        template['description'],
        len(sample_users),
        sample_users,
        json.dumps(template['features']),
        random.uniform(0.85, 0.99),
        template['severity'],
        random.uniform(0.75, 0.95),
        random.choice(['MONITORING', 'CONFIRMED']),
        random.choice(['AI_PATTERN_DETECTION', 'ANALYST_001']),
        discovered_at + timedelta(days=random.randint(1, 7))
    ))

execute_values(cur, """
    INSERT INTO fraud_patterns (
        pattern_id, discovered_at, pattern_name, pattern_type, description,
        affected_user_count, sample_user_ids, common_features, statistical_significance,
        severity, estimated_risk_score, status, confirmed_by, confirmed_at
    ) VALUES %s
""", patterns_data)
print(f"✓ Inserted {len(patterns_data)} fraud patterns")

# =====================================================
# 8. UPDATE DEVICE/IP USAGE COUNTS
# =====================================================
print("Updating device and IP usage statistics...")
# Update device usage counts
cur.execute("""
    UPDATE devices d SET
        total_users_count = (SELECT COUNT(DISTINCT user_id) FROM user_devices WHERE device_id = d.device_id),
        flagged_users_count = (SELECT COUNT(DISTINCT ud.user_id)
    FROM user_devices ud
    JOIN users u ON ud.user_id = u.user_id
    WHERE ud.device_id = d.device_id AND u.risk_level = 'HIGH')
""")

# Update IP usage counts
cur.execute("""
    UPDATE ip_addresses i SET
        total_users_count = (SELECT COUNT(DISTINCT user_id) FROM user_ip_history WHERE ip_address = i.ip_address),
        flagged_users_count = (SELECT COUNT(DISTINCT uih.user_id)
    FROM user_ip_history uih
    JOIN users u ON uih.user_id = u.user_id
    WHERE uih.ip_address = i.ip_address AND u.risk_level = 'HIGH')
""")
print("Updated usage statistics")

# =====================================================
# 9. ADD SANCTIONS LIST
# =====================================================
print("Generating sanctions list...")
sanctions_data = []
# Add sanctioned individuals
for _ in range(20):
    sanctions_data.append((
    'PERSON',
    fake.name(),
    [fake.name(), fake.name()],  # aliases
    fake.date_of_birth(minimum_age=30, maximum_age=70),
    random.choice(SANCTIONED_COUNTRIES),
    None,  # organization_name
    random.choice(['OFAC', 'UN', 'EU']),
    random.choice(['TERRORISM', 'DRUG_TRAFFICKING', 'MONEY_LAUNDERING']),
    fake.date_between(start_date='-5y', end_date='today'),
    'HIGH'
    ))
execute_values(cur, """
    INSERT INTO sanctions_list (
        entity_type, full_name, aliases, date_of_birth, nationality, organization_name,
        sanctioning_body, sanction_type, listed_date, risk_level
    ) VALUES %s
""", sanctions_data)
print(f"Inserted {len(sanctions_data)} sanctions records")

# =====================================================
# 9. Commit finalize
# =====================================================
conn.commit()
cur.close()
conn.close()
print("\n" + "="*60)
print("DATA GENERATION COMPLETE!")
print("="*60)
print(f"Total Users: {len(users_data)}")
print(f"  - Legitimate: {NUM_LEGITIMATE_USERS}")
print(f"  - Fraudulent: {len(fraud_user_ids)}")
print(f"Fraud Rings: {len(fraud_rings_data)}")
print(f"Devices: {len(devices_data)}")
print(f"IP Addresses: {len(ips_data)}")
print(f"Transactions: {len(transactions_data)}")
print(f"Historical Cases: {len(historical_cases_data)}")
print(f"Fraud Patterns: {len(patterns_data)}")
print("="*60)