import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import io
import os

from database import (
    init_db, get_connection, add_transaction, update_transaction, 
    delete_transaction, get_transactions_df, get_budgets_df, 
    set_budget, get_categories, add_category, reset_db_with_sample_data, DB_PATH
)
from sample_data import generate_sample_data

# --- Configurazione Pagina ---
st.set_page_config(
    page_title="FinPulse | Controllo Finanze & Spese",
    page_icon="💶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inizializza il DB se non esiste
if not os.path.exists(DB_PATH):
    init_db()
    generate_sample_data()

# --- Stili CSS personalizzati ---
st.markdown("""
<style>
    /* Card metriche personalizzate */
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .metric-title {
        font-size: 0.85rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-subtitle {
        font-size: 0.8rem;
        margin-top: 4px;
    }
    .text-positive { color: #10B981; }
    .text-negative { color: #EF4444; }
    .text-neutral { color: #38BDF8; }
    .text-warning { color: #F59E0B; }
    
    /* Titoli sezioni */
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #F1F5F9;
        margin-top: 10px;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 2px solid #334155;
    }
    
    /* Badge scadenze */
    .badge-urgent {
        background-color: rgba(239, 68, 68, 0.2);
        color: #EF4444;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-upcoming {
        background-color: rgba(245, 158, 11, 0.2);
        color: #F59E0B;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .badge-future {
        background-color: rgba(56, 189, 248, 0.2);
        color: #38BDF8;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Navigazione & Filtri Globali ---
with st.sidebar:
    st.markdown("## 💶 **FinPulse**")
    st.caption("Gestionale Finanze & Controllo di Gestione")
    st.markdown("---")
    
    menu = st.radio(
        "Navigazione",
        [
            "📊 Panoramica & Dashboard",
            "💳 Gestione Transazioni",
            "⏳ Scadenze & Flusso di Cassa",
            "🎯 Budget per Categoria",
            "📑 Report & Esportazione",
            "⚙️ Categorie & Dati"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 🔍 **Filtro Periodo**")
    period_option = st.selectbox(
        "Intervallo Temporale",
        [
            "Tutti i dati",
            "Questo Mese",
            "Ultimi 30 Giorni",
            "Ultimi 90 Giorni",
            "Anno Corrente",
            "Personalizzato"
        ]
    )
    
    today = date.today()
    if period_option == "Questo Mese":
        filter_start = today.replace(day=1)
        filter_end = today
    elif period_option == "Ultimi 30 Giorni":
        filter_start = today - timedelta(days=30)
        filter_end = today
    elif period_option == "Ultimi 90 Giorni":
        filter_start = today - timedelta(days=90)
        filter_end = today
    elif period_option == "Anno Corrente":
        filter_start = today.replace(month=1, day=1)
        filter_end = today
    elif period_option == "Personalizzato":
        c1, c2 = st.columns(2)
        filter_start = c1.date_input("Dal", today - timedelta(days=30))
        filter_end = c2.date_input("Al", today)
    else:
        filter_start = None
        filter_end = None

    st.markdown("---")
    with st.expander("🛠️ Azioni Rapide"):
        if st.button("🔄 Ricarica Dati Demo", use_container_width=True, help="Cancella e ricarica transazioni di test realistiche"):
            reset_db_with_sample_data()
            st.success("Dati demo caricati con successo!")
            st.rerun()

# Recupera tutti i dati per il periodo selezionato
df_all = get_transactions_df(start_date=filter_start, end_date=filter_end)

# ==============================================================================
# 1. PANORAMICA & DASHBOARD
# ==============================================================================
if menu == "📊 Panoramica & Dashboard":
    st.title("📊 Panoramica Finanziaria")
    st.caption("Visualizza in tempo reale entrate, uscite, margine operativo e scadenze.")
    
    # Calcolo Metriche
    df_completed = df_all[df_all['stato'] == 'Completato'] if not df_all.empty else pd.DataFrame()
    df_pending = df_all[df_all['stato'].isin(['In attesa', 'Programmato'])] if not df_all.empty else pd.DataFrame()
    
    tot_entrate = df_completed[df_completed['tipo'] == 'Entrata']['importo'].sum() if not df_completed.empty else 0.0
    tot_uscite = df_completed[df_completed['tipo'] == 'Uscita']['importo'].sum() if not df_completed.empty else 0.0
    saldo_netto = tot_entrate - tot_uscite
    
    saving_rate = ((saldo_netto / tot_entrate) * 100) if tot_entrate > 0 else 0.0
    pending_uscite = df_pending[df_pending['tipo'] == 'Uscita']['importo'].sum() if not df_pending.empty else 0.0
    pending_entrate = df_pending[df_pending['tipo'] == 'Entrata']['importo'].sum() if not df_pending.empty else 0.0

    # Controllo Scadenze Imminenti (< 7 giorni)
    df_imminent = get_transactions_df(stato="In attesa")
    if not df_imminent.empty:
        df_imminent['scadenza_dt'] = pd.to_datetime(df_imminent['scadenza'], errors='coerce').dt.date
        imminent_alert = df_imminent[
            (df_imminent['scadenza_dt'].notna()) & 
            (df_imminent['scadenza_dt'] <= today + timedelta(days=7)) &
            (df_imminent['tipo'] == 'Uscita')
        ]
        if not imminent_alert.empty:
            st.warning(f"⚠️ **Attenzione:** Hai **{len(imminent_alert)} pagamento/i in scadenza** nei prossimi 7 giorni per un totale di **€ {imminent_alert['importo'].sum():,.2f}**! Controlla la sezione Scadenze.")

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        saldo_class = "text-positive" if saldo_netto >= 0 else "text-negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Saldo Netto Periodo</div>
            <div class="metric-value {saldo_class}">€ {saldo_netto:,.2f}</div>
            <div class="metric-subtitle text-neutral">Margine: {saving_rate:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Totale Entrate Incassate</div>
            <div class="metric-value text-positive">€ {tot_entrate:,.2f}</div>
            <div class="metric-subtitle text-neutral">{len(df_completed[df_completed['tipo'] == 'Entrata']) if not df_completed.empty else 0} transazioni</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Totale Spese Sostenute</div>
            <div class="metric-value text-negative">€ {tot_uscite:,.2f}</div>
            <div class="metric-subtitle text-neutral">{len(df_completed[df_completed['tipo'] == 'Uscita']) if not df_completed.empty else 0} transazioni</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Uscite in Scadenza / Sospeso</div>
            <div class="metric-value text-warning">€ {pending_uscite:,.2f}</div>
            <div class="metric-subtitle text-positive">Entrate attese: € {pending_entrate:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Grafici Principali
    g_col1, g_col2 = st.columns([3, 2])
    
    with g_col1:
        st.subheader("📈 Andamento Entrate vs Uscite nel Tempo")
        if not df_completed.empty:
            df_chart = df_completed.copy()
            df_chart['periodo'] = df_chart['data'].dt.to_period('M').astype(str)
            df_grouped = df_chart.groupby(['periodo', 'tipo'])['importo'].sum().reset_index()
            
            fig = px.bar(
                df_grouped, 
                x='periodo', 
                y='importo', 
                color='tipo',
                barmode='group',
                color_discrete_map={'Entrata': '#10B981', 'Uscita': '#EF4444'},
                labels={'periodo': 'Mese', 'importo': 'Importo (€)', 'tipo': 'Tipo Movimento'},
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nessuna transazione completata nel periodo selezionato.")

    with g_col2:
        st.subheader("🍩 Ripartizione Spese per Categoria")
        if not df_completed.empty:
            df_exp = df_completed[df_completed['tipo'] == 'Uscita']
            if not df_exp.empty:
                exp_grouped = df_exp.groupby('categoria')['importo'].sum().reset_index()
                fig_donut = px.pie(
                    exp_grouped,
                    values='importo',
                    names='categoria',
                    hole=0.55,
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    template="plotly_dark"
                )
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                fig_donut.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("Nessuna spesa registrata nel periodo.")
        else:
            st.info("Nessun dato disponibile.")

    # Sezione Ultime Transazioni
    st.markdown("### 🕒 Ultime Transazioni Registrate")
    if not df_all.empty:
        display_cols = ['data', 'tipo', 'categoria', 'descrizione', 'importo', 'metodo_pagamento', 'stato']
        df_preview = df_all[display_cols].head(8).copy()
        df_preview['data'] = df_preview['data'].dt.strftime('%d/%m/%Y')
        df_preview['importo'] = df_preview['importo'].apply(lambda x: f"€ {x:,.2f}")
        
        st.dataframe(
            df_preview,
            use_container_width=True,
            hide_index=True,
            column_config={
                "data": st.column_config.TextColumn("Data"),
                "tipo": st.column_config.TextColumn("Tipo"),
                "categoria": st.column_config.TextColumn("Categoria"),
                "descrizione": st.column_config.TextColumn("Descrizione"),
                "importo": st.column_config.TextColumn("Importo"),
                "metodo_pagamento": st.column_config.TextColumn("Metodo"),
                "stato": st.column_config.TextColumn("Stato")
            }
        )
    else:
        st.info("Non ci sono transazioni da visualizzare.")

# ==============================================================================
# 2. GESTIONE TRANSAZIONI
# ==============================================================================
elif menu == "💳 Gestione Transazioni":
    st.title("💳 Gestione Transazioni")
    st.caption("Aggiungi nuove entrate o spese, filtra lo storico e gestisci i movimenti.")
    
    tab_new, tab_list, tab_edit = st.tabs(["➕ Nuova Transazione", "📋 Registro Completo", "✏️ Modifica / Elimina"])
    
    # TAB: Nuova Transazione
    with tab_new:
        with st.form("form_add_transaction", clear_on_submit=True):
            st.subheader("Registra un Nuovo Movimento")
            f_col1, f_col2, f_col3 = st.columns(3)
            
            tipo = f_col1.radio("Tipo Movimento", ["Uscita", "Entrata"], horizontal=True)
            cats = get_categories(tipo=tipo)
            categoria = f_col2.selectbox("Categoria", cats if cats else ["Generale"])
            data_movimento = f_col3.date_input("Data Transazione", date.today())
            
            f_col4, f_col5, f_col6 = st.columns(3)
            descrizione = f_col4.text_input("Descrizione / Beneficiario *", placeholder="Es. Fattura Cliente Alfa, Cancelleria, AWS...")
            importo = f_col5.number_input("Importo (€) *", min_value=0.01, step=1.00, format="%.2f")
            metodo = f_col6.selectbox("Metodo di Pagamento", ["Bonifico", "Carta di Credito", "PayPal", "Contanti", "RiBa / Addebito SEPA", "Altro"])
            
            f_col7, f_col8, f_col9 = st.columns(3)
            stato = f_col7.selectbox("Stato Pagamento", ["Completato", "In attesa", "Programmato"])
            scadenza = f_col8.date_input("Data Scadenza (opzionale)", value=None)
            note = f_col9.text_input("Note aggiuntive", placeholder="Es. N. Fattura, rif. contratto...")
            
            submit = st.form_submit_button("💾 Salva Transazione", use_container_width=True)
            if submit:
                if not descrizione.strip():
                    st.error("Il campo 'Descrizione' è obbligatorio.")
                elif importo <= 0:
                    st.error("L'importo deve essere maggiore di zero.")
                else:
                    add_transaction(
                        data=data_movimento,
                        tipo=tipo,
                        categoria=categoria,
                        descrizione=descrizione.strip(),
                        importo=importo,
                        metodo_pagamento=metodo,
                        stato=stato,
                        scadenza=str(scadenza) if scadenza else "",
                        note=note.strip()
                    )
                    st.success(f"Transazione '{descrizione}' di € {importo:,.2f} registrata con successo!")
                    st.rerun()

    # TAB: Registro Completo con Filtri
    with tab_list:
        st.subheader("Filtri Ricerca Avanzata")
        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        search_query = r_c1.text_input("Cerca per descrizione / note", placeholder="Es. fornitore o parola chiave...")
        filter_tipo = r_c2.selectbox("Filtra per Tipo", ["Tutti", "Entrata", "Uscita"])
        all_cats = ["Tutte"] + get_categories()
        filter_cat = r_c3.selectbox("Filtra per Categoria", all_cats)
        filter_stat = r_c4.selectbox("Filtra per Stato", ["Tutti", "Completato", "In attesa", "Programmato"])
        
        df_filtered = get_transactions_df(
            start_date=filter_start,
            end_date=filter_end,
            tipo=filter_tipo,
            categoria=filter_cat,
            stato=filter_stat
        )
        
        if search_query.strip() and not df_filtered.empty:
            q = search_query.lower()
            df_filtered = df_filtered[
                df_filtered['descrizione'].str.lower().str.contains(q, na=False) |
                df_filtered['note'].str.lower().str.contains(q, na=False)
            ]
            
        if not df_filtered.empty:
            st.write(f"Trovate **{len(df_filtered)}** transazioni:")
            
            df_show = df_filtered.copy()
            df_show['data_str'] = df_show['data'].dt.strftime('%d/%m/%Y')
            df_show['importo_fmt'] = df_show['importo'].apply(lambda x: f"€ {x:,.2f}")
            
            st.dataframe(
                df_show[['id', 'data_str', 'tipo', 'categoria', 'descrizione', 'importo_fmt', 'metodo_pagamento', 'stato', 'scadenza', 'note']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "data_str": st.column_config.TextColumn("Data"),
                    "tipo": st.column_config.TextColumn("Tipo"),
                    "categoria": st.column_config.TextColumn("Categoria"),
                    "descrizione": st.column_config.TextColumn("Descrizione"),
                    "importo_fmt": st.column_config.TextColumn("Importo"),
                    "metodo_pagamento": st.column_config.TextColumn("Metodo"),
                    "stato": st.column_config.TextColumn("Stato"),
                    "scadenza": st.column_config.TextColumn("Scadenza"),
                    "note": st.column_config.TextColumn("Note")
                }
            )
        else:
            st.info("Nessuna transazione trovata con i filtri applicati.")

    # TAB: Modifica / Elimina
    with tab_edit:
        st.subheader("Modifica o Cancella una Transazione")
        all_df = get_transactions_df()
        if not all_df.empty:
            # Lista di opzioni per la selezione
            tx_options = {
                f"ID {row['id']} - {row['data'].strftime('%d/%m/%Y')} - {row['tipo']} - € {row['importo']:,.2f} ({row['descrizione']})": row['id']
                for _, row in all_df.iterrows()
            }
            selected_label = st.selectbox("Seleziona la transazione da modificare", list(tx_options.keys()))
            selected_id = tx_options[selected_label]
            tx_row = all_df[all_df['id'] == selected_id].iloc[0]
            
            with st.form("edit_form"):
                e_col1, e_col2, e_col3 = st.columns(3)
                e_tipo = e_col1.radio("Tipo", ["Uscita", "Entrata"], index=0 if tx_row['tipo'] == 'Uscita' else 1, horizontal=True)
                available_cats = get_categories(tipo=e_tipo)
                cat_index = available_cats.index(tx_row['categoria']) if tx_row['categoria'] in available_cats else 0
                e_cat = e_col2.selectbox("Categoria", available_cats, index=cat_index)
                e_data = e_col3.date_input("Data", tx_row['data'].date())
                
                e_col4, e_col5, e_col6 = st.columns(3)
                e_desc = e_col4.text_input("Descrizione", value=tx_row['descrizione'])
                e_imp = e_col5.number_input("Importo (€)", value=float(tx_row['importo']), min_value=0.01, step=1.0)
                methods = ["Bonifico", "Carta di Credito", "PayPal", "Contanti", "RiBa / Addebito SEPA", "Altro"]
                m_idx = methods.index(tx_row['metodo_pagamento']) if tx_row['metodo_pagamento'] in methods else 0
                e_metodo = e_col6.selectbox("Metodo", methods, index=m_idx)
                
                e_col7, e_col8, e_col9 = st.columns(3)
                states = ["Completato", "In attesa", "Programmato"]
                s_idx = states.index(tx_row['stato']) if tx_row['stato'] in states else 0
                e_stato = e_col7.selectbox("Stato", states, index=s_idx)
                
                scad_val = None
                if tx_row['scadenza']:
                    try:
                        scad_val = datetime.strptime(str(tx_row['scadenza']), '%Y-%m-%d').date()
                    except:
                        scad_val = None
                e_scad = e_col8.date_input("Scadenza", value=scad_val)
                e_note = e_col9.text_input("Note", value=str(tx_row['note']) if tx_row['note'] else "")
                
                b1, b2 = st.columns(2)
                btn_save = b1.form_submit_button("💾 Aggiorna Modifiche", use_container_width=True)
                btn_del = b2.form_submit_button("🗑️ Elimina Definitivamente", use_container_width=True)
                
                if btn_save:
                    update_transaction(
                        trans_id=selected_id,
                        data=e_data,
                        tipo=e_tipo,
                        categoria=e_cat,
                        descrizione=e_desc.strip(),
                        importo=e_imp,
                        metodo_pagamento=e_metodo,
                        stato=e_stato,
                        scadenza=str(e_scad) if e_scad else "",
                        note=e_note.strip()
                    )
                    st.success("Transazione aggiornata con successo!")
                    st.rerun()
                    
                if btn_del:
                    delete_transaction(selected_id)
                    st.warning(f"Transazione ID {selected_id} eliminata.")
                    st.rerun()
        else:
            st.info("Nessuna transazione presente nel database.")

# ==============================================================================
# 3. SCADENZE & FLUSSO DI CASSA (CASH FLOW)
# ==============================================================================
elif menu == "⏳ Scadenze & Flusso di Cassa":
    st.title("⏳ Scadenze & Previsione Cash Flow")
    st.caption("Pianifica i pagamenti futuri, monitora le scadenze e anticipa la liquidità.")
    
    df_all_raw = get_transactions_df()
    df_pending = df_all_raw[df_all_raw['stato'].isin(['In attesa', 'Programmato'])].copy()
    
    if not df_pending.empty:
        df_pending['scadenza_dt'] = pd.to_datetime(df_pending['scadenza'], errors='coerce').dt.date
        df_pending['giorni_rimasti'] = df_pending['scadenza_dt'].apply(lambda d: (d - today).days if pd.notna(d) else 999)
        
        # Filtri per urgenza
        scaduti = df_pending[df_pending['giorni_rimasti'] < 0]
        imminenti = df_pending[(df_pending['giorni_rimasti'] >= 0) & (df_pending['giorni_rimasti'] <= 7)]
        futuri = df_pending[df_pending['giorni_rimasti'] > 7]
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔴 Scaduti da Saldare</div>
            <div class="metric-value text-negative">{len(scaduti)}</div>
            <div class="metric-subtitle">Totale: € {scaduti['importo'].sum():,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col2.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🟡 In Scadenza (Prossimi 7 gg)</div>
            <div class="metric-value text-warning">{len(imminenti)}</div>
            <div class="metric-subtitle">Totale: € {imminenti['importo'].sum():,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        col3.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔵 Scadenze Future (> 7 gg)</div>
            <div class="metric-value text-neutral">{len(futuri)}</div>
            <div class="metric-subtitle">Totale: € {futuri['importo'].sum():,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Lista Pagamenti & Incassi da Gestire")
        
        for idx, row in df_pending.sort_values(by='giorni_rimasti').iterrows():
            with st.container():
                c_info, c_imp, c_act = st.columns([3, 1.5, 1.2])
                
                # Badge di stato
                if row['giorni_rimasti'] < 0:
                    badge = f"<span class='badge-urgent'>SCADUTO da {-row['giorni_rimasti']} gg</span>"
                elif row['giorni_rimasti'] <= 7:
                    badge = f"<span class='badge-upcoming'>Scade tra {row['giorni_rimasti']} gg</span>"
                else:
                    badge = f"<span class='badge-future'>Scadenza tra {row['giorni_rimasti']} gg</span>"
                    
                tipo_icon = "🟢 Incasso" if row['tipo'] == 'Entrata' else "🔴 Uscita"
                scad_str = row['scadenza_dt'].strftime('%d/%m/%Y') if pd.notna(row['scadenza_dt']) else "N.D."
                
                c_info.markdown(f"""
                **{row['descrizione']}** ({tipo_icon}) {badge}  
                *Categoria:* {row['categoria']} | *Data Scadenza:* **{scad_str}** | *Stato attuale:* {row['stato']}  
                <span style="color: #64748B; font-size: 0.85rem;">Note: {row['note'] if row['note'] else 'Nessuna nota'}</span>
                """, unsafe_allow_html=True)
                
                imp_color = "text-positive" if row['tipo'] == 'Entrata' else "text-negative"
                c_imp.markdown(f"<div style='font-size: 1.4rem; font-weight: bold;' class='{imp_color}'>€ {row['importo']:,.2f}</div>", unsafe_allow_html=True)
                
                if c_act.button("✅ Salda Ora", key=f"pay_{row['id']}", use_container_width=True, help="Segna questa transazione come 'Completato'"):
                    update_transaction(
                        trans_id=row['id'],
                        data=date.today(),
                        tipo=row['tipo'],
                        categoria=row['categoria'],
                        descrizione=row['descrizione'],
                        importo=row['importo'],
                        metodo_pagamento=row['metodo_pagamento'],
                        stato="Completato",
                        scadenza=row['scadenza'],
                        note=f"{row['note']} (Saldato il {date.today().strftime('%d/%m/%Y')})".strip()
                    )
                    st.success("Marcato come completato!")
                    st.rerun()
                    
                st.markdown("<hr style='margin: 8px 0; border-color: #334155;'>", unsafe_allow_html=True)
    else:
        st.success("🎉 Fantastico! Non hai nessun pagamento in attesa o scadenza programmata.")

    # Simulatore Saldo Futuro (Cash Flow Proiezione)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🔮 Simulazione Saldo Cassa Futuro")
    st.caption("Calcolo del saldo previsto sommando gli incassi programmati e sottraendo le uscite previste.")
    
    df_comp = df_all_raw[df_all_raw['stato'] == 'Completato']
    saldo_attuale = (df_comp[df_comp['tipo'] == 'Entrata']['importo'].sum() - 
                     df_comp[df_comp['tipo'] == 'Uscita']['importo'].sum()) if not df_comp.empty else 0.0
                     
    if not df_pending.empty:
        entrate_future = df_pending[df_pending['tipo'] == 'Entrata']['importo'].sum()
        uscite_future = df_pending[df_pending['tipo'] == 'Uscita']['importo'].sum()
        saldo_proiettato = saldo_attuale + entrate_future - uscite_future
        
        sim1, sim2, sim3 = st.columns(3)
        sim1.metric("Saldo Attuale Cassa", f"€ {saldo_attuale:,.2f}")
        sim2.metric("Variazione Netta Prevista", f"€ {(entrate_future - uscite_future):,.2f}", delta=f"{entrate_future - uscite_future:,.2f}")
        sim3.metric("Saldo Futuro Stimato", f"€ {saldo_proiettato:,.2f}")
    else:
        st.metric("Saldo Attuale Cassa", f"€ {saldo_attuale:,.2f}")

# ==============================================================================
# 4. BUDGET PER CATEGORIA
# ==============================================================================
elif menu == "🎯 Budget per Categoria":
    st.title("🎯 Controllo Budget Mensile")
    st.caption("Imposta tetti di spesa per ciascuna categoria e monitora in tempo reale gli scostamenti.")
    
    budgets_df = get_budgets_df()
    
    # Calcola le spese del mese corrente per ogni categoria
    df_curr_month = get_transactions_df(
        start_date=today.replace(day=1),
        end_date=today,
        tipo="Uscita",
        stato="Completato"
    )
    
    spese_per_cat = df_curr_month.groupby('categoria')['importo'].sum().to_dict() if not df_curr_month.empty else {}
    
    b_col1, b_col2 = st.columns([2.5, 1.5])
    
    with b_col1:
        st.subheader("Stato Budget Mese Corrente")
        if not budgets_df.empty:
            for _, b_row in budgets_df.iterrows():
                cat = b_row['categoria']
                b_max = float(b_row['budget_mensile'])
                speso = spese_per_cat.get(cat, 0.0)
                perc = (speso / b_max) * 100 if b_max > 0 else 0
                
                # Barra e colori
                st.markdown(f"**{cat}** — Spesi: **€ {speso:,.2f}** / Budget: **€ {b_max:,.2f}** ({perc:.1f}%)")
                
                if perc >= 100:
                    st.progress(1.0)
                    st.markdown(f"<span style='color: #EF4444; font-weight: bold;'>🚨 Budget superato di € {(speso - b_max):,.2f}!</span>", unsafe_allow_html=True)
                elif perc >= 80:
                    st.progress(min(perc / 100, 1.0))
                    st.markdown(f"<span style='color: #F59E0B;'>⚠️ Attenzione: sei all'80%+ del budget allocato.</span>", unsafe_allow_html=True)
                else:
                    st.progress(min(perc / 100, 1.0))
                    st.markdown(f"<span style='color: #10B981;'>✅ Disponibilità residua: € {(b_max - speso):,.2f}</span>", unsafe_allow_html=True)
                    
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("Nessun budget ancora configurato. Utilizza il modulo a destra per impostarne uno.")

    with b_col2:
        st.subheader("⚙️ Imposta Budget Categoria")
        with st.form("set_budget_form"):
            expense_cats = get_categories(tipo="Uscita")
            b_cat = st.selectbox("Categoria di Spesa", expense_cats)
            
            # Cerca valore esistente se presente
            curr_budget_val = 100.0
            if not budgets_df.empty and b_cat in budgets_df['categoria'].values:
                curr_budget_val = float(budgets_df[budgets_df['categoria'] == b_cat]['budget_mensile'].iloc[0])
                
            b_amount = st.number_input("Budget Mensile Limite (€)", value=curr_budget_val, min_value=10.0, step=25.0)
            
            b_sub = st.form_submit_button("💾 Salva Budget", use_container_width=True)
            if b_sub:
                set_budget(b_cat, b_amount)
                st.success(f"Budget per '{b_cat}' fissato a € {b_amount:,.2f} / mese!")
                st.rerun()

# ==============================================================================
# 5. REPORT & ESPORTAZIONE
# ==============================================================================
elif menu == "📑 Report & Esportazione":
    st.title("📑 Report & Esportazione Dati")
    st.caption("Scarica i dati contabili in formato Excel o CSV compatibile con commercialisti e software gestionali.")
    
    df_export = get_transactions_df()
    
    if not df_export.empty:
        # Statistiche di Sintesi Annuali
        df_export['anno'] = df_export['data'].dt.year
        df_export['mese'] = df_export['data'].dt.strftime('%m-%Y')
        
        st.subheader("📊 Riepilogo Mensile delle Entrate e Uscite")
        pivot = pd.pivot_table(
            df_export[df_export['stato'] == 'Completato'],
            values='importo',
            index='mese',
            columns='tipo',
            aggfunc='sum',
            fill_value=0.0
        ).reset_index()
        
        if 'Entrata' not in pivot.columns:
            pivot['Entrata'] = 0.0
        if 'Uscita' not in pivot.columns:
            pivot['Uscita'] = 0.0
            
        pivot['Utile Netto'] = pivot['Entrata'] - pivot['Uscita']
        
        # Formattazione per visualizzazione
        pivot_disp = pivot.copy()
        pivot_disp['Entrata'] = pivot_disp['Entrata'].apply(lambda x: f"€ {x:,.2f}")
        pivot_disp['Uscita'] = pivot_disp['Uscita'].apply(lambda x: f"€ {x:,.2f}")
        pivot_disp['Utile Netto'] = pivot_disp['Utile Netto'].apply(lambda x: f"€ {x:,.2f}")
        
        st.dataframe(pivot_disp, use_container_width=True, hide_index=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📥 Download File")
        
        d_col1, d_col2 = st.columns(2)
        
        # Esportazione CSV
        csv_buffer = io.StringIO()
        df_export.to_csv(csv_buffer, index=False, sep=';', decimal=',')
        d_col1.download_button(
            label="📄 Scarica File CSV (Separatore ';')",
            data=csv_buffer.getvalue().encode('utf-8-sig'),
            file_name=f"finpulse_movimenti_{date.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Esportazione Excel Multi-Foglio
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Tutte_Transazioni', index=False)
            pivot.to_excel(writer, sheet_name='Riepilogo_Mensile', index=False)
            get_budgets_df().to_excel(writer, sheet_name='Budget_Impostati', index=False)
            
        d_col2.download_button(
            label="📊 Scarica File Excel (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name=f"finpulse_report_completo_{date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("Nessuna transazione registrata da esportare.")

# ==============================================================================
# 6. CATEGORIE & IMPOSTAZIONI
# ==============================================================================
elif menu == "⚙️ Categorie & Dati":
    st.title("⚙️ Categorie & Configurazione")
    st.caption("Personalizza le categorie di spesa ed entrata per adattare il software alla tua attività o vita personale.")
    
    c_tab1, c_tab2, c_tab3 = st.tabs(["🏷️ Gestione Categorie", "☁️ Come Mettere Online", "🗑️ Reset"])
    
    with c_tab1:
        set1, set2 = st.columns(2)
        
        with set1:
            st.subheader("Aggiungi Nuova Categoria")
            with st.form("new_cat_form", clear_on_submit=True):
                new_cat_tipo = st.radio("Tipo Categoria", ["Uscita", "Entrata"], horizontal=True)
                new_cat_nome = st.text_input("Nome Categoria", placeholder="Es. Software AI, Auto aziendale, Corsi...")
                add_btn = st.form_submit_button("➕ Aggiungi Categoria", use_container_width=True)
                if add_btn:
                    if new_cat_nome.strip():
                        ok = add_category(new_cat_tipo, new_cat_nome.strip())
                        if ok:
                            st.success(f"Categoria '{new_cat_nome}' aggiunta con successo!")
                            st.rerun()
                        else:
                            st.error("Questa categoria esiste già!")
                    else:
                        st.error("Inserisci un nome valido.")
                        
        with set2:
            st.subheader("Elenco Categorie Esistenti")
            e_col, u_col = st.columns(2)
            with e_col:
                st.markdown("**🟢 Entrate**")
                for c in get_categories(tipo="Entrata"):
                    st.write(f"• {c}")
            with u_col:
                st.markdown("**🔴 Uscite**")
                for c in get_categories(tipo="Uscita"):
                    st.write(f"• {c}")

    with c_tab2:
        st.subheader("🚀 Come Pubblicare Questo Software Online Gratis")
        st.markdown("""
        Puoi pubblicare questa web app online in **meno di 3 minuti** a costo zero tramite **Streamlit Community Cloud**:
        
        1. **Crea un repository su GitHub** (es. `gestionale-finanze`).
        2. **Carica i file del progetto** (`app.py`, `database.py`, `sample_data.py`, `requirements.txt`, cartella `.streamlit`).
        3. Vai su **[share.streamlit.io](https://share.streamlit.io)** e accedi con il tuo account GitHub.
        4. Clicca su **"New app"**, seleziona il tuo repository, il branch (`main`) e come file principale `app.py`.
        5. Clicca su **"Deploy!"**.
        
        🎉 In pochi istanti la tua applicazione sarà accessibile da qualsiasi computer, smartphone o tablet con il tuo link personalizzato HTTPS!
        """)

    with c_tab3:
        st.subheader("⚠️ Reset e Manutenzione Database")
        st.warning("Il ripristino sovrascriverà tutti i dati correnti con i dati demo di test.")
        if st.button("🔴 Ripristina Database con Dati di Esempio", use_container_width=True):
            reset_db_with_sample_data()
            st.success("Database ripristinato con dati demo.")
            st.rerun()
