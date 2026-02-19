"""
Database Service Layer for Historical Transaction Analysis
Provides real transaction history for velocity and pattern detection
"""

import asyncio
import asyncpg
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging


logger = logging.getLogger("FraudAIInvestigator")

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'frauddb',
    'user': 'user',
    'password': '123456',
    'min_size': 5,
    'max_size': 20
}

# =============================================================================
# DATABASE SERVICE
# =============================================================================

class FraudDatabaseService:
    """
    Async database service for fetching historical fraud data
    Provides transaction history, velocity metrics, and pattern analysis
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        logger.info("[DB] Database service initialized")
    
    async def connect(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(**DB_CONFIG)
            logger.info("[DB] Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"[DB] Connection failed: {e}")
            raise
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("[DB] Connection pool closed")
    
    # =========================================================================
    # USER TRANSACTION HISTORY
    # =========================================================================
    
    async def get_user_transaction_history(
        self, 
        user_id: str, 
        limit: int = 100,
        days: int = 90
    ) -> List[Dict]:
        """
        Get user's transaction history
        
        Returns list of transactions with full details
        """
        query = """
            SELECT 
                transaction_id,
                created_at,
                transaction_type,
                amount,
                currency,
                payment_method,
                payment_provider,
                ip_address,
                device_id,
                country_code,
                status,
                velocity_flag,
                amount_anomaly_flag,
                geographic_anomaly_flag
            FROM transactions
            WHERE user_id = $1
              AND created_at >= NOW() - INTERVAL '{} days'
            ORDER BY created_at DESC
            LIMIT $2
        """.format(days)
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit)
            return [dict(row) for row in rows]
    
    async def get_velocity_metrics(self, user_id: str) -> Dict:
        """
        Calculate real-time velocity metrics
        
        Returns comprehensive velocity analysis
        """
        query = """
            SELECT 
                -- Last 24 hours
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as txn_last_24h,
                SUM(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours' AND transaction_type = 'DEPOSIT') as deposits_last_24h,
                SUM(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours' AND transaction_type = 'WITHDRAWAL') as withdrawals_last_24h,
                
                -- Last 7 days
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as txn_last_7d,
                SUM(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days' AND transaction_type = 'DEPOSIT') as deposits_last_7d,
                
                -- Last 30 days
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as txn_last_30d,
                AVG(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as avg_amount_30d,
                STDDEV(amount) FILTER (WHERE created_at >= NOW() - INTERVAL '30 days') as stddev_amount_30d,
                
                -- All time
                COUNT(*) as total_transactions,
                SUM(amount) FILTER (WHERE transaction_type = 'DEPOSIT') as total_deposits,
                SUM(amount) FILTER (WHERE transaction_type = 'WITHDRAWAL') as total_withdrawals,
                MAX(created_at) as last_transaction_at
                
            FROM transactions
            WHERE user_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            
            if not row:
                return self._empty_velocity_metrics()
            
            return {
                'transactions_last_24h': row['txn_last_24h'] or 0,
                'deposits_last_24h': float(row['deposits_last_24h'] or 0),
                'withdrawals_last_24h': float(row['withdrawals_last_24h'] or 0),
                'transactions_last_7d': row['txn_last_7d'] or 0,
                'deposits_last_7d': float(row['deposits_last_7d'] or 0),
                'transactions_last_30d': row['txn_last_30d'] or 0,
                'avg_amount_30d': float(row['avg_amount_30d'] or 0),
                'stddev_amount_30d': float(row['stddev_amount_30d'] or 0),
                'total_transactions': row['total_transactions'] or 0,
                'total_deposits': float(row['total_deposits'] or 0),
                'total_withdrawals': float(row['total_withdrawals'] or 0),
                'last_transaction_at': row['last_transaction_at']
            }
    
    async def detect_rapid_escalation(self, user_id: str, current_amount: float) -> Dict:
        """
        Detect if current transaction shows rapid escalation pattern
        Compares current amount with recent transaction history
        """
        query = """
            SELECT 
                amount,
                created_at,
                transaction_type
            FROM transactions
            WHERE user_id = $1
              AND created_at >= NOW() - INTERVAL '7 days'
            ORDER BY created_at ASC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            
            if len(rows) < 2:
                return {'is_escalating': False, 'escalation_ratio': 0}
            
            amounts = [float(row['amount']) for row in rows]
            amounts.append(current_amount)
            
            # Check if amounts are increasing rapidly
            is_escalating = all(amounts[i] < amounts[i+1] * 0.8 for i in range(len(amounts)-1))
            escalation_ratio = current_amount / amounts[0] if amounts[0] > 0 else 0
            
            return {
                'is_escalating': is_escalating,
                'escalation_ratio': escalation_ratio,
                'previous_amounts': amounts[:-1],
                'transaction_count': len(amounts) - 1
            }
    
    async def detect_structuring(self, user_id: str, current_amount: float) -> Dict:
        """
        Detect structuring (multiple transactions just below threshold)
        Common fraud pattern to avoid reporting
        """
        query = """
            SELECT 
                COUNT(*) as count,
                SUM(amount) as total_amount
            FROM transactions
            WHERE user_id = $1
              AND created_at >= NOW() - INTERVAL '48 hours'
              AND amount BETWEEN 9500 AND 9999
              AND transaction_type = 'DEPOSIT'
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            
            count = row['count'] or 0
            total = float(row['total_amount'] or 0)
            
            # Structuring detected if 3+ transactions just below $10k
            is_structuring = count >= 3 and 9500 <= current_amount <= 9999
            
            return {
                'is_structuring': is_structuring,
                'similar_transactions_48h': count,
                'total_amount_48h': total,
                'avg_amount': total / count if count > 0 else 0
            }
    
    # =========================================================================
    # DEVICE & IP HISTORY
    # =========================================================================
    
    async def get_device_history(self, device_id: str) -> Dict:
        """Get historical data for a device"""
        query = """
            SELECT 
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT ip_address) as unique_ips,
                COUNT(*) as total_transactions,
                SUM(CASE WHEN velocity_flag OR amount_anomaly_flag THEN 1 ELSE 0 END) as flagged_transactions
            FROM transactions
            WHERE device_id = $1
              AND created_at >= NOW() - INTERVAL '90 days'
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, device_id)
            
            return {
                'unique_users': row['unique_users'] or 0,
                'unique_ips': row['unique_ips'] or 0,
                'total_transactions': row['total_transactions'] or 0,
                'flagged_transactions': row['flagged_transactions'] or 0,
                'flag_rate': (row['flagged_transactions'] or 0) / max(row['total_transactions'] or 1, 1)
            }
    
    async def get_ip_history(self, ip_address: str) -> Dict:
        """Get historical data for an IP address"""
        query = """
            SELECT 
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT device_id) as unique_devices,
                COUNT(*) as total_transactions,
                SUM(CASE WHEN velocity_flag OR amount_anomaly_flag THEN 1 ELSE 0 END) as flagged_transactions,
                MAX(created_at) as last_seen
            FROM transactions
            WHERE ip_address = $1
              AND created_at >= NOW() - INTERVAL '90 days'
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, ip_address)
            
            return {
                'unique_users': row['unique_users'] or 0,
                'unique_devices': row['unique_devices'] or 0,
                'total_transactions': row['total_transactions'] or 0,
                'flagged_transactions': row['flagged_transactions'] or 0,
                'flag_rate': (row['flagged_transactions'] or 0) / max(row['total_transactions'] or 1, 1),
                'last_seen': row['last_seen']
            }
    
    # =========================================================================
    # FRAUD RING DETECTION
    # =========================================================================
    
    async def find_connected_users(
        self, 
        user_id: str, 
        device_id: str, 
        ip_address: str
    ) -> Dict:
        """
        Find users connected through shared devices or IPs
        Critical for fraud ring detection
        """
        query = """
            WITH user_connections AS (
                -- Users sharing the same device
                SELECT DISTINCT 
                    t2.user_id,
                    'shared_device' as connection_type,
                    COUNT(*) OVER (PARTITION BY t2.user_id) as connection_strength
                FROM transactions t1
                JOIN transactions t2 ON t1.device_id = t2.device_id
                WHERE t1.user_id = $1
                  AND t2.user_id != $1
                  AND t2.created_at >= NOW() - INTERVAL '90 days'
                
                UNION ALL
                
                -- Users sharing the same IP
                SELECT DISTINCT 
                    t2.user_id,
                    'shared_ip' as connection_type,
                    COUNT(*) OVER (PARTITION BY t2.user_id) as connection_strength
                FROM transactions t1
                JOIN transactions t2 ON t1.ip_address = t2.ip_address
                WHERE t1.user_id = $1
                  AND t2.user_id != $1
                  AND t2.created_at >= NOW() - INTERVAL '90 days'
            )
            SELECT 
                user_id,
                ARRAY_AGG(DISTINCT connection_type) as connection_types,
                SUM(connection_strength) as total_strength
            FROM user_connections
            GROUP BY user_id
            ORDER BY total_strength DESC
            LIMIT 20
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            
            connected_users = []
            for row in rows:
                connected_users.append({
                    'user_id': row['user_id'],
                    'connection_types': row['connection_types'],
                    'connection_strength': row['total_strength']
                })
            
            # Check if any connected users are already flagged
            if connected_users:
                flagged_query = """
                    SELECT user_id, risk_level
                    FROM users
                    WHERE user_id = ANY($1)
                      AND risk_level IN ('HIGH', 'MEDIUM')
                """
                
                user_ids = [u['user_id'] for u in connected_users]
                flagged_rows = await conn.fetch(flagged_query, user_ids)
                
                flagged_map = {row['user_id']: row['risk_level'] for row in flagged_rows}
                
                for user in connected_users:
                    user['risk_level'] = flagged_map.get(user['user_id'], 'LOW')
            
            return {
                'connected_user_count': len(connected_users),
                'connected_users': connected_users,
                'high_risk_connections': len([u for u in connected_users if u.get('risk_level') == 'HIGH'])
            }
    
    async def check_coordinated_timing(self, user_ids: List[str]) -> Dict:
        """
        Check if multiple users have coordinated transaction timing
        Fraud rings often transact at similar times
        """
        if len(user_ids) < 2:
            return {'is_coordinated': False}
        
        query = """
            SELECT 
                user_id,
                DATE_TRUNC('hour', created_at) as hour_bucket,
                COUNT(*) as txn_count
            FROM transactions
            WHERE user_id = ANY($1)
              AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY user_id, hour_bucket
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_ids)
            
            # Group by hour bucket
            hour_buckets = defaultdict(set)
            for row in rows:
                hour_buckets[row['hour_bucket']].add(row['user_id'])
            
            # Check if multiple users transacted in same hour bucket
            coordinated_hours = [
                bucket for bucket, users in hour_buckets.items() 
                if len(users) >= min(3, len(user_ids))
            ]
            
            return {
                'is_coordinated': len(coordinated_hours) > 0,
                'coordinated_time_windows': len(coordinated_hours),
                'suspected_ring_size': len(user_ids)
            }
    
    # =========================================================================
    # HISTORICAL FRAUD CASES
    # =========================================================================
    
    async def get_user_fraud_history(self, user_id: str) -> Dict:
        """Get user's fraud case history"""
        query = """
            SELECT 
                COUNT(*) as total_cases,
                SUM(CASE WHEN is_confirmed_fraud THEN 1 ELSE 0 END) as confirmed_fraud_cases,
                MAX(created_at) as last_case_at,
                ARRAY_AGG(fraud_type) FILTER (WHERE is_confirmed_fraud) as fraud_types
            FROM historical_fraud_cases
            WHERE user_id = $1
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            
            return {
                'total_cases': row['total_cases'] or 0,
                'confirmed_fraud_cases': row['confirmed_fraud_cases'] or 0,
                'has_fraud_history': (row['confirmed_fraud_cases'] or 0) > 0,
                'last_case_at': row['last_case_at'],
                'fraud_types': row['fraud_types'] or []
            }
    
    async def check_similar_patterns(self, user_id: str, features: Dict) -> List[Dict]:
        """
        Find similar fraud patterns from historical cases
        Uses feature similarity matching
        """
        # Simplified version - in production would use vector similarity
        query = """
            SELECT 
                pattern_id,
                pattern_name,
                pattern_type,
                description,
                estimated_risk_score
            FROM fraud_patterns
            WHERE status = 'CONFIRMED'
              AND $1 = ANY(sample_user_ids)
            ORDER BY estimated_risk_score DESC
            LIMIT 5
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _empty_velocity_metrics(self) -> Dict:
        """Return empty velocity metrics for new users"""
        return {
            'transactions_last_24h': 0,
            'deposits_last_24h': 0,
            'withdrawals_last_24h': 0,
            'transactions_last_7d': 0,
            'deposits_last_7d': 0,
            'transactions_last_30d': 0,
            'avg_amount_30d': 0,
            'stddev_amount_30d': 0,
            'total_transactions': 0,
            'total_deposits': 0,
            'total_withdrawals': 0,
            'last_transaction_at': None
        }

# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global database service instance
db_service: Optional[FraudDatabaseService] = None

async def get_db_service() -> FraudDatabaseService:
    """Get or create database service singleton"""
    global db_service
    
    if db_service is None:
        db_service = FraudDatabaseService()
        await db_service.connect()
    
    return db_service

async def close_db_service():
    """Close database service"""
    global db_service
    
    if db_service is not None:
        await db_service.close()
        db_service = None