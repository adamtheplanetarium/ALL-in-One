#!/usr/bin/env python3
"""
Config Cleanup Script
Removes bloat from gui_mailer_config.json (206MB -> <1MB)
Run this BEFORE starting the GUI if your config file is huge
"""
import json
import os
from datetime import datetime

CONFIG_FILE = 'gui_mailer_config.json'
BACKUP_FILE = f'gui_mailer_config_BACKUP_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

def cleanup_config():
    print("=" * 70)
    print("CONFIG CLEANUP TOOL")
    print("=" * 70)
    
    if not os.path.exists(CONFIG_FILE):
        print(f"[!] {CONFIG_FILE} not found!")
        return
    
    # Check size
    size_bytes = os.path.getsize(CONFIG_FILE)
    size_mb = size_bytes / (1024 * 1024)
    print(f"\n[FILE] Current config size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
    
    if size_mb < 10:
        print("[OK] Config size is OK (< 10MB). No cleanup needed.")
        return
    
    print(f"[WARNING] Config is too large! Cleaning up...")
    
    # Backup original
    print(f"\n[BACKUP] Creating backup: {BACKUP_FILE}")
    import shutil
    try:
        shutil.copy2(CONFIG_FILE, BACKUP_FILE)
        print(f"[OK] Backup created successfully")
    except Exception as e:
        print(f"[ERROR] Backup failed: {e}")
        return
    
    # Load config
    print(f"\n[LOAD] Loading config...")
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return
    
    print(f"[OK] Config loaded")
    
    # Show what will be removed
    print(f"\n[CLEANUP] Items to remove:")
    removed_keys = []
    
    if 'smtp_servers_text' in config:
        size = len(config['smtp_servers_text'])
        print(f"   - smtp_servers_text: {size:,} chars")
        removed_keys.append('smtp_servers_text')
    
    if 'recipients_text' in config:
        size = len(config['recipients_text'])
        print(f"   - recipients_text: {size:,} chars")
        removed_keys.append('recipients_text')
    
    if 'from_addresses_text' in config:
        size = len(config['from_addresses_text'])
        print(f"   - from_addresses_text: {size:,} chars")
        removed_keys.append('from_addresses_text')
    
    if 'email_template' in config:
        size = len(config['email_template'])
        print(f"   - email_template: {size:,} chars")
        removed_keys.append('email_template')
    
    # Limit collections
    MAX_EMAILS = 100000
    
    if 'verified_froms' in config and len(config['verified_froms']) > MAX_EMAILS:
        print(f"   - verified_froms: {len(config['verified_froms']):,} -> {MAX_EMAILS:,}")
        config['verified_froms'] = config['verified_froms'][:MAX_EMAILS]
    
    if 'unverified_froms' in config and len(config['unverified_froms']) > MAX_EMAILS:
        print(f"   - unverified_froms: {len(config['unverified_froms']):,} -> {MAX_EMAILS:,}")
        config['unverified_froms'] = config['unverified_froms'][:MAX_EMAILS]
    
    if 'collected_from_emails' in config and len(config['collected_from_emails']) > MAX_EMAILS:
        print(f"   - collected_from_emails: {len(config['collected_from_emails']):,} -> {MAX_EMAILS:,}")
        config['collected_from_emails'] = config['collected_from_emails'][:MAX_EMAILS]
    
    # Remove bloat keys
    for key in removed_keys:
        if key in config:
            del config[key]
    
    # Save cleaned config
    print(f"\n[SAVE] Saving cleaned config...")
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        print(f"[OK] Config saved")
    except Exception as e:
        print(f"[ERROR] Failed to save config: {e}")
        return
    
    # Check new size
    new_size_bytes = os.path.getsize(CONFIG_FILE)
    new_size_mb = new_size_bytes / (1024 * 1024)
    saved_bytes = size_bytes - new_size_bytes
    saved_mb = saved_bytes / (1024 * 1024)
    
    print(f"\n[SUCCESS] CLEANUP COMPLETE!")
    print(f"   Before: {size_mb:.2f} MB")
    print(f"   After:  {new_size_mb:.2f} MB")
    print(f"   Saved:  {saved_mb:.2f} MB ({(saved_mb/size_mb*100):.1f}%)")
    print(f"\n[NOTE] Use Load/Save buttons in GUI to restore textarea contents")
    print("=" * 70)

if __name__ == "__main__":
    cleanup_config()
