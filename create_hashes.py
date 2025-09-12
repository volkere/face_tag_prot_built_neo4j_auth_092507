#!/usr/bin/env python3
"""
Einfaches Skript zum Generieren von bcrypt-Hashes
"""

import bcrypt

def create_password_hash(password):
    """Erstellt einen bcrypt-Hash für ein Passwort"""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

if __name__ == "__main__":
    # Passwörter definieren
    passwords = {
        'admin': 'admin123',
        'user': 'user123'
    }
    
    print("Generierte Passwort-Hashes:")
    print("=" * 50)
    
    for username, password in passwords.items():
        hash_value = create_password_hash(password)
        print(f"Benutzername: {username}")
        print(f"Passwort: {password}")
        print(f"Hash: {hash_value}")
        print("-" * 30)
