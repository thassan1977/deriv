"""
Transaction Stream Publisher
Publishes fake transactions from PostgreSQL to Redis Stream for fraud detection
"""

import psycopg2
import redis
import json
import time
import random
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("TransactionPublisher")

# =====================================================
# Configuration
# =====================================================
POSTGRES_CONFIG = {
    'dbname': 'frauddb',
    'user': 'user',
    'password': '123456',
    'host': 'localhost',
    'port': '5432'
}

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'username': 'default',
    'password': 'eYVX7EwVmmxKPCDmwMtyKVge8oLd2t81',
}

STREAM_KEY = "deriv:transactions"
BATCH_SIZE = 100  # Transactions per batch
BATCH_INTERVAL = 5  # Seconds between batches
MAX_LENGTH_QUEUE = 100  # Max transactions in redis stream (no explode)
# =====================================================
# Connect to databases
# =====================================================
pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
pg_cur = pg_conn.cursor()

redis_client = redis.Redis(**REDIS_CONFIG)

logger.info(" Connected to PostgreSQL and Redis")


def build_transaction_event(txn_row, user_row, ip_row, device_row, doc_row):
    """
    Build complete transaction event matching the Java TransactionEvent format
    """
    txn_id, user_id, created_at, txn_type, amount, currency, payment_method, \
        payment_provider, ip_address, device_id, country_code, status, \
        completed_at, velocity_flag, amount_flag, geo_flag = txn_row
    
    user_id_u, created_at_u, email, full_name, dob, nationality, \
        monthly_income, occupation, employment_status, source_of_funds, \
        account_status, risk_level, kyc_status, kyc_verified_at, \
        total_deposits, total_withdrawals, txn_count, last_login = user_row
    
    # IP profile
    ip_addr, first_seen_ip, last_seen_ip, country_code_ip, country_name, \
        city, region, lat, lon, isp, org, asn, is_vpn, is_proxy, is_tor, \
        is_datacenter, is_anonymous, is_sanctioned, is_high_risk, \
        risk_score_ip, total_users_ip, flagged_users_ip = ip_row
    
    # Device profile
    device_id_d, first_seen_dev, last_seen_dev, device_type, os, browser, \
        browser_version, user_agent, screen_res, timezone, language, \
        is_emulator, is_vpn_dev, is_proxy_dev, is_tor_dev, \
        total_users_dev, flagged_users_dev = device_row
    
    verification_status = None 
    confidence_score = 0.5 
    face_match_score = 0.0 
    quality_score = 0.0 
    forged = False 
    ai_generated = False 
    expired = False

    # Document profile (may be None)
    doc_confidence = 0.5
    if doc_row:
        verification_status = str(doc_row[6]) if doc_row[6] else None 
        try: 
            confidence_score = float(doc_row[7]) if doc_row[7] else 0.5 
        except (ValueError, TypeError): 
            confidence_score = 1.0 if str(doc_row[7]).upper() == "PASSED" else 0.0 
        face_match_score = float(doc_row[8]) if doc_row[8] else 0.0 
        quality_score = float(doc_row[9]) if doc_row[9] else 0.0 
        forged = bool(doc_row[10]) 
        ai_generated = bool(doc_row[11]) 
        expired = bool(doc_row[12])
    
    event = {
        "transactionId": txn_id,
        "userId": user_id,
        "timestamp": created_at.isoformat() if created_at else datetime.now().isoformat(),
        "transactionType": txn_type,
        "amount": float(amount) if amount else 0.0,
        "currency": currency,
        "paymentMethod": payment_method,
        "paymentProvider": payment_provider,
        "ipAddress": ip_address,
        "deviceId": device_id,
        "countryCode": country_code,
        
        # User Profile
        "userProfile": {
            "userId": user_id,
            "email": email,
            "fullName": full_name,
            "declaredMonthlyIncome": float(monthly_income) if monthly_income else 0.0,
            "occupation": occupation,
            "employmentStatus": employment_status,
            "sourceOfFunds": source_of_funds,
            "accountStatus": account_status,
            "riskLevel": risk_level,
            "kycStatus": kyc_status,
            "createdAt": created_at_u.isoformat() if created_at_u else datetime.now().isoformat(),
            "totalDevices": total_users_dev if total_users_dev else 1,
            "totalDeposits": float(total_deposits) if total_deposits else 0.0,
            "totalWithdrawals": float(total_withdrawals) if total_withdrawals else 0.0,
            "transactionCount": txn_count if txn_count else 0,
            "accountCreatedAt": created_at_u.isoformat() if created_at_u else datetime.now().isoformat()
        },
        
        # IP Profile
        "ipProfile": {
            "ipAddress": ip_address,
            "countryCode": country_code_ip,
            "countryName": country_name,
            "city": city,
            "region": region,
            "latitude": float(lat) if lat else 0.0,
            "longitude": float(lon) if lon else 0.0,
            "isp": isp,
            "organization": org,
            "asn": asn,
            "vpn": bool(is_vpn),
            "proxy": bool(is_proxy),
            "tor": bool(is_tor),
            "datacenter": bool(is_datacenter),
            "anonymous": bool(is_anonymous),
            "sanctionedCountry": bool(is_sanctioned),
            "highRiskCountry": bool(is_high_risk),
            "riskScore": float(risk_score_ip) if risk_score_ip else 0.0,
            "totalUsers": total_users_ip if total_users_ip else 1,
            "flaggedUsers": flagged_users_ip if flagged_users_ip else 0
        },
        
        # Device Profile
        "deviceProfile": {
            "deviceId": device_id,
            "deviceType": device_type,
            "os": os,
            "browser": browser,
            "browserVersion": browser_version,
            "userAgent": user_agent,
            "screenResolution": screen_res,
            "timezone": timezone,
            "language": language,
            "emulator": bool(is_emulator),
            "vpn": bool(is_vpn_dev),
            "proxy": bool(is_proxy_dev),
            "tor": bool(is_tor_dev),
            "totalUsersCount": total_users_dev if total_users_dev else 1,
            "flaggedUsersCount": flagged_users_dev if flagged_users_dev else 0
        },
        
        # Document Profile
        "documentProfile": { 
            "verificationStatus": verification_status, 
            "confidenceScore": confidence_score, 
            "faceMatchScore": face_match_score, 
            "documentQualityScore": quality_score, 
            "forged": forged, 
            "aiGenerated": ai_generated, 
            "expired": expired,
        },
        # Transaction flags
        "flags": {
            "velocityFlag": bool(velocity_flag),
            "amountAnomalyFlag": bool(amount_flag),
            "geographicAnomalyFlag": bool(geo_flag)
        }
    }
    
    return event

# =====================================================
# Publish transactions to Redis Stream
# =====================================================
def publish_transactions(limit=None, fraud_only=False):
    """
    Publish transactions from PostgreSQL to Redis Stream
    
    Args:
        limit: Maximum number of transactions to publish (None = all)
        fraud_only: If True, only publish transactions from high-risk users
    """
    
    # Build query
    where_clause = "WHERE u.risk_level = 'HIGH'" if fraud_only else ""
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    query = f"""
        SELECT 
            t.transaction_id, t.user_id, t.created_at, t.transaction_type, 
            t.amount, t.currency, t.payment_method, t.payment_provider,
            t.ip_address, t.device_id, t.country_code, t.status, t.completed_at,
            t.velocity_flag, t.amount_anomaly_flag, t.geographic_anomaly_flag,
            
            -- User data
            u.user_id, u.created_at, u.email, u.full_name, u.date_of_birth,
            u.nationality, u.declared_monthly_income, u.occupation, 
            u.employment_status, u.source_of_funds, u.account_status,
            u.risk_level, u.kyc_status, u.kyc_verified_at,
            u.total_deposits, u.total_withdrawals, u.transaction_count, u.last_login_at,
            
            -- IP data
            ip.ip_address, ip.first_seen_at, ip.last_seen_at, ip.country_code,
            ip.country_name, ip.city, ip.region, ip.latitude, ip.longitude,
            ip.isp, ip.organization, ip.asn, ip.is_vpn, ip.is_proxy, ip.is_tor,
            ip.is_datacenter, ip.is_anonymous, ip.is_sanctioned_country,
            ip.is_high_risk_country, ip.risk_score, ip.total_users_count, ip.flagged_users_count,
            
            -- Device data
            d.device_id, d.first_seen_at, d.last_seen_at, d.device_type, d.os,
            d.browser, d.browser_version, d.user_agent, d.screen_resolution,
            d.timezone, d.language, d.is_emulator, d.is_vpn, d.is_proxy, d.is_tor,
            d.total_users_count, d.flagged_users_count
            
        FROM transactions t
        JOIN users u ON t.user_id = u.user_id
        LEFT JOIN ip_addresses ip ON t.ip_address = ip.ip_address
        LEFT JOIN devices d ON t.device_id = d.device_id
        {where_clause}
        ORDER BY t.created_at DESC
        {limit_clause}
    """
    
    pg_cur.execute(query)
    rows = pg_cur.fetchall()
    
    logger.info(f" Found {len(rows)} transactions to publish")
    
    published = 0
    errors = 0
    
    for row in rows:
        try:
            # Split row into components
            txn_data = row[0:16]
            user_data = row[16:34]
            ip_data = row[34:56]
            device_data = row[56:73]
            
            # Get document verification
            pg_cur.execute("""
                SELECT * FROM document_verifications 
                WHERE user_id = %s 
                ORDER BY submitted_at DESC 
                LIMIT 1
            """, (txn_data[1],))
            doc_data = pg_cur.fetchone()
            
            # Build event
            event = build_transaction_event(txn_data, user_data, ip_data, device_data, doc_data)
            
            # Publish to Redis Stream
            event_json = json.dumps(event)
            msg_id = redis_client.xadd(
                STREAM_KEY,
                {'event_data': event_json},
            )
            logger.info(f"Published transaction {event_json} with Redis ID {msg_id}")
            published += 1
            
            if published % 100 == 0:
                logger.info(f" Published {published} transactions...")
            
        except Exception as e:
            logger.error(f" Error publishing transaction {row[0]}: {e}")
            errors += 1
    
    logger.info(f" Published {published} transactions ({errors} errors)")
    return published

# =====================================================
# Continuous streaming mode
# =====================================================
def stream_continuously():
    """
    Continuously publish transactions in batches
    Simulates real-time transaction stream
    """
    logger.info(" Starting continuous transaction stream...")
    logger.info(f"Publishing {BATCH_SIZE} transactions every {BATCH_INTERVAL} seconds")
    
    # Track published transactions
    pg_cur.execute("SELECT COUNT(*) FROM transactions")
    total_txns = pg_cur.fetchone()[0]
    
    published_ids = set()
    
    while True:
        try:
            # Get unpublished transactions
            pg_cur.execute(f"""
                SELECT transaction_id FROM transactions 
                WHERE transaction_id NOT IN %s
                ORDER BY RANDOM()
                LIMIT {BATCH_SIZE}
            """, (tuple(published_ids) if published_ids else ('',),))
            
            batch_ids = [row[0] for row in pg_cur.fetchall()]
            
            if not batch_ids:
                logger.info(" No more unpublished transactions, resetting...")
                published_ids.clear()
                time.sleep(BATCH_INTERVAL)
                continue
            
            # Publish this batch
            for txn_id in batch_ids:
                pg_cur.execute("""
                    SELECT 
                        t.transaction_id, t.user_id, t.created_at, t.transaction_type, 
                        t.amount, t.currency, t.payment_method, t.payment_provider,
                        t.ip_address, t.device_id, t.country_code, t.status, t.completed_at,
                        t.velocity_flag, t.amount_anomaly_flag, t.geographic_anomaly_flag,
                        
                        u.user_id, u.created_at, u.email, u.full_name, u.date_of_birth,
                        u.nationality, u.declared_monthly_income, u.occupation, 
                        u.employment_status, u.source_of_funds, u.account_status,
                        u.risk_level, u.kyc_status, u.kyc_verified_at,
                        u.total_deposits, u.total_withdrawals, u.transaction_count, u.last_login_at,
                        
                        ip.ip_address, ip.first_seen_at, ip.last_seen_at, ip.country_code,
                        ip.country_name, ip.city, ip.region, ip.latitude, ip.longitude,
                        ip.isp, ip.organization, ip.asn, ip.is_vpn, ip.is_proxy, ip.is_tor,
                        ip.is_datacenter, ip.is_anonymous, ip.is_sanctioned_country,
                        ip.is_high_risk_country, ip.risk_score, ip.total_users_count, ip.flagged_users_count,
                        
                        d.device_id, d.first_seen_at, d.last_seen_at, d.device_type, d.os,
                        d.browser, d.browser_version, d.user_agent, d.screen_resolution,
                        d.timezone, d.language, d.is_emulator, d.is_vpn, d.is_proxy, d.is_tor,
                        d.total_users_count, d.flagged_users_count
                        
                    FROM transactions t
                    JOIN users u ON t.user_id = u.user_id
                    LEFT JOIN ip_addresses ip ON t.ip_address = ip.ip_address
                    LEFT JOIN devices d ON t.device_id = d.device_id
                    WHERE t.transaction_id = %s
                """, (txn_id,))
                
                row = pg_cur.fetchone()
                if not row:
                    continue
                
                txn_data = row[0:16]
                user_data = row[16:34]
                ip_data = row[34:56]
                device_data = row[56:73]
                
                pg_cur.execute("""
                    SELECT * FROM document_verifications 
                    WHERE user_id = %s 
                    ORDER BY submitted_at DESC 
                    LIMIT 1
                """, (txn_data[1],))
                doc_data = pg_cur.fetchone()
                
                event = build_transaction_event(txn_data, user_data, ip_data, device_data, doc_data)
                event_json = json.dumps(event)
                
                redis_client.xadd(STREAM_KEY, {'event_data': event_json})
                published_ids.add(txn_id)
            
            logger.info(f"Published batch of {len(batch_ids)} transactions (Total: {len(published_ids)}/{total_txns})")
            
            time.sleep(BATCH_INTERVAL)
            
        except KeyboardInterrupt:
            logger.info("\n Stopping stream...")
            break
        except Exception as e:
            logger.error(f" Error in streaming: {e}")
            time.sleep(BATCH_INTERVAL)

# =====================================================
# Main
# =====================================================
if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("TRANSACTION STREAM PUBLISHER")
    print("="*70)
    print("\nOptions:")
    print("1. Publish all transactions once")
    print("2. Publish fraud transactions only")
    print("3. Stream continuously (simulates real-time)")
    print("4. Publish specific number of transactions")
    print("="*70)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = input("\nSelect mode (1-4): ").strip()
    
    try:
        if mode == "1":
            publish_transactions()
        elif mode == "2":
            publish_transactions(fraud_only=True)
        elif mode == "3":
            stream_continuously()
        elif mode == "4":
            limit = int(input("How many transactions? "))
            publish_transactions(limit=limit)
        else:
            print("Invalid mode selected")
    except KeyboardInterrupt:
        print("\n\n Stopped by user")
    finally:
        pg_cur.close()
        pg_conn.close()
        redis_client.close()
        print("\n Connections closed")