#!/usr/bin/env python3
"""
Skript zum Generieren von sicheren Passwort-Hashes für die Authentifizierung
"""

import streamlit_authenticator as stauth
import yaml

def update_config_with_new_passwords():
    """Aktualisiert die config.yaml mit neuen Passwort-Hashes"""
    
    # Neue Passwörter definieren
    passwords = ['admin123', 'user123']
    
    # Hashes generieren
    hashed_passwords = stauth.Hasher(passwords).generate()
    
    # Config laden
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Passwörter aktualisieren
    usernames = ['admin', 'user']
    for i, username in enumerate(usernames):
        config['credentials']['usernames'][username]['password'] = hashed_passwords[i]
    
    # Config speichern
    with open('config.yaml', 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    
    print("Passwort-Hashes erfolgreich aktualisiert!")
    print("Benutzername: admin, Passwort: admin123")
    print("Benutzername: user, Passwort: user123")

if __name__ == "__main__":
    update_config_with_new_passwords()
