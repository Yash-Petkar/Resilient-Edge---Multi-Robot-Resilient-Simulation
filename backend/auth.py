"""Local JWT authentication for the self-hosted ResilientEdge backend."""
from __future__ import annotations
import hashlib, hmac, os, secrets, time, uuid
from dataclasses import dataclass
from typing import Optional, Dict, Any
import jwt
from dotenv import load_dotenv
from backend.database.sqlite_db import ResilientEdgeDatabase
load_dotenv()
ROLES={"ADMIN","OPERATOR","OBSERVER","VIEWER"}

class AuthenticationError(Exception): pass

@dataclass(frozen=True)
class AuthUser:
    id: str
    email: str
    role: str
    full_name: str
    local: bool=False


def _secret() -> str:
    secret=os.getenv('JWT_SECRET','').strip()
    if len(secret)<32: raise RuntimeError('JWT_SECRET must be configured with at least 32 characters')
    return secret

def hash_password(password: str) -> str:
    if len(password)<8: raise ValueError('Password must be at least 8 characters')
    salt=secrets.token_bytes(16)
    digest=hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme,n,r,p,salt_hex,digest_hex=encoded.split('$')
        if scheme!='scrypt': return False
        digest=hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception: return False

class AuthService:
    ACCESS_MINUTES = 30
    REFRESH_DAYS = 7

    def __init__(self, db: Optional[ResilientEdgeDatabase]=None):
        self.db=db or ResilientEdgeDatabase()

    def _token(self,user: Dict[str,Any], token_type: str, minutes: int, session_id: str) -> str:
        now=int(time.time())
        return jwt.encode({'sub':user['id'],'email':user['email'],'role':user.get('role') or 'OBSERVER','iat':now,'exp':now+minutes*60,'type':token_type,'sid':session_id,'jti':str(uuid.uuid4())},_secret(),algorithm='HS256')

    @staticmethod
    def _refresh_hash(token: str) -> str:
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def authenticate(self,email,password):
        user=self.db.get_user_by_email(email)
        if not user or not user.get('is_active') or not verify_password(password,user['password_hash']):
            self.audit(None,'LOGIN_FAILED',metadata={'reason':'invalid_credentials'})
            raise AuthenticationError('Invalid email or password')
        auth_user=self.user_from_row(user)
        self.audit(auth_user,'LOGIN')
        session_id=str(uuid.uuid4())
        access=self._token(user,'access',self.ACCESS_MINUTES,session_id)
        refresh=self._token(user,'refresh',self.REFRESH_DAYS*24*60,session_id)
        now=time.time()
        self.db.create_auth_session(session_id, user['id'], self._refresh_hash(refresh), now, now+self.REFRESH_DAYS*86400)
        return auth_user, access, refresh

    def verify_token(self,token: str, expected_type='access')->AuthUser:
        if not token: raise AuthenticationError('Missing access token')
        try:
            claims=jwt.decode(token,_secret(),algorithms=['HS256'],options={'require':['sub','email','role','exp']})
            if claims.get('type','access')!=expected_type: raise AuthenticationError('Invalid token type')
        except AuthenticationError: raise
        except Exception as exc: raise AuthenticationError('Invalid or expired access token') from exc
        row=self.db.get_user_by_id(str(claims['sub']))
        if not row or not row.get('is_active'): raise AuthenticationError('User account is inactive or missing')
        role=row.get('role') or 'OBSERVER'
        if role not in ROLES: raise AuthenticationError('User profile has an invalid role')
        return self.user_from_row(row)

    def refresh(self,token: str):
        user=self.verify_token(token,'refresh')
        session=self.db.get_auth_session(self._refresh_hash(token))
        now=time.time()
        if not session or session.get('user_id') != user.id or session.get('revoked_at') is not None or float(session.get('expires_at',0)) <= now:
            raise AuthenticationError('Refresh session is invalid or revoked')
        self.db.revoke_auth_session(session['id'])
        row=self.db.get_user_by_id(user.id)
        new_session_id=str(uuid.uuid4())
        access=self._token(row,'access',self.ACCESS_MINUTES,new_session_id)
        refresh=self._token(row,'refresh',self.REFRESH_DAYS*24*60,new_session_id)
        self.db.create_auth_session(new_session_id, user.id, self._refresh_hash(refresh), now, now+self.REFRESH_DAYS*86400)
        return access, refresh

    def logout(self, access_token: str):
        user=self.verify_token(access_token,'access')
        try:
            claims=jwt.decode(access_token,_secret(),algorithms=['HS256'],options={'require':['sub','exp','sid']})
        except Exception as exc:
            raise AuthenticationError('Invalid or expired access token') from exc
        session_id=str(claims['sid'])
        session=self.db.get_auth_session_by_id(session_id)
        if not session or session.get('user_id') != user.id:
            raise AuthenticationError('Authentication session is invalid')
        self.db.revoke_auth_session(session_id)
        self.audit(user,'LOGOUT')
        return user

    def user_from_row(self,row): return AuthUser(id=row['id'],email=row['email'],role=row.get('role') or 'OBSERVER',full_name=row.get('full_name') or row['email'])

    def audit(self,user:AuthUser|Dict[str,Any]|None,action,entity_type=None,entity_id=None,metadata=None):
        if isinstance(user,AuthUser): uid,role=(None if user.local else user.id),user.role
        elif isinstance(user,dict): uid,role=user.get('id'),user.get('role')
        else: uid,role=None,None
        safe_metadata=metadata or {}
        self.db.save_audit_log({'log_id':str(uuid.uuid4()),'user_id':uid,'user_role':role,'action':action,'entity_type':entity_type,'entity_id':entity_id,'metadata':safe_metadata})

    def authenticate_header(self,authorization:Optional[str])->AuthUser:
        if not authorization or not authorization.lower().startswith('bearer '): raise AuthenticationError('Authentication required')
        return self.verify_token(authorization.split(' ',1)[1].strip())
    def authenticate_token(self,token:Optional[str])->AuthUser: return self.verify_token(token or '')
    def local_user(self): raise AuthenticationError('Local development role authentication is disabled; use /api/auth/login')

auth_service=AuthService()

def extract_bearer(authorization:Optional[str])->Optional[str]:
    return authorization.split(' ',1)[1].strip() if authorization and authorization.lower().startswith('bearer ') else None
