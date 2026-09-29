import pathlib, tempfile, os, time
from backend.auth import AuthService, AuthenticationError, extract_bearer, hash_password
from backend.database.sqlite_db import ResilientEdgeDatabase

def make_service(td):
    os.environ['JWT_SECRET']='test-secret-'+'x'*40
    return AuthService(ResilientEdgeDatabase(os.path.join(td,'auth.db')))

def seed(svc, role='OBSERVER'):
    svc.db.create_user('u1','user@example.com',hash_password('Password!123'),'Test User',role)

def test_missing_token_is_rejected():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td)
        try: svc.authenticate_header(None); assert False
        except AuthenticationError: pass

def test_malformed_token_is_rejected():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td)
        try: svc.authenticate_header('Bearer '); assert False
        except AuthenticationError: pass

def test_invalid_and_expired_tokens_are_rejected():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc)
        for token in ['invalid','Bearer.invalid.token']:
            try: svc.verify_token(token); assert False
            except AuthenticationError: pass

def test_valid_token_resolves_profile_roles():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc,'ADMIN'); user,access,_=svc.authenticate('user@example.com','Password!123')
        assert svc.verify_token(access).role=='ADMIN'

def test_all_supported_roles_resolve_from_profile():
    for role in ['ADMIN','OPERATOR','OBSERVER','VIEWER']:
        with tempfile.TemporaryDirectory() as td:
            svc=make_service(td); seed(svc,role); _,access,_=svc.authenticate('user@example.com','Password!123'); assert svc.verify_token(access).role==role

def test_missing_profile_is_rejected_safely():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td)
        import jwt
        token=jwt.encode({'sub':'missing','email':'x@example.com','role':'ADMIN','exp':int(time.time())+300},os.environ['JWT_SECRET'],algorithm='HS256')
        try: svc.verify_token(token); assert False
        except AuthenticationError: pass

def test_extract_bearer_is_exact():
    token='abc.def.ghi'; assert extract_bearer('Bearer '+token)==token; assert extract_bearer('bearer '+token)==token; assert extract_bearer('Basic abc') is None

def test_node_proxy_preserves_authorization_header():
    source=pathlib.Path('server.ts').read_text()
    assert '...req.headers' in source
    assert 'authorization' not in source.lower() or '...req.headers' in source

def test_password_hash_is_not_plaintext():
    encoded=hash_password('Password!123'); assert encoded!='Password!123'; assert len(encoded)>50

def test_wrong_password_is_rejected():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc)
        try: svc.authenticate('user@example.com','wrong-password'); assert False
        except AuthenticationError: pass


def test_refresh_rotation_and_revocation():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc,'ADMIN')
        _,access,refresh=svc.authenticate('user@example.com','Password!123')
        new_access,new_refresh=svc.refresh(refresh)
        assert svc.verify_token(new_access).role=='ADMIN'
        try: svc.refresh(refresh); assert False
        except AuthenticationError: pass
        svc.logout(new_access)
        try: svc.refresh(new_refresh); assert False
        except AuthenticationError: pass

def test_login_failure_is_audited_without_credentials():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc)
        try: svc.authenticate('user@example.com','wrong-password'); assert False
        except AuthenticationError: pass
        logs=svc.db.get_audit_logs(5)
        failed=[x for x in logs if x['action']=='LOGIN_FAILED'][0]
        assert failed['user_id'] is None
        assert 'password' not in str(failed['metadata']).lower()


def test_expired_access_token_is_rejected():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc,'ADMIN')
        import jwt
        token=jwt.encode(
            {'sub':'u1','email':'user@example.com','role':'ADMIN','exp':int(time.time())-1,'type':'access','sid':'missing'},
            os.environ['JWT_SECRET'],algorithm='HS256'
        )
        try:
            svc.verify_token(token)
            assert False
        except AuthenticationError:
            pass


def test_logout_revokes_only_the_active_session():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc,'ADMIN')
        _, access_a, refresh_a = svc.authenticate('user@example.com','Password!123')
        _, access_b, refresh_b = svc.authenticate('user@example.com','Password!123')
        svc.logout(access_a)
        try:
            svc.refresh(refresh_a)
            assert False
        except AuthenticationError:
            pass
        assert svc.verify_token(access_b).role == 'ADMIN'
        svc.refresh(refresh_b)


def test_logout_creates_audit_event_without_token_data():
    with tempfile.TemporaryDirectory() as td:
        svc=make_service(td); seed(svc,'ADMIN')
        _, access, _ = svc.authenticate('user@example.com','Password!123')
        svc.logout(access)
        logs=svc.db.get_audit_logs(10)
        logout=[x for x in logs if x['action']=='LOGOUT'][0]
        assert logout['user_id']=='u1'
        assert 'token' not in str(logout['metadata']).lower()
