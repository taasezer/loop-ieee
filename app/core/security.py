"""
LOOP Lojistik Platformu - Gelişmiş Güvenlik Sistemi
Authentication, authorization, auditing ve threat detection
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from enum import Enum
from loguru import logger
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import secrets
import re
from ipaddress import ip_address, IPv4Address

from core.config import settings
from models.user import User, UserRole


class SecurityLevel(Enum):
    """Güvenlik seviyeleri"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditAction(Enum):
    """Audit aksiyon tipleri"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    DOWNLOAD = "download"
    UPLOAD = "upload"
    SUSPICIOUS = "suspicious"
    BLOCKED = "blocked"


@dataclass
class SecurityEvent:
    """Güvenlik olayı"""
    timestamp: datetime
    user_id: Optional[str]
    ip_address: str
    action: str
    resource: str
    details: Dict[str, Any]
    risk_score: float
    security_level: SecurityLevel


@dataclass
class RateLimitConfig:
    """Rate limit konfigürasyonu"""
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    window_size: int  # Saniye


@dataclass
class SecurityPolicy:
    """Güvenlik politikası"""
    password_min_length: int = 8
    password_complexity: bool = True
    session_timeout: int = 1800  # Saniye
    max_failed_attempts: int = 5
    lockout_duration: int = 3600  # Saniye
    require_2fa: bool = False
    ip_whitelist: List[str] = None
    ip_blacklist: List[str] = None
    rate_limit: RateLimitConfig = None


class SecurityManager:
    """Gelişmiş güvenlik yöneticisi"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security_bearer = HTTPBearer()
        
        # Güvenlik politikaları
        self.policies = {
            'default': SecurityPolicy(),
            'admin': SecurityPolicy(
                password_min_length=12,
                require_2fa=True,
                rate_limit=RateLimitConfig(
                    requests_per_minute=1000,
                    requests_per_hour=10000,
                    burst_limit=100,
                    window_size=60
                )
            ),
            'courier': SecurityPolicy(
                session_timeout=7200,  # 2 saat
                rate_limit=RateLimitConfig(
                    requests_per_minute=300,
                    requests_per_hour=3000,
                    burst_limit=50,
                    window_size=60
                )
            ),
            'customer': SecurityPolicy(
                rate_limit=RateLimitConfig(
                    requests_per_minute=100,
                    requests_per_hour=1000,
                    burst_limit=20,
                    window_size=60
                )
            )
        }
        
        # Geçici storage (Redis ile değiştirilecek)
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.locked_accounts: Dict[str, datetime] = {}
        self.active_sessions: Dict[str, Dict] = {}
        self.security_events: List[SecurityEvent] = []
        self.rate_limit_cache: Dict[str, List[datetime]] = {}
        self.suspicious_ips: Dict[str, int] = {}
    
    # Password Management
    def hash_password(self, password: str) -> str:
        """Şifreyi hash'le"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Şifreyi doğrula"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password(self, password: str, policy: SecurityPolicy = None) -> Dict[str, Any]:
        """Şifre gücünü doğrula"""
        policy = policy or self.policies['default']
        errors = []
        score = 0
        
        # Uzunluk kontrolü
        if len(password) < policy.password_min_length:
            errors.append(f"Şifre en az {policy.password_min_length} karakter olmalı")
        else:
            score += 1
        
        # Karmaşıklık kontrolü
        if policy.password_complexity:
            if not re.search(r'[a-z]', password):
                errors.append("Şifre küçük harf içermeli")
            else:
                score += 1
                
            if not re.search(r'[A-Z]', password):
                errors.append("Şifre büyük harf içermeli")
            else:
                score += 1
                
            if not re.search(r'[0-9]', password):
                errors.append("Şifre sayı içermeli")
            else:
                score += 1
                
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append("Şifre özel karakter içermeli")
            else:
                score += 1
        
        # Yaygın şifre kontrolü
        common_passwords = ['123456', 'password', 'admin', 'loop123']
        if password.lower() in common_passwords:
            errors.append("Yaygın şifreler kullanılamaz")
        else:
            score += 1
        
        # Puanlama
        strength = "weak"
        if score >= 4:
            strength = "strong"
        elif score >= 2:
            strength = "medium"
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': strength,
            'score': score
        }
    
    # JWT Token Management
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Access token oluştur"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Refresh token oluştur"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Token'ı doğrula"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Token tipi kontrolü
            if payload.get("type") != token_type:
                return None
            
            # Expiration kontrolü
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                return None
            
            return payload
            
        except JWTError:
            return None
    
    # Session Management
    def create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """Oturum oluştur"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        self.active_sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str) -> bool:
        """Oturumu doğrula"""
        if session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        
        # IP kontrolü
        if session_data["ip_address"] != ip_address:
            self._log_security_event(
                user_id=session_data["user_id"],
                ip_address=ip_address,
                action="session_ip_mismatch",
                details={"session_ip": session_data["ip_address"]}
            )
            return False
        
        # Timeout kontrolü
        policy = self.policies.get('default')
        if datetime.utcnow() - session_data["last_activity"] > timedelta(seconds=policy.session_timeout):
            self.invalidate_session(session_id)
            return False
        
        # Son aktiviteyi güncelle
        session_data["last_activity"] = datetime.utcnow()
        return True
    
    def invalidate_session(self, session_id: str):
        """Oturumu geçersiz kıl"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    # Rate Limiting
    def check_rate_limit(self, identifier: str, policy: SecurityPolicy) -> bool:
        """Rate limit kontrolü"""
        if not policy.rate_limit:
            return True
        
        now = datetime.utcnow()
        
        # Rate limit cache'i temizle
        if identifier not in self.rate_limit_cache:
            self.rate_limit_cache[identifier] = []
        
        # Eski kayıtları temizle
        self.rate_limit_cache[identifier] = [
            timestamp for timestamp in self.rate_limit_cache[identifier]
            if now - timestamp < timedelta(minutes=60)
        ]
        
        # Dakika kontrolü
        minute_requests = [
            timestamp for timestamp in self.rate_limit_cache[identifier]
            if now - timestamp < timedelta(minutes=1)
        ]
        
        if len(minute_requests) >= policy.rate_limit.requests_per_minute:
            return False
        
        # Saat kontrolü
        hour_requests = [
            timestamp for timestamp in self.rate_limit_cache[identifier]
            if now - timestamp < timedelta(hours=1)
        ]
        
        if len(hour_requests) >= policy.rate_limit.requests_per_hour:
            return False
        
        # Burst kontrolü
        window_requests = [
            timestamp for timestamp in self.rate_limit_cache[identifier]
            if now - timestamp < timedelta(seconds=policy.rate_limit.window_size)
        ]
        
        if len(window_requests) >= policy.rate_limit.burst_limit:
            return False
        
        # Kaydı ekle
        self.rate_limit_cache[identifier].append(now)
        return True
    
    # IP Management
    def is_ip_allowed(self, ip_address: str, policy: SecurityPolicy) -> bool:
        """IP adresine izin verilip verilmediğini kontrol et"""
        # Blacklist kontrolü
        if policy.ip_blacklist:
            for blocked_ip in policy.ip_blacklist:
                if self._ip_matches(ip_address, blocked_ip):
                    return False
        
        # Whitelist kontrolü
        if policy.ip_whitelist:
            for allowed_ip in policy.ip_whitelist:
                if self._ip_matches(ip_address, allowed_ip):
                    return True
            return False  # Whitelist varsa sadece listedekiler izinli
        
        return True
    
    def _ip_matches(self, ip: str, pattern: str) -> bool:
        """IP adresinin pattern ile eşleşip eşleşmediğini kontrol et"""
        try:
            if '/' in pattern:  # CIDR notation
                from ipaddress import ip_network
                return ip_address(ip) in ip_network(pattern)
            elif pattern.endswith('*'):  # Wildcard
                return ip.startswith(pattern[:-1])
            else:  # Exact match
                return ip == pattern
        except Exception:
            return False
    
    # Failed Login Attempts
    def record_failed_attempt(self, identifier: str):
        """Başarısız giriş denemesini kaydet"""
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(datetime.utcnow())
        
        # Eski kayıtları temizle (son 1 saat)
        self.failed_attempts[identifier] = [
            timestamp for timestamp in self.failed_attempts[identifier]
            if datetime.utcnow() - timestamp < timedelta(hours=1)
        ]
        
        # Lockout kontrolü
        policy = self.policies.get('default')
        if len(self.failed_attempts[identifier]) >= policy.max_failed_attempts:
            self.locked_accounts[identifier] = datetime.utcnow()
            
            self._log_security_event(
                user_id=identifier,
                ip_address="unknown",
                action="account_locked",
                details={"failed_attempts": len(self.failed_attempts[identifier])},
                security_level=SecurityLevel.HIGH
            )
    
    def is_account_locked(self, identifier: str) -> bool:
        """Hesap kilitli mi?"""
        if identifier not in self.locked_accounts:
            return False
        
        policy = self.policies.get('default')
        lockout_time = self.locked_accounts[identifier]
        
        if datetime.utcnow() - lockout_time > timedelta(seconds=policy.lockout_duration):
            # Kilitleme süresi doldu
            del self.locked_accounts[identifier]
            return False
        
        return True
    
    # Security Event Logging
    def _log_security_event(
        self,
        user_id: Optional[str],
        ip_address: str,
        action: str,
        resource: str = "",
        details: Dict[str, Any] = None,
        security_level: SecurityLevel = SecurityLevel.MEDIUM
    ):
        """Güvenlik olayını logla"""
        event = SecurityEvent(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            ip_address=ip_address,
            action=action,
            resource=resource,
            details=details or {},
            risk_score=self._calculate_risk_score(action, details),
            security_level=security_level
        )
        
        self.security_events.append(event)
        
        # Log seviyesine göre logla
        if security_level == SecurityLevel.CRITICAL:
            logger.critical(f"Security Event: {event}")
        elif security_level == SecurityLevel.HIGH:
            logger.error(f"Security Event: {event}")
        elif security_level == SecurityLevel.MEDIUM:
            logger.warning(f"Security Event: {event}")
        else:
            logger.info(f"Security Event: {event}")
    
    def _calculate_risk_score(self, action: str, details: Dict[str, Any]) -> float:
        """Risk skoru hesapla"""
        base_scores = {
            AuditAction.LOGIN.value: 1.0,
            AuditAction.LOGOUT.value: 0.5,
            AuditAction.CREATE.value: 2.0,
            AuditAction.UPDATE.value: 1.5,
            AuditAction.DELETE.value: 3.0,
            AuditAction.SUSPICIOUS.value: 5.0,
            AuditAction.BLOCKED.value: 8.0
        }
        
        score = base_scores.get(action, 2.0)
        
        # Ek faktörler
        if details:
            if details.get('failed_attempts', 0) > 3:
                score *= 2.0
            
            if details.get('ip_mismatch', False):
                score *= 1.5
            
            if details.get('unusual_time', False):
                score *= 1.3
        
        return min(score, 10.0)
    
    # Audit Logging
    def log_audit_event(
        self,
        user_id: Optional[str],
        ip_address: str,
        action: AuditAction,
        resource: str,
        details: Dict[str, Any] = None
    ):
        """Audit olayını logla"""
        self._log_security_event(
            user_id=user_id,
            ip_address=ip_address,
            action=action.value,
            resource=resource,
            details=details,
            security_level=self._get_security_level_for_action(action)
        )
    
    def _get_security_level_for_action(self, action: AuditAction) -> SecurityLevel:
        """Aksiyona göre güvenlik seviyesi belirle"""
        if action in [AuditAction.SUSPICIOUS, AuditAction.BLOCKED]:
            return SecurityLevel.HIGH
        elif action in [AuditAction.LOGIN, AuditAction.LOGOUT]:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW
    
    # Threat Detection
    def detect_threats(self) -> List[SecurityEvent]:
        """Tehditleri tespit et"""
        threats = []
        
        # Çok fazla başarısız giriş denemesi
        for identifier, attempts in self.failed_attempts.items():
            if len(attempts) >= 10:  # 1 saatte 10'dan fazla
                threats.append(SecurityEvent(
                    timestamp=datetime.utcnow(),
                    user_id=identifier,
                    ip_address="unknown",
                    action="brute_force_attack",
                    details={"failed_attempts": len(attempts)},
                    risk_score=8.0,
                    security_level=SecurityLevel.CRITICAL
                ))
        
        # Şüpheli IP'ler
        for ip_address, count in self.suspicious_ips.items():
            if count >= 5:
                threats.append(SecurityEvent(
                    timestamp=datetime.utcnow(),
                    user_id=None,
                    ip_address=ip_address,
                    action="suspicious_ip_activity",
                    details={"activity_count": count},
                    risk_score=6.0,
                    security_level=SecurityLevel.HIGH
                ))
        
        return threats
    
    # Security Reports
    def generate_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Güvenlik raporu oluştur"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_events = [
            event for event in self.security_events
            if event.timestamp > cutoff_time
        ]
        
        # İstatistikler
        events_by_type = {}
        events_by_level = {}
        events_by_ip = {}
        
        for event in recent_events:
            # Tip bazlı istatistik
            events_by_type[event.action] = events_by_type.get(event.action, 0) + 1
            
            # Seviye bazlı istatistik
            level = event.security_level.value
            events_by_level[level] = events_by_level.get(level, 0) + 1
            
            # IP bazlı istatistik
            events_by_ip[event.ip_address] = events_by_ip.get(event.ip_address, 0) + 1
        
        # Tehdit analizi
        threats = self.detect_threats()
        
        return {
            "period": f"{hours}h",
            "total_events": len(recent_events),
            "events_by_type": events_by_type,
            "events_by_level": events_by_level,
            "top_ips": dict(sorted(events_by_ip.items(), key=lambda x: x[1], reverse=True)[:10]),
            "threats_detected": len(threats),
            "threats": [asdict(threat) for threat in threats],
            "risk_score_average": sum(event.risk_score for event in recent_events) / len(recent_events) if recent_events else 0
        }
    
    # IP Intelligence
    def analyze_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """IP adresi itibar analizi"""
        # Bu fonksiyon gerçek bir IP itibar servisi ile entegre edilecek
        return {
            "ip_address": ip_address,
            "reputation_score": 100,  # 0-100
            "is_tor": False,
            "is_proxy": False,
            "is_vpn": False,
            "country": "TR",
            "threat_level": "low",
            "last_seen": datetime.utcnow().isoformat()
        }


# Global security manager instance
security_manager = SecurityManager()


# Authentication dependency
def get_current_user(required_roles: List[UserRole] = None):
    """Mevcut kullanıcıyı al"""
    async def current_user_dependency(
        credentials: HTTPAuthorizationCredentials = Security(security_manager.security_bearer)
    ) -> User:
        # Token'ı doğrula
        payload = security_manager.verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Geçersiz veya süresi dolmuş token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Kullanıcıyı veritabanından al (mock)
        user = await get_user_by_id(payload.get("sub"))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Kullanıcı bulunamadı"
            )
        
        # Rol kontrolü
        if required_roles and user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Yetkisiz erişim"
            )
        
        return user
    
    return current_user_dependency


# Yardımcı fonksiyonlar
async def get_user_by_id(user_id: str) -> Optional[User]:
    """Kullanıcıyı ID'ye göre al"""
    # Bu fonksiyon veritabanından kullanıcı getirecek
    # Şimdilik mock data döndürüyoruz
    return User(
        id=user_id,
        email="user@loop.com",
        role=UserRole.COURIER,
        is_active=True
    )


def generate_secure_token(length: int = 32) -> str:
    """Güvenli token oluştur"""
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data: str) -> str:
    """Hassas veriyi hash'le"""
    return hashlib.sha256(data.encode()).hexdigest()


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """Hassas veriyi maskele"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]


# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}