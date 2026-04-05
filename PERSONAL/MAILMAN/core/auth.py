#!/usr/bin/env python3
"""
MAILMAN Authentication Module
Handles OAuth2 flows for Gmail and Google Workspace accounts.
Encrypts and stores tokens using per-account Fernet keys.

Usage:
  python3 auth.py --setup              # Interactive setup for new account
  python3 auth.py --list               # List configured accounts
  python3 auth.py --refresh <account>  # Force token refresh
  python3 auth.py --revoke <account>   # Revoke access for account
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime

try:
    from cryptography.fernet import Fernet
except ImportError:
    print("Missing dependency: pip install cryptography --break-system-packages")
    sys.exit(1)

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("Missing dependency: pip install google-api-python-client google-auth-oauthlib --break-system-packages")
    sys.exit(1)


# Gmail API scopes - read, modify, send
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.send",
]

MAILMAN_ROOT = Path(__file__).parent.parent
CONFIG_DIR = MAILMAN_ROOT / "config"
LOGS_DIR = MAILMAN_ROOT / "logs"


class TokenVault:
    """
    Encrypted token storage using Fernet symmetric encryption.
    Each account gets its own encryption key, stored separately from tokens.
    """

    def __init__(self):
        self.keys_file = CONFIG_DIR / ".keys.json"
        self.tokens_file = CONFIG_DIR / ".tokens.enc"
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._keys = self._load_keys()
        self._tokens = self._load_tokens()

    def _load_keys(self):
        if self.keys_file.exists():
            with open(self.keys_file, "r") as f:
                return json.load(f)
        return {}

    def _save_keys(self):
        with open(self.keys_file, "w") as f:
            json.dump(self._keys, f, indent=2)
        os.chmod(self.keys_file, 0o600)

    def _load_tokens(self):
        if self.tokens_file.exists():
            with open(self.tokens_file, "r") as f:
                return json.load(f)
        return {}

    def _save_tokens(self):
        with open(self.tokens_file, "w") as f:
            json.dump(self._tokens, f, indent=2)
        os.chmod(self.tokens_file, 0o600)

    def _get_fernet(self, account_id):
        if account_id not in self._keys:
            self._keys[account_id] = Fernet.generate_key().decode()
            self._save_keys()
        return Fernet(self._keys[account_id].encode())

    def store_token(self, account_id, credentials):
        """Encrypt and store OAuth2 credentials for an account."""
        fernet = self._get_fernet(account_id)
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else GMAIL_SCOPES,
            "stored_at": datetime.utcnow().isoformat(),
        }
        encrypted = fernet.encrypt(json.dumps(token_data).encode()).decode()
        self._tokens[account_id] = encrypted
        self._save_tokens()

    def load_token(self, account_id):
        """Decrypt and return OAuth2 credentials for an account."""
        if account_id not in self._tokens:
            return None
        fernet = self._get_fernet(account_id)
        try:
            decrypted = fernet.decrypt(self._tokens[account_id].encode())
            token_data = json.loads(decrypted)
            return Credentials(
                token=token_data["token"],
                refresh_token=token_data["refresh_token"],
                token_uri=token_data["token_uri"],
                client_id=token_data["client_id"],
                client_secret=token_data["client_secret"],
                scopes=token_data.get("scopes", GMAIL_SCOPES),
            )
        except Exception as e:
            print(f"Error decrypting token for {account_id}: {e}")
            return None

    def remove_token(self, account_id):
        """Remove stored credentials for an account."""
        self._tokens.pop(account_id, None)
        self._keys.pop(account_id, None)
        self._save_tokens()
        self._save_keys()

    def list_accounts(self):
        """Return list of configured account IDs."""
        return list(self._tokens.keys())


class AccountManager:
    """
    Manages OAuth2 setup and credential lifecycle for email accounts.
    """

    def __init__(self):
        self.vault = TokenVault()
        self.accounts_file = CONFIG_DIR / "accounts.json"

    def _load_accounts_config(self):
        if self.accounts_file.exists():
            with open(self.accounts_file, "r") as f:
                return json.load(f)
        return {"accounts": []}

    def _save_accounts_config(self, config):
        with open(self.accounts_file, "w") as f:
            json.dump(config, f, indent=2)

    def setup_gmail_account(self, account_id, client_secrets_path, account_type="personal"):
        """
        Run OAuth2 flow for a Gmail/Workspace account.

        Args:
            account_id: Unique identifier (e.g., "gmail_personal", "antidote_work")
            client_secrets_path: Path to OAuth2 client_secret.json from Google Cloud Console
            account_type: "personal" or "workspace"
        """
        if not Path(client_secrets_path).exists():
            print(f"Client secrets file not found: {client_secrets_path}")
            print("\nTo get this file:")
            print("1. Go to https://console.cloud.google.com/apis/credentials")
            print("2. Create an OAuth2 Client ID (Desktop application)")
            print("3. Download the client_secret.json")
            print(f"4. Place it at: {client_secrets_path}")
            return None

        flow = InstalledAppFlow.from_client_secrets_file(
            client_secrets_path,
            scopes=GMAIL_SCOPES,
        )
        credentials = flow.run_local_server(port=0)

        # Store encrypted token
        self.vault.store_token(account_id, credentials)

        # Update accounts config
        config = self._load_accounts_config()
        account_entry = {
            "id": account_id,
            "type": account_type,
            "provider": "gmail",
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

        # Replace if exists, otherwise append
        config["accounts"] = [a for a in config["accounts"] if a["id"] != account_id]
        config["accounts"].append(account_entry)
        self._save_accounts_config(config)

        print(f"Account '{account_id}' configured successfully.")
        return credentials

    def get_credentials(self, account_id):
        """
        Get valid credentials for an account, refreshing if needed.
        """
        creds = self.vault.load_token(account_id)
        if not creds:
            print(f"No credentials found for '{account_id}'. Run --setup first.")
            return None

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self.vault.store_token(account_id, creds)
            except Exception as e:
                print(f"Token refresh failed for '{account_id}': {e}")
                print("Run --setup again to re-authenticate.")
                return None

        return creds

    def list_accounts(self):
        """List all configured accounts with status."""
        config = self._load_accounts_config()
        if not config["accounts"]:
            print("No accounts configured. Run: python3 auth.py --setup")
            return []

        print(f"\nConfigured accounts ({len(config['accounts'])}):")
        for acct in config["accounts"]:
            creds = self.vault.load_token(acct["id"])
            status = "active" if creds else "needs_reauth"
            print(f"  {acct['id']:25s} | {acct['provider']:10s} | {acct['type']:12s} | {status}")
        return config["accounts"]

    def revoke_account(self, account_id):
        """Remove all stored credentials for an account."""
        self.vault.remove_token(account_id)
        config = self._load_accounts_config()
        config["accounts"] = [a for a in config["accounts"] if a["id"] != account_id]
        self._save_accounts_config(config)
        print(f"Account '{account_id}' revoked and credentials destroyed.")


def main():
    parser = argparse.ArgumentParser(description="MAILMAN Account Authentication")
    parser.add_argument("--setup", action="store_true", help="Set up a new email account")
    parser.add_argument("--list", action="store_true", help="List configured accounts")
    parser.add_argument("--refresh", type=str, help="Force refresh token for account")
    parser.add_argument("--revoke", type=str, help="Revoke access for account")
    parser.add_argument("--account-id", type=str, help="Account identifier")
    parser.add_argument("--client-secret", type=str, help="Path to OAuth2 client_secret.json")
    parser.add_argument("--account-type", type=str, default="personal",
                        choices=["personal", "workspace"], help="Account type")
    args = parser.parse_args()

    manager = AccountManager()

    if args.list:
        manager.list_accounts()
    elif args.revoke:
        manager.revoke_account(args.revoke)
    elif args.refresh:
        creds = manager.get_credentials(args.refresh)
        if creds:
            print(f"Token refreshed for '{args.refresh}'")
    elif args.setup:
        account_id = args.account_id or input("Account ID (e.g., gmail_personal): ").strip()
        client_secret = args.client_secret or input("Path to client_secret.json: ").strip()
        account_type = args.account_type
        manager.setup_gmail_account(account_id, client_secret, account_type)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
