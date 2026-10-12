import sqlite3
import json
import os
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import DB_PATH

_db_lock = threading.Lock()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    with _db_lock:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                specific_spot TEXT,
                date_time TEXT NOT NULL,
                item_type TEXT NOT NULL, -- 'lost' or 'found'
                contact_name TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                contact_phone TEXT,
                brand TEXT,
                primary_color TEXT,
                secondary_color TEXT,
                distinguishing_features TEXT, -- JSON array
                secret_verification_question TEXT,
                secret_verification_answer TEXT,
                image_url TEXT,
                status TEXT DEFAULT 'active', -- 'active', 'matched', 'claimed', 'returned'
                vision_embedding TEXT, -- JSON vector
                vision_features_extracted INTEGER DEFAULT 0,
                nlp_features_extracted INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
        """)
        
        # Claims table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                claimant_name TEXT NOT NULL,
                claimant_student_id TEXT NOT NULL,
                claimant_email TEXT NOT NULL,
                claimant_phone TEXT,
                secret_answer TEXT NOT NULL,
                additional_proof TEXT,
                submitted_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending', -- 'pending', 'verified', 'rejected', 'handed_over'
                verification_score REAL DEFAULT 0.0,
                verification_passed INTEGER DEFAULT 0,
                verification_notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items (id)
            );
        """)
        
        # Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_email TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                item_id INTEGER,
                match_id INTEGER,
                created_at TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            );
        """)
        
        # Custody tracking logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custody_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (item_id) REFERENCES items (id)
            );
        """)
        
        conn.commit()
        conn.close()

# Database helper functions
def insert_item(item_data: Dict[str, Any]) -> int:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        dist_feats = item_data.get("distinguishing_features", [])
        if isinstance(dist_feats, list):
            dist_feats = json.dumps(dist_feats)
            
        vis_emb = item_data.get("vision_embedding")
        if isinstance(vis_emb, (list, dict)):
            vis_emb = json.dumps(vis_emb)
            
        now_str = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO items (
                title, description, category, location, specific_spot, date_time,
                item_type, contact_name, contact_email, contact_phone, brand,
                primary_color, secondary_color, distinguishing_features,
                secret_verification_question, secret_verification_answer,
                image_url, status, vision_embedding, vision_features_extracted,
                nlp_features_extracted, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_data["title"],
            item_data["description"],
            item_data["category"],
            item_data["location"],
            item_data.get("specific_spot"),
            item_data["date_time"],
            item_data["item_type"],
            item_data["contact_name"],
            item_data["contact_email"],
            item_data.get("contact_phone"),
            item_data.get("brand"),
            item_data.get("primary_color"),
            item_data.get("secondary_color"),
            dist_feats,
            item_data.get("secret_verification_question"),
            item_data.get("secret_verification_answer"),
            item_data.get("image_url"),
            item_data.get("status", "active"),
            vis_emb,
            item_data.get("vision_features_extracted", 0),
            item_data.get("nlp_features_extracted", 0),
            item_data.get("created_at", now_str)
        ))
        
        item_id = cursor.lastrowid
        
        # Log custody creation
        cursor.execute("""
            INSERT INTO custody_logs (item_id, action, actor, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            item_id,
            f"REPORTED_{item_data['item_type'].upper()}",
            item_data["contact_name"],
            now_str,
            f"Item reported at {item_data['location']}"
        ))
        
        conn.commit()
        conn.close()
        return item_id

def _format_item_row(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    features = d.get("distinguishing_features")
    if features:
        try:
            d["distinguishing_features"] = json.loads(features)
        except Exception:
            d["distinguishing_features"] = []
    else:
        d["distinguishing_features"] = []

    emb = d.get("vision_embedding")
    if emb:
        try:
            d["vision_embedding"] = json.loads(emb)
        except Exception:
            d["vision_embedding"] = None

    d["vision_features_extracted"] = bool(d.get("vision_features_extracted", 0))
    d["nlp_features_extracted"] = bool(d.get("nlp_features_extracted", 0))
    return d

def get_item(item_id: int) -> Optional[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        return _format_item_row(row) if row else None

def update_item_status(item_id: int, new_status: str, actor: str = "System", details: str = ""):
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE items SET status = ? WHERE id = ?", (new_status, item_id))
        now_str = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO custody_logs (item_id, action, actor, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (item_id, f"STATUS_{new_status.upper()}", actor, now_str, details))
        conn.commit()
        conn.close()

def list_items(
    item_type: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM items WHERE 1=1"
        params = []
        
        if item_type:
            query += " AND item_type = ?"
            params.append(item_type)
        if category:
            query += " AND category = ?"
            params.append(category)
        if location:
            query += " AND location = ?"
            params.append(location)
        if status:
            query += " AND status = ?"
            params.append(status)
        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR brand LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param, s_param])
            
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [_format_item_row(row) for row in rows]

def get_custody_history(item_id: int) -> List[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM custody_logs WHERE item_id = ? ORDER BY id ASC", (item_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

def insert_claim(claim_data: Dict[str, Any]) -> int:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO claims (
                item_id, claimant_name, claimant_student_id, claimant_email, claimant_phone,
                secret_answer, additional_proof, submitted_at, status, verification_score,
                verification_passed, verification_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            claim_data["item_id"],
            claim_data["claimant_name"],
            claim_data["claimant_student_id"],
            claim_data["claimant_email"],
            claim_data.get("claimant_phone"),
            claim_data["secret_answer"],
            claim_data.get("additional_proof"),
            now_str,
            claim_data.get("status", "pending"),
            claim_data.get("verification_score", 0.0),
            1 if claim_data.get("verification_passed") else 0,
            claim_data.get("verification_notes", "")
        ))
        claim_id = cursor.lastrowid
        
        # Log to custody history
        cursor.execute("""
            INSERT INTO custody_logs (item_id, action, actor, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (
            claim_data["item_id"],
            "CLAIM_SUBMITTED",
            claim_data["claimant_name"],
            now_str,
            f"Claim #{claim_id} submitted. Verification Score: {claim_data.get('verification_score', 0):.2f}"
        ))
        
        conn.commit()
        conn.close()
        return claim_id

def list_claims_for_item(item_id: int) -> List[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM claims WHERE item_id = ? ORDER BY id DESC", (item_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

def insert_notification(recipient_email: str, title: str, message: str, item_id: Optional[int] = None, match_id: Optional[int] = None):
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO notifications (recipient_email, title, message, item_id, match_id, created_at, is_read)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (recipient_email, title, message, item_id, match_id, now_str))
        conn.commit()
        conn.close()

def get_notifications(recipient_email: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        if recipient_email:
            cursor.execute("SELECT * FROM notifications WHERE recipient_email = ? ORDER BY id DESC LIMIT ?", (recipient_email, limit))
        else:
            cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

def mark_notification_read(notification_id: int) -> bool:
    with _db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated

