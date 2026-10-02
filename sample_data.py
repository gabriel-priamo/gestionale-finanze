from datetime import datetime, date, timedelta
import random

def generate_sample_data(db_path=None):
    from database import add_transaction, add_category, init_db, set_budget, DB_PATH
    
    actual_db = db_path if db_path else DB_PATH
    init_db(actual_db)
    
    today = date.today()
    
    # Esempi di transazioni distribuite negli ultimi 90 giorni e prossimi 30 giorni
    transactions = [
        # --- Entrate Mese Corrente & Precedenti ---
        (today - timedelta(days=5), 'Entrata', 'Vendite e Clienti', 'Sviluppo Web App per Cliente Alfa', 2450.0, 'Bonifico', 'Completato', '', 'Fattura 12/2026 saldata'),
        (today - timedelta(days=12), 'Entrata', 'Consulenze', 'Consulenza Strategia Cloud & DevOps', 980.0, 'Bonifico', 'Completato', '', 'Accordo mensile'),
        (today - timedelta(days=25), 'Entrata', 'Stipendio / Compensi', 'Compenso Mensile Amministratore', 3200.0, 'Bonifico', 'Completato', '', 'Bonifico stipendio'),
        (today - timedelta(days=34), 'Entrata', 'Vendite e Clienti', 'Integrazione API e CRM Cliente Beta', 1800.0, 'Bonifico', 'Completato', '', 'Fattura 11/2026'),
        (today - timedelta(days=55), 'Entrata', 'Stipendio / Compensi', 'Compenso Mensile Amministratore', 3200.0, 'Bonifico', 'Completato', '', 'Bonifico stipendio'),
        (today - timedelta(days=62), 'Entrata', 'Investimenti / Rendite', 'Dividendi Trimestrali Fondo ETF', 415.50, 'Bonifico', 'Completato', '', 'Accredito automatico'),
        (today - timedelta(days=70), 'Entrata', 'Vendite e Clienti', 'Consulenza Architettura Software', 1500.0, 'Bonifico', 'Completato', '', 'Fattura 10/2026'),
        (today - timedelta(days=85), 'Entrata', 'Stipendio / Compensi', 'Compenso Mensile Amministratore', 3200.0, 'Bonifico', 'Completato', '', 'Bonifico stipendio'),

        # --- Uscite Fisse & Variabili (Mese corrente e passati) ---
        (today - timedelta(days=2), 'Uscita', 'Cibo & Spesa', 'Pranzo di lavoro con partner commerciale', 64.0, 'Carta di Credito', 'Completato', '', 'Ristorante Il Portico'),
        (today - timedelta(days=4), 'Uscita', 'Software & Tool SaaS', 'Abbonamento Claude & ChatGPT Plus', 44.0, 'Carta di Credito', 'Completato', '', 'Strumenti AI per sviluppo'),
        (today - timedelta(days=7), 'Uscita', 'Software & Tool SaaS', 'Server Cloud Google Cloud & Vercel Pro', 78.50, 'Carta di Credito', 'Completato', '', 'Infrastruttura web'),
        (today - timedelta(days=10), 'Uscita', 'Marketing & Pubblicità', 'Campagna Google Ads & Meta Lead Gen', 210.0, 'PayPal', 'Completato', '', 'Acquisizione contatti B2B'),
        (today - timedelta(days=15), 'Uscita', 'Affitto / Mutuo', 'Affitto Ufficio / Coworking Mensile', 650.0, 'Bonifico', 'Completato', '', 'Canone locazione'),
        (today - timedelta(days=18), 'Uscita', 'Utenze (Luce, Gas, Web)', 'Fibra Ottica Aziendale + Utenze', 135.0, 'Bonifico', 'Completato', '', 'Fattura bimestrale'),
        (today - timedelta(days=20), 'Uscita', 'Spese Personale / Collaboratori', 'Collaborazione Freelance Grafica & UI', 550.0, 'Bonifico', 'Completato', '', 'Design system completato'),
        (today - timedelta(days=22), 'Uscita', 'Trasporti & Viaggi', 'Treno Alta Velocità Milano-Roma (Meeting)', 142.0, 'Carta di Credito', 'Completato', '', 'Biglietto andata e ritorno'),
        (today - timedelta(days=28), 'Uscita', 'Formazione & Libri', 'Corso Avanzato Python & Cloud Native', 89.0, 'Carta di Credito', 'Completato', '', 'Piattaforma e-learning'),
        (today - timedelta(days=35), 'Uscita', 'Affitto / Mutuo', 'Affitto Ufficio / Coworking Mensile', 650.0, 'Bonifico', 'Completato', '', 'Canone mese precedente'),
        (today - timedelta(days=38), 'Uscita', 'Software & Tool SaaS', 'Abbonamenti GitHub, JetBrains, Notion', 65.0, 'Carta di Credito', 'Completato', '', 'Toolchain sviluppo'),
        (today - timedelta(days=42), 'Uscita', 'Marketing & Pubblicità', 'Sponsorizzazioni LinkedIn Ads', 195.0, 'PayPal', 'Completato', '', 'Campagna promozionale'),
        (today - timedelta(days=65), 'Uscita', 'Affitto / Mutuo', 'Affitto Ufficio / Coworking Mensile', 650.0, 'Bonifico', 'Completato', '', 'Canone locazione'),
        (today - timedelta(days=72), 'Uscita', 'Tasse & Commercialista', 'Acconto Tributario F24 & Consulenza', 840.0, 'Bonifico', 'Completato', '', 'Gestione fiscale trimestrale'),

        # --- Scadenze Imminenti e Future (In attesa / Programmati) ---
        (today + timedelta(days=3), 'Uscita', 'Software & Tool SaaS', 'Rinnovo Licenze Microsoft 365 & Domain', 120.0, 'Carta di Credito', 'In attesa', str(today + timedelta(days=3)), 'Scadenza automatica'),
        (today + timedelta(days=7), 'Entrata', 'Vendite e Clienti', 'Saldo Fattura Finale Progetto E-commerce Gamma', 3100.0, 'Bonifico', 'In attesa', str(today + timedelta(days=7)), 'Cliente confermato per bonifico a 30gg'),
        (today + timedelta(days=12), 'Uscita', 'Affitto / Mutuo', 'Canone Affitto Ufficio Prossimo Mese', 650.0, 'Bonifico', 'Programmato', str(today + timedelta(days=12)), 'Bonifico programmato'),
        (today + timedelta(days=18), 'Uscita', 'Spese Personale / Collaboratori', 'Fattura Copywriter & SEO Specialist', 400.0, 'Bonifico', 'In attesa', str(today + timedelta(days=18)), 'In revisione bozza articoli'),
        (today + timedelta(days=25), 'Entrata', 'Stipendio / Compensi', 'Compenso Amministratore Prossimo Mese', 3200.0, 'Bonifico', 'Programmato', str(today + timedelta(days=25)), 'Accredito fine mese')
    ]
    
    for t in transactions:
        dt, tipo, cat, desc, imp, metodo, stato, scad, note = t
        add_transaction(
            data=dt,
            tipo=tipo,
            categoria=cat,
            descrizione=desc,
            importo=imp,
            metodo_pagamento=metodo,
            stato=stato,
            scadenza=scad,
            note=note,
            db_path=actual_db
        )
        
    print(f"Inserite {len(transactions)} transazioni di esempio.")

if __name__ == "__main__":
    generate_sample_data()
