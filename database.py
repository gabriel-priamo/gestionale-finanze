import sqlite3
import os
from datetime import datetime, date
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "finanze.db")

def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=DB_PATH):
    """Inizializza le tabelle del database se non esistono."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    # Tabella transazioni
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('Entrata', 'Uscita')),
        categoria TEXT NOT NULL,
        sottocategoria TEXT DEFAULT '',
        descrizione TEXT NOT NULL,
        importo REAL NOT NULL,
        metodo_pagamento TEXT DEFAULT 'Bonifico',
        stato TEXT DEFAULT 'Completato' CHECK(stato IN ('Completato', 'In attesa', 'Programmato')),
        scadenza TEXT DEFAULT '',
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tabella categorie
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL CHECK(tipo IN ('Entrata', 'Uscita')),
        nome TEXT NOT NULL UNIQUE
    )
    """)
    
    # Tabella budget mensili
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT NOT NULL UNIQUE,
        budget_mensile REAL NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    
    seed_default_categories(db_path)

def seed_default_categories(db_path=DB_PATH):
    """Inserisce categorie predefinite se la tabella è vuota."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    count = cursor.fetchone()[0]
    
    if count == 0:
        default_categories = [
            # Entrate
            ('Entrata', 'Stipendio / Compensi'),
            ('Entrata', 'Vendite e Clienti'),
            ('Entrata', 'Consulenze'),
            ('Entrata', 'Investimenti / Rendite'),
            ('Entrata', 'Rimborsi'),
            ('Entrata', 'Altre Entrate'),
            # Uscite
            ('Uscita', 'Affitto / Mutuo'),
            ('Uscita', 'Utenze (Luce, Gas, Web)'),
            ('Uscita', 'Software & Tool SaaS'),
            ('Uscita', 'Spese Personale / Collaboratori'),
            ('Uscita', 'Marketing & Pubblicità'),
            ('Uscita', 'Tasse & Commercialista'),
            ('Uscita', 'Fornitori & Materiali'),
            ('Uscita', 'Cibo & Spesa'),
            ('Uscita', 'Trasporti & Viaggi'),
            ('Uscita', 'Assicurazioni'),
            ('Uscita', 'Formazione & Libri'),
            ('Uscita', 'Varie / Imprevisti')
        ]
        cursor.executemany("INSERT OR IGNORE INTO categories (tipo, nome) VALUES (?, ?)", default_categories)
        conn.commit()
        
    # Inizializza anche qualche budget di default
    cursor.execute("SELECT COUNT(*) FROM budgets")
    b_count = cursor.fetchone()[0]
    if b_count == 0:
        default_budgets = [
            ('Software & Tool SaaS', 150.0),
            ('Marketing & Pubblicità', 300.0),
            ('Utenze (Luce, Gas, Web)', 250.0),
            ('Cibo & Spesa', 400.0),
            ('Varie / Imprevisti', 200.0)
        ]
        cursor.executemany("INSERT OR IGNORE INTO budgets (categoria, budget_mensile) VALUES (?, ?)", default_budgets)
        conn.commit()
        
    conn.close()

def get_categories(tipo=None, db_path=DB_PATH):
    """Restituisce la lista dei nomi di categoria."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    if tipo:
        cursor.execute("SELECT nome FROM categories WHERE tipo = ? ORDER BY nome ASC", (tipo,))
    else:
        cursor.execute("SELECT nome FROM categories ORDER BY nome ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_category(tipo, nome, db_path=DB_PATH):
    """Aggiunge una nuova categoria personalizzata."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (tipo, nome) VALUES (?, ?)", (tipo, nome.strip()))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def add_transaction(data, tipo, categoria, descrizione, importo, 
                    sottocategoria="", metodo_pagamento="Bonifico", 
                    stato="Completato", scadenza="", note="", db_path=DB_PATH):
    """Aggiunge una transazione al database."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO transactions (data, tipo, categoria, sottocategoria, descrizione, importo, metodo_pagamento, stato, scadenza, note)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(data), tipo, categoria, sottocategoria, descrizione, float(importo), metodo_pagamento, stato, str(scadenza) if scadenza else "", note))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def update_transaction(trans_id, data, tipo, categoria, descrizione, importo, 
                       sottocategoria="", metodo_pagamento="Bonifico", 
                       stato="Completato", scadenza="", note="", db_path=DB_PATH):
    """Aggiorna una transazione esistente."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE transactions 
    SET data=?, tipo=?, categoria=?, sottocategoria=?, descrizione=?, importo=?, metodo_pagamento=?, stato=?, scadenza=?, note=?
    WHERE id=?
    """, (str(data), tipo, categoria, sottocategoria, descrizione, float(importo), metodo_pagamento, stato, str(scadenza) if scadenza else "", note, trans_id))
    conn.commit()
    conn.close()

def delete_transaction(trans_id, db_path=DB_PATH):
    """Elimina una transazione."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    conn.close()

def get_transactions_df(start_date=None, end_date=None, tipo=None, categoria=None, stato=None, db_path=DB_PATH):
    """Recupera le transazioni come DataFrame Pandas con filtri opzionali."""
    conn = get_connection(db_path)
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND data >= ?"
        params.append(str(start_date))
    if end_date:
        query += " AND data <= ?"
        params.append(str(end_date))
    if tipo and tipo != "Tutti":
        query += " AND tipo = ?"
        params.append(tipo)
    if categoria and categoria != "Tutte":
        query += " AND categoria = ?"
        params.append(categoria)
    if stato and stato != "Tutti":
        query += " AND stato = ?"
        params.append(stato)
        
    query += " ORDER BY data DESC, id DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty:
        df['data'] = pd.to_datetime(df['data'])
    return df

def get_budgets_df(db_path=DB_PATH):
    """Recupera la tabella dei budget impostati."""
    conn = get_connection(db_path)
    df = pd.read_sql_query("SELECT categoria, budget_mensile FROM budgets ORDER BY categoria ASC", conn)
    conn.close()
    return df

def set_budget(categoria, budget_mensile, db_path=DB_PATH):
    """Imposta o aggiorna il budget per una specifica categoria."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO budgets (categoria, budget_mensile)
    VALUES (?, ?)
    ON CONFLICT(categoria) DO UPDATE SET budget_mensile=excluded.budget_mensile
    """, (categoria, float(budget_mensile)))
    conn.commit()
    conn.close()

def reset_db_with_sample_data(db_path=DB_PATH):
    """Cancella e ricarica dati demo realistici."""
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
    from sample_data import generate_sample_data
    generate_sample_data(db_path)
