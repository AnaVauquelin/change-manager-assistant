import streamlit as st
import requests
import pandas as pd
import re

st.set_page_config(page_title="Change Manager Assistant", layout="wide")

# --- REFINED CSS ---
st.markdown("### 🚀 NJ Change Manager Assistant")
#st.markdown('<div class="main-title">🚀 NJ Change Manager Assistant</div>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)



# 🚀 GLOBAL WORKSPACE DESCRIPTION (Moved above tabs)
with st.expander("ℹ️ About This Workspace & NJ DGE Compliance Context", expanded=False):
    st.markdown("""
**What this application does:**

The **Change Manager Assistant** helps track software releases to meet the strict compliance rules of the **New Jersey Division of Gaming Enforcement (DGE)**.

* **Fixes Export Errors:** Prevents formatting and line-break errors that happen when exporting tables from Confluence or PDFs.
* **Reads Screenshots (OCR):** Uses computer vision to read, extract, and log release data directly from uploaded image tables.
* **Tracks Compliance Tags:** Automatically categorizes and monitors your **`[ND]`**, **`[RN]`**, and **`[ERN]`** tickets.
* **Multi-Month History:** Combines data across multiple months to find bottlenecks and monitor ticket statuses (`SENT`, `APPROVED`, `DEPLOYED`).
""")

st.markdown("<br>", unsafe_allow_html=True)




tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🚀 Collector", "📖 Docs", "📊 Dashboard", "✉️ Email Gen", "🔍 ID Extractor", "📊 Manifest Analytics", "✅ EX Evaluator"])
#tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🚀 Collector", "📖 Docs", "📊 Dashboard", "✉️ Email Gen", "🔍 ID Extractor", "📊 Manifest Analytics"])

if 'tickets' not in st.session_state: st.session_state.tickets = []
















# --- TAB 1: COLLECTOR ---
with tab1:
    st.markdown("### 🆔 IDs Collector")
    st.markdown("<br>", unsafe_allow_html=True)

    ticket_input = st.text_input("Enter Jira ID(s):", placeholder="GK-18175")
    
    if st.button("Collect Data", type="primary"):
        if ticket_input:
            with st.spinner("Retrieving ticket intelligence from Jira matrix..."):
                try:
                    res = requests.post("http://127.0.0.1:5001/get-notes", json={"ticket_id": ticket_input})
                    if res.status_code == 200: 
                        st.session_state.tickets = res.json()['tickets']
                        st.success("Data sync complete!")
                except Exception as e:
                    st.error(f"Failed to connect to the backend core pipeline: {str(e)}")

    for t in st.session_state.tickets:
        header = f"🎫 {t['ticket_id']} | 🏷️ {t['status']}"
        with st.expander(header, expanded=True):
            st.info(t['policy'])
            
            # 🎯 1. Add clickable direct shortcut link for the main parent ticket
            st.link_button(f"🔗 Open Main Ticket {t['ticket_id']} in Jira", f"https://jira.gosystem.io/browse/{t['ticket_id']}", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("### 📋 Summary")
            st.text_input("S", value=t['summary'], key=f"s_{t['ticket_id']}", label_visibility="collapsed")
            st.markdown("### 📝 Release Notes")
            st.text_area("N", value=t['release_notes'], height=250, key=f"n_{t['ticket_id']}", label_visibility="collapsed")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### 🆔 NJ Change IDs")
                
                raw_ids = t['nj_change_ids']
                if raw_ids:
                    split_lines = re.split(r'(?=\b(?:RN|ND|EX)-\d{2}\b)', raw_ids)
                    html_lines = []
                    
                    for line in split_lines:
                        clean_line = line.strip().strip(",")
                        if clean_line:
                            formatted_line = re.sub(
                                r'\b((?:RN|ND|EX)-\d{2})\b', 
                                r'<strong style="color: #ff4b4b; font-size: 19px; background-color: rgba(255, 75, 75, 0.1); padding: 2px 6px; border-radius: 4px;">\1</strong>', 
                                clean_line
                            )
                            html_lines.append(f'<div style="margin-bottom: 12px; line-height: 1.5; color: #e0e0e0; font-size: 16px;">{formatted_line}</div>')
                    
                    container_html = f"""
                    <div style="background-color: #1e1e1e; border-radius: 5px; padding: 15px; border: 1px solid #2d2d2d; min-height: 150px;">
                        {"".join(html_lines)}
                    </div>
                    """
                    st.markdown(container_html, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="background-color: #1e1e1e; border-radius: 5px; padding: 15px; color: #757575; font-style: italic; border: 1px solid #2d2d2d;">No compliance mappings listed.</div>', unsafe_allow_html=True)
                
            with c2:
                st.markdown("### 🔗 Dependencies NJ")
                st.text_area("D", value=t['dependencies_nj'], height=150, key=f"dp_{t['ticket_id']}", label_visibility="collapsed")
            
            if t.get('linked_tickets'):
                st.markdown("### 🧱 Linked Tickets (Contains)")
                for link in t['linked_tickets']:
                    raw_id_field = link.get("NJ IDs", "")
                    all_ids = re.findall(r'\b[A-Z0-9]+-\d+\b', raw_id_field)
                    
                    filtered_ids = [cid for cid in all_ids if not cid.startswith("NJ-")]
                    
                    if filtered_ids:
                        display_ids = "".join([
                            f'<div style="color: #ff4b4b; font-weight: bold; font-size: 16px; margin-bottom: 4px;">{cid}</div>' 
                            for cid in filtered_ids
                        ])
                    else:
                        display_ids = '<div style="color: #888888; font-weight: bold; font-size: 16px;">None</div>'

                    # 🎯 2. Wrap the child ticket ID in a clear, high-visibility HTML hyperlink
                    clean_child_id = str(link["Ticket"]).strip()
                    clickable_child_title = f'<a href="https://jira.gosystem.io/browse/{clean_child_id}" target="_blank" style="color: #ff4b4b; font-weight: bold; text-decoration: none;">{clean_child_id} ↗</a>'

                    st.markdown(f'''
                        <div style="background-color: #1e1e1e; border-radius: 6px; padding: 12px 18px; margin-bottom: 8px; border: 1px solid #2d2d2d;">
                            <table style="width:100%; border:none; border-collapse:collapse; background:transparent; margin:0; padding:0;">
                                <tr style="border:none; background:transparent;">
                                    <td style="width:80%; vertical-align:top; border:none; color:#ffffff; line-height:1.6; padding:0;">
                                        <span style="color: #aaaaaa; font-size: 13px; font-weight: bold;">Ticket:</span> 
                                        <strong style="font-size: 15px;">{clickable_child_title}</strong><br>
                                        <span style="color: #aaaaaa; font-size: 13px; font-weight: bold;">Description:</span> 
                                        <span style="font-size: 15px; color: #eeeeee;">{link["Summary"]}</span>
                                    </td>
                                    <td style="width:20%; vertical-align:middle; text-align:right; border:none; padding:0;">
                                        {display_ids}
                                    </td>
                                </tr>
                            </table>
                        </div>
                    ''', unsafe_allow_html=True)
















# --- TAB 2: DOCS ---
with tab2:
    st.markdown("### 📖 Resources & Documentation")
    #st.markdown('<div class="main-title">📖 Resources & Documentation</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🤖 Gemini Assistant")
        st.link_button("🚀 Open Gemini", "https://gemini.google.com/gem/1Sqda5Eq9EVScdD4sPJeuiTkXb2t78FoG?usp=sharing", use_container_width=True)
    with c2:
        st.subheader("📜 Release Policy")
        st.link_button("📑 Confluence Docs", "https://wiki.gosystem.io/x/YgdrNQ", use_container_width=True)






# --- TAB 3: DASHBOARD ---
with tab3:
    st.markdown("### 📊 Stats & Monitoring")
    #st.markdown('<div class="main-title">📊 Stats & Monitoring</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Styled Link Button for NJ Dashboard
    dash_url = "https://jira.gosystem.io/secure/Dashboard.jspa?selectPageId=49406"
    st.link_button("📊 NJ Dashboard", dash_url, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Refresh Stats", type="primary"):
        # The spinner keeps the loading animation right here under the button
        with st.spinner("Fetching live tracking metrics from Jira..."):
            try:
                r = requests.get("http://127.0.0.1:5001/get-dashboard-stats")
                if r.status_code == 200:
                    stats = r.json()['stats']
                    cols = st.columns(len(stats))
                    for i, s in enumerate(stats):
                        cols[i].metric(label=s['status'], value=s['count'])
            except Exception as e:
                st.error(f"Failed to fetch dashboard metrics: {str(e)}")









# --- TAB 4: EMAIL GEN ---
with tab4:
    st.markdown("### ✉️ Regulator Email Generator")
    #st.markdown('<div class="main-title">✉️ Regulator Email Generator</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if 'email_bundle_tickets' not in st.session_state:
        st.session_state.email_bundle_tickets = []

    st.subheader("📋 Bundle RNP Tickets for Consolidated Matrix")
    bundle_input = st.text_input(
        "Enter RNP Jira IDs separated by commas:", 
        placeholder="RNP-1856, RNP-1855",
        key="email_gen_bundle_input"
    )
    
    if st.button("Fetch & Aggregate RNP Data Points", type="primary", key="fetch_email_bundle_btn"):
        if bundle_input:
            requested_ids = [tk.strip() for tk in bundle_input.split(",") if tk.strip()]
            
            # CRITICAL FIX: Flush out previous values to prevent data cross-contamination
            st.session_state.email_bundle_tickets = []
            fetched_bundle = []
            
            with st.spinner("Extracting parameters and points 1-15 from RNP schemas..."):
                for t_id in requested_ids:
                    try:
                        res = requests.post("http://127.0.0.1:5001/get-notes", json={"ticket_id": t_id})
                        if res.status_code == 200:
                            data_payload = res.json()
                            ticket_data = data_payload['tickets'][0] if ('tickets' in data_payload and data_payload['tickets']) else data_payload
                            fetched_bundle.append(ticket_data)
                    except Exception as e:
                        st.error(f"Error gathering ticket {t_id}: {str(e)}")
            
            if fetched_bundle:
                st.session_state.email_bundle_tickets = fetched_bundle
                st.success(f"Successfully loaded and aggregated {len(fetched_bundle)} RNP matrices!")

    if st.session_state.email_bundle_tickets:
        st.markdown("---")
        st.subheader("📝 Edit Combined RNP Content Matrices")
        
        # Comprehensive parsed lists for lines 1 to 15 across any loaded RNP tickets
        aggregated_rows_data = {i: [] for i in range(2, 16)}
        combined_subject_ids = []
        
        # Parse out rows fields from incoming dataset
        for t in st.session_state.email_bundle_tickets:
            raw_ids = t.get('subject_ids', t.get('nj_change_ids', t.get('ticket_id', '')))
            if not raw_ids and 'summary' in t:
                found_tags = re.findall(r'(IG-RN-\d+|IG-ND-\d+)', t['summary'])
                if found_tags:
                    raw_ids = found_tags
            
            if raw_ids:
                if isinstance(raw_ids, list):
                    for item in raw_ids:
                        clean_item = str(item).strip("[]'\" ")
                        if clean_item and clean_item not in combined_subject_ids:
                            combined_subject_ids.append(clean_item)
                else:
                    for item in str(raw_ids).replace('[', '').replace(']', '').split(','):
                        clean_item = item.strip()
                        if clean_item and "DATABASE" not in clean_item.upper() and clean_item not in combined_subject_ids:
                            combined_subject_ids.append(clean_item)

            body_text = t.get('release_notes', '') or t.get('email_body', '')
            if body_text:
                body_text = str(body_text).replace('\r', '')
                
                for r_num in range(2, 16):
                    next_num = r_num + 1
                    if next_num <= 15:
                        pattern = rf"(?:^\s*|\s+|\n){r_num}\.\s*(.*?)(?=(?:\n\s*{next_num}\.|\s+{next_num}\.|$))"
                    else:
                        pattern = rf"(?:^\s*|\s+|\n){r_num}\.\s*(.*)$"
                    
                    match = re.search(pattern, body_text, re.DOTALL)
                    if match:
                        raw_val = match.group(1).strip().split('\n')[0].strip()
                        if raw_val and raw_val.upper() != "N/A":
                            sub_items = [item.strip() for item in raw_val.split(',') if item.strip()]
                            for sub_item in sub_items:
                                if sub_item not in aggregated_rows_data[r_num]:
                                    aggregated_rows_data[r_num].append(sub_item)

        if not combined_subject_ids:
            combined_subject_ids = [t.get('ticket_id', 'RNP') for t in st.session_state.email_bundle_tickets]

        default_subj_prefix = f"[{', '.join(combined_subject_ids)}]"
        editable_subject_prefix = st.text_input("Consolidated Subject Tags Prefix Layout:", value=default_subj_prefix, key="bundle_global_subj_prefix")

        st.markdown("#### 🧱 Row 1 Custom Features Matrix Setup")
        edited_features = []
        edited_descriptions = []
        ticket_keys_tracking = []

        for idx, t in enumerate(st.session_state.email_bundle_tickets):
            t_id = t.get('ticket_id', f'Ticket-{idx}')
            st.markdown(f"**Component Configuration: `{t_id}`**")
            
            body_text = t.get('release_notes', '') or t.get('email_body', '')
            if body_text:
                body_text = str(body_text).replace('\r', '')
                
            match_r1 = re.search(r"(?:^\s*|\s+|\n)1\.\s*(.*?)(?=(?:\n\s*2\.|\s+2\.|$))", body_text, re.DOTALL)
            line_1_content = match_r1.group(1).strip() if match_r1 else t.get('summary', '')

            raw_title_lower = t.get('summary', '').lower()
            raw_desc_lower = line_1_content.lower()

            if "evolution" in raw_title_lower or "evolution" in raw_desc_lower:
                simplified_feature = "Evolution Games Activation"
                simplified_desc = "Activated two games from the provider Evolution. More information is provided in the attached file"
            elif "open-bet" in raw_title_lower or "kambi" in raw_title_lower or "stake" in raw_title_lower or "free bet" in raw_desc_lower:
                simplified_feature = "Sportsbook Adjustment: Kambi Free Bet Stake Display"
                simplified_desc = "Updated the player sports history log to ensure the correct stake value is accurately displayed when a wager is placed using Kambi Free Bets. More information is provided in the attached file"
            elif "recaptcha" in raw_title_lower or "recaptcha" in raw_desc_lower or "whitelist" in raw_title_lower:
                simplified_feature = "Security Infrastructure: Whitelist reCAPTCHA Configuration"
                simplified_desc = "Implemented automated security parameter whitelist updates within reCAPTCHA to shield platform endpoints from malicious bot traffic. More information is provided in the attached file"
            elif "cage_management" in raw_title_lower or "cage tables" in raw_title_lower:
                simplified_feature = "Database Infrastructure - Cage Accounting Tables"
                simplified_desc = "Created dedicated back-end data tables to safely record and historicalize vault cashier ledger balances across environment hosts."
            elif "helm-charts" in raw_title_lower or "stands" in raw_title_lower:
                simplified_feature = "Environment Configuration Alignment"
                simplified_desc = "Updated back-end environment hosting configuration scripts to align deployment environments and reinforce core infrastructure stability."
            else:
                simplified_feature = t.get('summary', 'System Optimization Update')
                simplified_feature = re.sub(r'^[:\s\-\—\*\•\.]+|\s*-\s*Release Notes$', '', simplified_feature, flags=re.IGNORECASE).strip()
                
                clean_lines = [l.strip('* ').strip() for l in line_1_content.split('\n') if l.strip() and not l.strip().startswith('*ND-')]
                if clean_lines and len(clean_lines[0]) > 10:
                    simplified_desc = f"{clean_lines[0]}. More information is provided in the attached file"
                else:
                    simplified_desc = "Applied backend code logic updates to optimize performance data alignment strategies."

            c_feat, c_desc = st.columns([1, 2])
            with c_feat:
                f_val = st.text_input(f"Feature Name ({t_id}):", value=simplified_feature, key=f"b_feat_{t_id}_{idx}")
                edited_features.append(f_val)
                ticket_keys_tracking.append(t_id)
            with c_desc:
                d_val = st.text_area(f"Description Details ({t_id}):", value=simplified_desc, height=85, key=f"b_desc_{t_id}_{idx}")
                edited_descriptions.append(d_val)

        st.markdown("---")
        st.markdown("#### 📁 Aggregated Compliance Metadata Matrix Settings (Rows 2 - 15)")
        
        def get_row_default_val(row_index, fallback_txt="N/A"):
            items = aggregated_rows_data.get(row_index, [])
            clean_items = [i for i in items if i.upper() != "N/A" and i.strip() != ""]
            return ", ".join(clean_items) if clean_items else fallback_txt

        # CALCULATE NEXT WORKING BUSINESS DAY FOR POINT 5
        import datetime
        today = datetime.date.today()
        days_ahead = 3 if today.weekday() == 4 else 2 if today.weekday() == 5 else 1
        next_working_day = (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        col_edit1, col_edit2 = st.columns([1, 2])
        with col_edit1:
            editable_row2 = st.text_input("Row 2 Value (Type/Scope):", value=get_row_default_val(2), key="bundle_edit_row2")
            editable_row3 = st.text_input("Row 3 Value (Platform Components):", value=get_row_default_val(3), key="bundle_edit_deps")
        with col_edit2:
            editable_row4 = st.text_input("Row 4 Value (Deployment System):", value=get_row_default_val(4), key="bundle_edit_row4")
            editable_row5 = st.text_input("Row 5 Value (Execution Targets):", value=next_working_day, key="bundle_edit_row5")
            editable_row6 = st.text_input("Row 6 Value (Signed Off Verification):", value=get_row_default_val(6), key="bundle_edit_row6")

        c_low1, c_low2, c_low3 = st.columns(3)
        with c_low1:
            editable_r7 = st.text_input("Row 7 Text:", value=get_row_default_val(7), key="b_r7")
            editable_r8 = st.text_input("Row 8 Text:", value=get_row_default_val(8), key="b_r8")
            editable_r9 = st.text_input("Row 9 Text:", value=get_row_default_val(9), key="b_r9")
        with c_low2:
            editable_r10 = st.text_input("Row 10 Text:", value=get_row_default_val(10), key="b_r10")
            editable_r11 = st.text_input("Row 11 Text:", value=get_row_default_val(11), key="b_r11")
            editable_r12 = st.text_input("Row 12 Text:", value=get_row_default_val(12), key="b_r12")
        with c_low3:
            editable_r13 = st.text_input("Row 13 Text:", value=get_row_default_val(13), key="b_r13")
            editable_r14 = st.text_input("Row 14 Text:", value=get_row_default_val(14), key="b_r14")
            editable_r15 = st.text_input("Row 15 Text:", value=get_row_default_val(15), key="b_r15")

        # 📧 COMPILATION PIPELINE ENGINE
        st.markdown("---")
        st.subheader("📧 Consolidated Email 1 (before deploy):")
        
        clean_tag_header = ", ".join(combined_subject_ids)
        first_line_summary = edited_features[0].strip() if edited_features else "System Deliveries"
        final_subject = f"[{clean_tag_header}] (CIE) {first_line_summary}"
        st.code(f"Subject: {final_subject}", language="text")

        row_1_span_count = len(edited_features)
        matrix_rows_list = []
        for loop_idx, f_item in enumerate(edited_features):
            f_text = f_item.strip()
            d_text = edited_descriptions[loop_idx].strip().replace('\n', '<br>') if loop_idx < len(edited_descriptions) else ""
            
            # FIXED: 'font-weight: bold;' removed from the table cells below to keep text normal
            if loop_idx == 0:
                row_html = f'<tr><td rowspan="{row_1_span_count}" style="padding: 8px; text-align: center; font-weight: bold; vertical-align: top; border: 1px solid #000000; color: #000000; background-color: #ffffff;">1</td><td style="padding: 8px; width: 25%; vertical-align: top; border: 1px solid #000000; color: #000000;">{f_text}</td><td style="padding: 8px; width: 70%; vertical-align: top; border: 1px solid #000000; color: #000000;">{d_text}</td></tr>'
            else:
                row_html = f'<tr><td style="padding: 8px; width: 25%; vertical-align: top; border: 1px solid #000000; color: #000000;">{f_text}</td><td style="padding: 8px; width: 70%; vertical-align: top; border: 1px solid #000000; color: #000000;">{d_text}</td></tr>'
            matrix_rows_list.append(row_html)
            
        matrix_rows_html = "".join(matrix_rows_list)

        raw_html_email = f"""<table border="1" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 14px; border-color: #000000; background-color: #ffffff; color: #000000;">
    <thead>
        <tr style="background-color: #f4f5f7; text-align: left; color: #172b4d;">
            <th style="padding: 8px; width: 5%; text-align: center; border: 1px solid #000000; font-weight: bold;">#</th>
            <th style="padding: 8px; width: 25%; border: 1px solid #000000; font-weight: bold;">Feature / Change</th>
            <th style="padding: 8px; width: 70%; border: 1px solid #000000; font-weight: bold;">Description</th>
        </tr>
    </thead>
    <tbody>
        {matrix_rows_html}
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">2</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_row2}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">3</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_row3}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">4</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_row4}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">5</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_row5}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">6</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_row6}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">7</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r7}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">8</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r8}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">9</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r9}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">10</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r10}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">11</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r11}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">12</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r12}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">13</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r13}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">14</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r14}</td></tr>
        <tr><td style="padding: 8px; text-align: center; font-weight: bold; border: 1px solid #000000;">15</td><td colspan="2" style="padding: 8px; border: 1px solid #000000; color: #000000;">{editable_r15}</td></tr>
    </tbody>
</table>"""

        st.markdown(raw_html_email, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.text_area("📋 Copy Raw HTML for Email client:", value=raw_html_email, height=150, key="b_html_raw_output_box")
        
        st.markdown("---")
        st.subheader("📧 Email 2 (after deploy confirmation):")
        st.code(f"Subject: RE: {final_subject}", language="text")
        st.text_area("Confirmation Body:", value="Dear RN team,\n\nInstallation was successfully performed.", height=80, key="b_e2_confirmation_text")
    else:
        st.info("💡 Enter your comma-separated RNP ticket IDs in the box above and click 'Fetch & Aggregate RNP Data Points' to compile your complete data metrics matrix.")




















# --- TAB 5: ID EXTRACTOR ---
with tab5:
    st.markdown("### 🔍 NJ ID Extractor")
    st.markdown("<hr>", unsafe_allow_html=True)
    raw_in = st.text_area("Messy Text:", height=200, key="id_in")
    
    # Target Streamlit's primary action button selector
    st.markdown("""
        <style>
        div.stButton > button[data-testid="stBaseButton-primary"] {
            background-color: #ff4b4b !important;
            color: white !important;
            border: 1px solid #ff4b4b !important;
        }
        div.stButton > button[data-testid="stBaseButton-primary"]:hover {
            background-color: #ff3333 !important;
            color: white !important;
            border: 1px solid #ff3333 !important;
        }
        </style>
        """, unsafe_allow_html=True)

    if st.button("Extract & Fetch", type="primary", key="extractor_submit_btn"):
        if raw_in:
            with st.spinner("Parsing text and extracting valid regulatory tokens..."):
                try:
                    res = requests.post("http://127.0.0.1:5001/extract-nj-ids", json={"raw_text": raw_in})
                    if res.status_code == 200:
                        df = pd.DataFrame(res.json()['extracted_data'])
                        
                        # Clean column headers for professional display
                        df.columns = ["Original ID", "Summary Description", "NJ Change ID"]
                        
                        # 🎯 1. Convert Original IDs into clickable Jira hyper-links
                        def make_jira_link(ticket_id):
                            clean_id = str(ticket_id).strip()
                            return f'<a href="https://jira.gosystem.io/browse/{clean_id}" target="_blank" style="color: #ff4b4b; font-weight: bold; text-decoration: none;">{clean_id}</a>'
                        
                        df["Original ID"] = df["Original ID"].apply(make_jira_link)
                        
                        # Formatter that isolates each ID onto a separate line and styles it red
                        def split_ids_to_new_lines(text):
                            text_str = str(text)
                            
                            # First, wrap all target compliance ID prefixes in red badge styling
                            formatted = re.sub(
                                r'\b((?:RN|ND|EX)-\d{2})\b', 
                                r'<strong style="color: #ff4b4b; background-color: rgba(255, 75, 75, 0.15); padding: 2px 6px; border-radius: 4px; font-size: 15px;">\1</strong>', 
                                text_str
                            )
                            
                            # Add a clean HTML line break before any badges that aren't at the very start of the cell
                            formatted = re.sub(r'(?:\s*,\s*|\s+)(?=<strong style="color: #ff4b4b;)', r'<br><br>', formatted)
                            return formatted
                        
                        df["NJ Change ID"] = df["NJ Change ID"].apply(split_ids_to_new_lines)
                        
                        # Render the dataframe with custom styling via safe HTML table bypass
                        html_table = df.to_html(escape=False, index=False, justify="left")
                        st.markdown(html_table, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Consolidated individual ID tokens extraction loop
                        ids = []
                        for v in res.json()['extracted_data']: 
                            ids.extend(re.findall(r'\b(?:ND|EX|RN)-\d{2}\b', str(v.get("nj_change_id", ""))))
                        
                        unique_sorted_ids = sorted(list(set(ids)))
                        
                        # Display consolidated IDs below using the same vibrant layout format
                        st.markdown("### 🧲 Consolidated IDs Summary")
                        if unique_sorted_ids:
                            formatted_badges = " ".join([
                                f'<strong style="color: #ff4b4b; background-color: rgba(255, 75, 75, 0.15); padding: 4px 8px; border-radius: 4px; margin-right: 6px; display: inline-block; font-size: 16px;">{cid}</strong>'
                                for cid in unique_sorted_ids
                            ])
                            st.markdown(f'<div style="background-color: #1e1e1e; padding: 15px; border-radius: 5px; border: 1px solid #2d2d2d;">{formatted_badges}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div style="color: #757575; font-style: italic;">No change IDs found.</div>', unsafe_allow_html=True)
                            
                except Exception as e:
                    st.error(f"Extraction execution pipeline failure: {str(e)}")















# --- TAB 6: MANIFEST ANALYTICS ---
with tab6:
    st.markdown("### 📸 Multi-Month Manifest Aggregator")
    st.write("Add multiple months, upload screenshots, and isolate precise unapproved regulatory items.")

    # 1. Initialize session state to store multi-month pipelines and tracking data safely
    if "months_pipeline" not in st.session_state:
        st.session_state.months_pipeline = [{"id": 0, "name": "March 2026", "files": []}]

    # Local runtime counters for execution logic loop aggregation
    grand_total, grand_deployed, grand_staged, grand_draft, grand_cancelled = 0, 0, 0, 0, 0
    grand_nd, grand_rn, grand_ern = 0, 0, 0
    grand_component_mentions = {}
    all_months_processed_data = []

    # 2. Render configuration cards for each configured workspace month
    for idx, month_data in enumerate(st.session_state.months_pipeline):
        current_title = month_data.get("name", f"Section #{idx+1}")
        
        with st.expander(f"🗓️ {current_title}", expanded=True):
            col_month, col_year, col_files = st.columns([1.5, 1, 3])
            
            with col_month:
                months_list = ["January", "February", "March", "April", "May", "June", 
                               "July", "August", "September", "October", "November", "December"]
                default_month_idx = 2 if idx == 0 else 0
                selected_m = st.selectbox(f"Select Month:", options=months_list, index=default_month_idx, key=f"select_month_name_{idx}")
                
            with col_year:
                years_list = ["2024", "2025", "2026", "2027", "2028"]
                selected_y = st.selectbox(f"Select Year:", options=years_list, index=2, key=f"select_year_value_{idx}")
            
            month_data["name"] = f"{selected_m} {selected_y}"
            
            with col_files:
                uploaded_files = st.file_uploader(
                    f"Upload table screenshots for {month_data['name']}:",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=True,
                    key=f"month_files_{idx}"
                )
                if uploaded_files:
                    month_data["files"] = uploaded_files




            # --- SCREENSHOT PREVIEW GALLERY (RAW BYTE BYPASS) ---
            if month_data["files"]:
                st.markdown("##### 🖼️ Uploaded Screenshots Preview (Raw Resolution):")
                preview_cols = st.columns(min(len(month_data["files"]), 4))
                for f_idx, file in enumerate(month_data["files"]):
                    with preview_cols[f_idx % 4]:
                        import base64
                        
                        # Read raw uncompressed file bytes directly from memory
                        file_bytes = file.getvalue()
                        encoded = base64.b64encode(file_bytes).decode()
                        
                        # Determine MIME type safely
                        mime_type = file.type if file.type else "image/png"
                        
                        # Force browser to render raw source image inside a scrollable box
                        st.markdown(
                            f'''
                            <div style="border: 1px solid #2d2d2d; border-radius: 4px; padding: 4px; background: #0e1117; text-align: center;">
                                <img src="data:{mime_type};base64,{encoded}" 
                                     style="max-width: 100%; height: auto; image-rendering: pixelated; image-rendering: crisp-edges;" 
                                     alt="Page {f_idx+1}"/>
                                <div style="font-size: 12px; color: #888888; margin-top: 4px;">Page {f_idx+1}</div>
                            </div>
                            ''', 
                            unsafe_allow_html=True
                        )
            





            if len(st.session_state.months_pipeline) > 1:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Remove This Month", key=f"del_month_{idx}", use_container_width=True):
                    st.session_state.months_pipeline.pop(idx)
                    st.rerun()

    if st.button("➕ Add Another Month", use_container_width=True):
        new_id = len(st.session_state.months_pipeline)
        st.session_state.months_pipeline.append({"id": new_id, "name": "", "files": []})
        st.rerun()

    st.markdown("---")

    # 3. Processing Pipeline Loop Execution Frame
    if st.button("⚡ Calculate & Aggregate All Months", type="primary", use_container_width=True):
        with st.spinner("OCR engine is analyzing images across all months..."):
            
            grand_stuck_list = []
            
            for month_data in st.session_state.months_pipeline:
                if not month_data["name"] or not month_data["files"]:
                    continue  
                
                m_total, m_deployed, m_staged, m_draft, m_cancelled = 0, 0, 0, 0, 0
                m_nd, m_rn, m_ern = 0, 0, 0
                m_component_mentions = {}
                
                for file in month_data["files"]:
                    files = {"file": (file.name, file.getvalue(), file.type)}
                    response = requests.post("http://127.0.0.1:5001/calculate-screenshot-metrics", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        m_total += data["total_tickets"]
                        m_deployed += data["deployed"]
                        m_staged += data["staged"]
                        m_draft += data["draft"]
                        m_cancelled += data["cancelled"]
                        m_nd += data["nd_count"]
                        m_rn += data["rn_count"]
                        m_ern += data["ern_count"]
                        
                        # Cache targets matching strict [SENT][RN] validation requirements
                        if data.get("stuck_rn_tickets"):
                            for stuck in data["stuck_rn_tickets"]:
                                stuck["month_origin"] = month_data["name"]
                                grand_stuck_list.append(stuck)

                        if data.get("component_mentions"):
                            for comp, count in data["component_mentions"].items():
                                m_component_mentions[comp] = m_component_mentions.get(comp, 0) + count

                grand_total += m_total
                grand_deployed += m_deployed
                grand_staged += m_staged
                grand_draft += m_draft
                grand_cancelled += m_cancelled
                grand_nd += m_nd
                grand_rn += m_rn
                grand_ern += m_ern
                
                for comp, count in m_component_mentions.items():
                    grand_component_mentions[comp] = grand_component_mentions.get(comp, 0) + count
                
                all_months_processed_data.append({
                    "Month": month_data["name"],
                    "Total Tickets": m_total, 
                    "DEPLOYED": m_deployed, 
                    "STAGED": m_staged, 
                    "DRAFT": m_draft, 
                    "CANCELLED": m_cancelled,
                    "Infrastructure [ND]": m_nd, 
                    "Release Notes [RN]": m_rn, 
                    "Emergency [ERN]": m_ern, 
                    "components": m_component_mentions
                })

            st.session_state.calculated_aggregation = {
                "grand": {"total": grand_total, "deployed": grand_deployed, "staged": grand_staged, "draft": grand_draft, "cancelled": grand_cancelled, "nd": grand_nd, "rn": grand_rn, "ern": grand_ern, "components": grand_component_mentions},
                "monthly_breakdowns": all_months_processed_data,
                "stuck_tickets": grand_stuck_list
            }

    # 4. Display Outputs & Interactive Matrices Data View
    if "calculated_aggregation" in st.session_state:
        agg_data = st.session_state.calculated_aggregation
        
        # HIGH ALERT COMPLIANCE REGULATORY PANEL
        if agg_data.get("stuck_tickets"):
            st.markdown("### 🛑 High Alert: Stuck Regulatory Submissions Detected")
            st.error(f"The following {len(agg_data['stuck_tickets'])} Release Notes (RN) item has been submitted (SENT) but remains unapproved:")
            
            for item in agg_data["stuck_tickets"]:
                st.markdown(f"""
                <div style="background-color: rgba(255, 75, 75, 0.08); border-left: 5px solid #ff4b4b; padding: 14px; margin-bottom: 12px; border-radius: 4px; border: 1px solid rgba(255, 75, 75, 0.2);">
                    <strong style="color: #ffffff;">Manifest Origin:</strong> <span style="color: #e0e0e0;">{item['month_origin']}</span><br>
                    <strong style="color: #ffffff;">Target Reference Tag:</strong> <code style="color: #ff4b4b; background-color: rgba(255,75,75,0.15); padding: 2px 6px; border-radius: 3px; font-size: 14px;">{item['extracted_tag']}</code><br>
                    <span style="font-size: 13px; color: #aaaaaa; display: block; margin-top: 6px;"><strong>Raw Line Extraction Text:</strong> {item['line_text']}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("---")
            
        st.markdown("## 🏆 Grand Consolidated Summary (All Months)")
        g_m1, g_m2, g_m3, g_m4, g_m5 = st.columns(5)
        g_m1.metric("Total Tickets", agg_data["grand"]["total"])
        g_m2.metric("DEPLOYED", agg_data["grand"]["deployed"])
        g_m3.metric("STAGED", agg_data["grand"]["staged"])
        g_m4.metric("DRAFT", agg_data["grand"]["draft"])
        g_m5.metric("CANCELLED", agg_data["grand"]["cancelled"])

        st.markdown("---")
        st.markdown("## 📊 Historical Cross-Month Comparison")
        
        comparison_df = pd.DataFrame(agg_data["monthly_breakdowns"])
        if "components" in comparison_df.columns:
            comparison_df = comparison_df.drop(columns=["components"])
            
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("## 🔍 Detailed Monthly Focus Areas")
        
        for monthly in agg_data["monthly_breakdowns"]:
            with st.expander(f"📍 Component Impact for {monthly['Month']}"):
                if monthly.get("components"):
                    comp_df = pd.DataFrame(list(monthly["components"].items()), columns=["Component", "Mentions Count"]).sort_values(by="Mentions Count", ascending=False)
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No text markers extracted for component scanning.")










import time

# --- TAB 7: EX EVALUATOR ---
with tab7:
    st.markdown("### ✅ EX-Only Ticket Finder")
    st.markdown("<hr>", unsafe_allow_html=True)
    st.write("Scan Jira to gather standard maintenance exemptions (`EX-xx`) devoid of strict regulatory holding delays.")
    
    # Initialize core state variables for tracking tracking data safely across re-runs
    if "scanning_active" not in st.session_state:
        st.session_state.scanning_active = False
    if "ex_results" not in st.session_state:
        st.session_state.ex_results = []

    act_col1, act_col2 = st.columns([1, 4])
    
    with act_col1:
        if st.button("Scan for EX-Only Tickets", type="primary", key="scan_ex_btn", disabled=st.session_state.scanning_active):
            try:
                start_res = requests.post("http://127.0.0.1:5001/start-ex-scan")
                if start_res.status_code == 200:
                    st.session_state.scanning_active = True
                    st.session_state.ex_results = [] # Flush old records for clean run
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to start pipeline: {str(e)}")
    
    with act_col2:
        if st.button("🛑 Stop Scanning Process", type="secondary", key="stop_ex_btn", disabled=not st.session_state.scanning_active):
            try:
                requests.post("http://127.0.0.1:5001/stop-ex-scan")
                st.toast("Cancellation signal sent! Wrapping up...")
            except Exception as stop_err:
                st.error(f"Could not connect to halt request: {str(stop_err)}")

    # ACTIVE LIVE-POLLING OPERATION LOOP
    if st.session_state.scanning_active:
        status_placeholder = st.empty()
        table_placeholder = st.empty()
        
        while st.session_state.scanning_active:
            try:
                check_res = requests.get("http://127.0.0.1:5001/check-ex-scan")
                if check_res.status_code == 200:
                    state_data = check_res.json()
                    current_tickets = state_data.get("tickets", [])
                    engine_status = state_data.get("status")
                    
                    # Cache progress to session state dynamically
                    st.session_state.ex_results = current_tickets
                    
                    status_placeholder.info(f"⏳ Scanning database... Found {len(current_tickets)} tickets so far. Please wait or press Stop.")
                    
                    if current_tickets:
                        df_live = pd.DataFrame(current_tickets)[["ticket_id", "summary", "status", "nj_change_ids"]]
                        df_live.columns = ["Jira ID", "Summary Description", "Current Status", "Extracted Change IDs"]
                        df_live["Jira ID"] = "https://jira.gosystem.io/browse/" + df_live["Jira ID"]
                        
                        table_placeholder.dataframe(
                            df_live, 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={"Jira ID": st.column_config.LinkColumn("Jira ID", display_text=r"browse/([A-Z0-9]+-\d+)$")}
                        )
                    
                    if engine_status in ["complete", "stopped"] or "error" in engine_status:
                        st.session_state.scanning_active = False
                        
                        # Show permanent confirmation banners based on ending state status
                        if engine_status == "stopped":
                            st.sidebar.warning(f"Scan interrupted! Kept {len(current_tickets)} records.")
                        else:
                            st.sidebar.success("Global database scan completed fully!")
                            
                        st.rerun()
                        
                time.sleep(2)
            except Exception as poll_err:
                st.session_state.scanning_active = False
                st.error(f"Polling broken: {str(poll_err)}")
                break

    # 🚀 PERSISTENT DISPLAY FRAME (Always shows results when the scanner engine is idle)
    if not st.session_state.scanning_active and st.session_state.ex_results:
        st.success(f"📊 Showing {len(st.session_state.ex_results)} tickets found up to completion/interruption point:")
        
        df_final = pd.DataFrame(st.session_state.ex_results)[["ticket_id", "summary", "status", "nj_change_ids"]]
        df_final.columns = ["Jira ID", "Summary Description", "Current Status", "Extracted Change IDs"]
        df_final["Jira ID"] = "https://jira.gosystem.io/browse/" + df_final["Jira ID"]
        
        st.dataframe(
            df_final, 
            use_container_width=True, 
            hide_index=True, 
            column_config={
                "Jira ID": st.column_config.LinkColumn(
                    "Jira ID", 
                    display_text=r"browse/([A-Z0-9]+-\d+)$"
                )
            }
        )




