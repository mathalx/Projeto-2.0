import os
import json
import hashlib
import binascii
from datetime import datetime

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def hash_password(password: str, salt: bytes = None) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with salt."""
    if salt is None:
        salt = os.urandom(16)
    # 100,000 iterations for secure hashing
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(salt).decode('ascii') + ':' + binascii.hexlify(pwdhash).decode('ascii')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify a stored password against a provided password."""
    try:
        salt_hex, pwdhash_hex = stored_password.split(':')
        salt = binascii.unhexlify(salt_hex.encode('ascii'))
        pwdhash = binascii.unhexlify(pwdhash_hex.encode('ascii'))
        new_pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return pwdhash == new_pwdhash
    except Exception:
        return False

def init_db():
    """Ensure data directory and initial users exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        initial_users = {
            "Ana.norte": {
                "password": hash_password("123456789"),
                "active": True,
                "is_admin": True,
                "created_at": created_at
            },
            "anaju.mãe": {
                "password": hash_password("123456789"),
                "active": True,
                "is_admin": False,
                "created_at": created_at
            },
            "anaju.pai": {
                "password": hash_password("123456789"),
                "active": True,
                "is_admin": False,
                "created_at": created_at
            }
        }
        save_users(initial_users)

def load_users() -> dict:
    init_db()
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def authenticate_user(username: str, password: str):
    users = load_users()
    if username in users:
        user_data = users[username]
        if user_data.get("active", True):
            if verify_password(user_data["password"], password):
                return True, "Login realizado com sucesso", user_data.get("is_admin", False)
        else:
            return False, "Usuário desativado no sistema.", False
    return False, "Credenciais incorretas ou usuário não encontrado.", False

def add_user(username: str, password: str, is_admin: bool = False):
    users = load_users()
    if username in users:
        return False, "Nome de usuário já cadastrado."
    if not username.strip() or not password.strip():
        return False, "Usuário e senha não podem estar vazios."
    
    users[username] = {
        "password": hash_password(password),
        "active": True,
        "is_admin": is_admin,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)
    return True, "Usuário cadastrado com sucesso."

def update_password(username: str, current_password: str, new_password: str):
    users = load_users()
    if username not in users:
        return False, "Usuário não encontrado."
    
    user_data = users[username]
    if not verify_password(user_data["password"], current_password):
        return False, "Senha atual incorreta."
    
    if len(new_password.strip()) < 6:
        return False, "A nova senha deve ter pelo menos 6 caracteres."
        
    users[username]["password"] = hash_password(new_password)
    save_users(users)
    return True, "Senha alterada com sucesso."

def admin_reset_password(username: str, new_password: str):
    users = load_users()
    if username not in users:
        return False, "Usuário não encontrado."
    users[username]["password"] = hash_password(new_password)
    save_users(users)
    return True, "Senha redefinida pelo administrador com sucesso."

def toggle_user_status(username: str):
    users = load_users()
    if username not in users:
        return False, "Usuário não encontrado."
    current = users[username].get("active", True)
    if username == "Ana.norte" and current:
        return False, "Não é permitido desativar o usuário administrador principal."
    users[username]["active"] = not current
    save_users(users)
    status_text = "ativado" if not current else "desativado"
    return True, f"Usuário {status_text} com sucesso."

def delete_user(username: str):
    users = load_users()
    if username not in users:
        return False, "Usuário não encontrado."
    if username in ["Ana.norte"]:
        return False, "Não é permitido excluir o usuário administrador principal."
    del users[username]
    save_users(users)
    return True, "Usuário removido com sucesso."
