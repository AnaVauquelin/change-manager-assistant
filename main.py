import os
import re
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# --- CONFIGURATION ---
JIRA_SERVER = "https://jira.gosystem.io"
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "YOUR_TOKEN_HERE")

class TicketRequest(BaseModel):
    ticket_id: str

class RawTextRequest(BaseModel):
    raw_text: str

class WikiRequest(BaseModel):
    wiki_url: str

def get_clean_value(issue_obj, field_name, all_field_defs):
    f_id = next((f['id'] for f in all_field_defs if f['name'] == field_name), None)
    if not f_id: return ""
    val = getattr(issue_obj.fields, f_id, None)
    if val is None: return ""
    if isinstance(val, list):
        items = [str(i.value) if hasattr(i, 'value') else str(i.name) if hasattr(i, 'name') else str(i) for i in val]
        return ", ".join(items)
    return str(val.value) if hasattr(val, 'value') else str(val.name) if hasattr(val, 'name') else str(val)







@app.post("/get-notes")
async def get_notes(data: TicketRequest):
    try:
        jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_API_TOKEN)
        ticket_ids = [t.strip() for t in re.split(r'[\s,]+', data.ticket_id) if t.strip()]
        results = []
        all_field_defs = jira.fields()

        # Find the internal Jira ID for the custom field named "Email Body"
        email_body_field_id = next((f['id'] for f in all_field_defs if f['name'] == 'Email Body'), None)

        for tid in ticket_ids:
            try:
                issue = jira.issue(tid)
                
                # Fetch the Email Body content specifically
                raw_email_body = ""
                if email_body_field_id and hasattr(issue.fields, email_body_field_id):
                    val = getattr(issue.fields, email_body_field_id)
                    raw_email_body = str(val) if val is not None else ""
                
                # Fallback to standard release notes if Email Body field isn't populated
                if not raw_email_body:
                    raw_email_body = get_clean_value(issue, "Release Notes", all_field_defs)

                linked_changes = []
                if hasattr(issue.fields, 'issuelinks'):
                    for link in issue.fields.issuelinks:
                        if hasattr(link, 'outwardIssue') and link.type.outward == "contains":
                            child_key = link.outwardIssue.key
                            child_issue = jira.issue(child_key)
                            linked_changes.append({
                                "Ticket": child_key,
                                "Summary": child_issue.fields.summary,
                                "NJ IDs": get_clean_value(child_issue, "NJ Change IDs", all_field_defs)
                            })

                nj_ids = get_clean_value(issue, "NJ Change IDs", all_field_defs)
                clean_id_list = [id.strip() for id in re.split(r'[\s,]+', nj_ids) if id.strip()]
                formatted_subject_ids = f"[{', '.join(clean_id_list)}]" if clean_id_list else "[PENDING ID]"
                
                policy = "✅ STANDARD"
                if "RN-" in nj_ids: policy = "🛑 WAIT: 3-DAY RULE (RN)"
                elif "ND-" in nj_ids: policy = "⚠️ NOTIFY: NOTIFY & EXECUTE (ND)"
                elif "EX-" in nj_ids: policy = "✅ GO: NO WAIT (EX)"

                results.append({
                    "ticket_id": tid,
                    "status": issue.fields.status.name.upper(),
                    "summary": issue.fields.summary,
                    "release_notes": raw_email_body, # Passed directly to frontend aggregator
                    "nj_change_ids": nj_ids,
                    "subject_ids": formatted_subject_ids,
                    "dependencies_nj": get_clean_value(issue, "Dependencies NJ", all_field_defs),
                    "policy": policy,
                    "linked_tickets": linked_changes
                })
            except Exception as e:
                results.append({"ticket_id": tid, "error": str(e)})
        return {"tickets": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))











        

@app.post("/extract-nj-ids")
async def extract_nj_ids(data: RawTextRequest):
    try:
        jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_API_TOKEN)
        all_field_defs = jira.fields()
        found_keys = re.findall(r'([A-Z0-9]+-\d+)', data.raw_text)
        unique_keys = list(dict.fromkeys(found_keys))
        results = []
        for key in unique_keys:
            try:
                issue = jira.issue(key)
                results.append({
                    "original_id": key,
                    "summary": issue.fields.summary,  # 🎯 CHANGED: Removed the [:60] + "..." limitation to show full name
                    "nj_change_id": get_clean_value(issue, "NJ Change IDs", all_field_defs)
                })
            except: continue
        return {"extracted_data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))












@app.get("/get-dashboard-stats")
async def get_dashboard_stats():
    try:
        jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_API_TOKEN)
        stats_to_track = ["RELEASE NOTES PREPARATION", "PREPARE EMAIL DATA", "PENDING REGULATOR APPROVAL", "SENT TO REGULATOR", "APPROVED"]
        dashboard_data = []
        for status in stats_to_track:
            jql = f'project = RNP AND status = "{status}"'
            issues = jira.search_issues(jql, maxResults=0)
            dashboard_data.append({"status": status, "count": issues.total})
        return {"stats": dashboard_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)












@app.post("/parse-wiki-manifest")
async def parse_wiki_manifest(data: WikiRequest):
    try:
        import requests as r_lib
        from bs4 import BeautifulSoup
        
        # Запрос к твоей Confluence-вики. Для авторизации используем твой текущий токен.
        headers = {"Authorization": f"Bearer {JIRA_API_TOKEN}"}
        response = r_lib.get(data.wiki_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Вытаскиваем чистый текст страницы
            return {"text": soup.get_text(separator="\n")}
        else:
            raise HTTPException(status_code=response.status_code, detail="Cannot access Wiki page")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))












from fastapi import UploadFile, File
import io
from PIL import Image







@app.post("/calculate-screenshot-metrics")
async def calculate_screenshot_metrics(file: UploadFile = File(...)):
    try:
        import easyocr
        import numpy as np
        import re
        
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(np.array(image), detail=0)
        
        deployed = 0
        staged = 0
        cancelled = 0
        draft = 0
        
        nd_count = 0
        rn_count = 0
        ern_count = 0
        
        all_text_blocks = [text.strip().upper() for text in results if text.strip()]
        
        # 1. Status tracking metrics counters
        for clean_text in all_text_blocks:
            if clean_text == "DRAFT":
                draft += 1
            elif clean_text in ["SENT", "APPROVED"]:
                staged += 1
            elif clean_text == "DEPLOYED":
                deployed += 1
            elif clean_text == "CANCELLED":
                cancelled += 1
                
            has_nd = bool(re.search(r'\[ND\]|\]ND|ND\]|\bND\b', clean_text))
            has_rn = bool(re.search(r'\[RN\]|\]RN|RN\]|\bRN\b', clean_text))
            has_ern = bool(re.search(r'\[ERN\]|\]ERN|ERN\]|\bERN\b', clean_text))
            
            if has_ern:
                ern_count += 1
            elif has_nd and has_rn:
                if clean_text.find("ND") < clean_text.find("RN"): nd_count += 1
                else: rn_count += 1
            elif has_nd:
                nd_count += 1
            elif has_rn:
                rn_count += 1

        # 2. Extract explicit targets and cross-reference safely
        sent_rn_candidates = []
        resolved_tokens_global = set()
        
        for clean_text in all_text_blocks:
            found_tokens = re.findall(r'(IG-RN-\d+)', clean_text)
            
            # If the block explicitly marks complete execution milestones, cache its tokens to the whitelist
            if "APPROVED" in clean_text or "DEPLOYED" in clean_text:
                for token in found_tokens:
                    resolved_tokens_global.add(token)
            
            else:
                # STRATEGIC FIX: Verify that "RN" is matched as a standalone tag or bracket element, NOT substring fragments
                has_explicit_rn = bool(re.search(r'\[RN\]|\]RN|RN\]|\bRN\b', clean_text))
                has_explicit_sent = "SENT" in clean_text
                
                if has_explicit_sent and has_explicit_rn and "DRAFT" not in clean_text:
                    if found_tokens:
                        sent_rn_candidates.append({
                            "text": clean_text,
                            "tokens": found_tokens
                        })

        # 3. Filter real stuck occurrences out of verified candidate scopes
        stuck_rn_tickets = []
        for candidate in sent_rn_candidates:
            stuck_tokens_in_row = [t for t in candidate["tokens"] if t not in resolved_tokens_global]
            
            if stuck_tokens_in_row:
                ticket_label = ", ".join(stuck_tokens_in_row)
                stuck_rn_tickets.append({
                    "line_text": candidate["text"],
                    "extracted_tag": ticket_label
                })

        total_tickets = deployed + staged + cancelled + draft
        classified_total = nd_count + rn_count + ern_count
        if classified_total != total_tickets and total_tickets > 0:
            diff = total_tickets - classified_total
            if diff > 0:
                if nd_count >= rn_count: nd_count += diff
                else: rn_count += diff
            else:
                reduction = abs(diff)
                for _ in range(reduction):
                    if rn_count > nd_count and rn_count > 0: rn_count -= 1
                    elif nd_count > 0: nd_count -= 1

        full_ocr_text = " ".join(all_text_blocks).lower()
        keywords_map = {
            "Database, Schema & Indexing": ["db", "database", "schema", "indexing", "table", "migrations", "upgrades"],
            "Security, MFA & Compliance": ["security", "mfa", "otp", "auth", "verification", "geocomply", "policy", "terms", "responsible"],
            "Payments & Finance": ["payment", "deposit", "withdrawal", "currency", "invoicing", "transaction", "checkout", "routing"],
            "UI / UX & Mobile Ecosystem": ["ui", "ux", "safari", "display", "localization", "translation", "widget"]
        }
        
        component_mentions = {}
        for component, words in keywords_map.items():
            count = sum(full_ocr_text.count(word) for word in words)
            component_mentions[component] = count

        return {
            "total_tickets": total_tickets,
            "deployed": deployed,
            "staged": staged,
            "cancelled": cancelled,
            "draft": draft,
            "nd_count": nd_count,
            "rn_count": rn_count,
            "ern_count": ern_count,
            "component_mentions": component_mentions,
            "stuck_rn_tickets": stuck_rn_tickets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
















import threading

# Global memory to hold the background scan task state
scan_state = {
    "is_running": False,
    "tickets": [],
    "status": "idle"
}

def run_ex_scan_worker(nj_field_id, jql):
    global scan_state
    try:
        jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_API_TOKEN)
        start_at = 0
        max_results_per_batch = 100
        
        while True:
            if os.path.exists("stop_scan.flag"):
                print("⚠️ STOP SIGNAL DETECTED! Cleaning up background thread...")
                scan_state["status"] = "stopped"
                break

            issues = jira.search_issues(jql, startAt=start_at, maxResults=max_results_per_batch)
            if not issues:
                scan_state["status"] = "complete"
                break
                
            for issue in issues:
                raw_val = getattr(issue.fields, nj_field_id, None)
                if not raw_val:
                    continue
                    
                label_strings = []
                if isinstance(raw_val, list):
                    for item in raw_val:
                        if hasattr(item, 'value'): label_strings.append(str(item.value).upper())
                        elif hasattr(item, 'name'): label_strings.append(str(item.name).upper())
                        else: label_strings.append(str(item).upper())
                else:
                    if hasattr(raw_val, 'value'): label_strings.append(str(raw_val.value).upper())
                    elif hasattr(raw_val, 'name'): label_strings.append(str(raw_val.name).upper())
                    else: label_strings.append(str(raw_val).upper())
                
                if not label_strings:
                    continue
                    
                if any("EX" in s for s in label_strings):
                    clean_display_text = ", ".join([lbl.split(" - ")[0] for lbl in label_strings if "EX" in lbl])
                    
                    # Append instantly so partial progress can be streamed live
                    scan_state["tickets"].append({
                        "ticket_id": issue.key,
                        "summary": issue.fields.summary,
                        "status": issue.fields.status.name.upper(),
                        "nj_change_ids": clean_display_text
                    })
            
            start_at += len(issues)
            if len(issues) < max_results_per_batch:
                scan_state["status"] = "complete"
                break
                
    except Exception as e:
        print(f"❌ Thread Exception: {str(e)}")
        scan_state["status"] = f"error: {str(e)}"
    finally:
        scan_state["is_running"] = False
        if os.path.exists("stop_scan.flag"):
            os.remove("stop_scan.flag")

@app.post("/start-ex-scan")
async def start_ex_scan():
    global scan_state
    if scan_state["is_running"]:
        return {"status": "already_running"}
        
    try:
        if os.path.exists("stop_scan.flag"):
            os.remove("stop_scan.flag")
            
        jira = JIRA(server=JIRA_SERVER, token_auth=JIRA_API_TOKEN)
        all_field_defs = jira.fields()
        nj_field_id = next((f['id'] for f in all_field_defs if f['name'] == "NJ Change IDs"), None)
        
        if not nj_field_id:
            raise HTTPException(status_code=500, detail="Custom field not found.")
            
        jql = '"NJ Change IDs" is not EMPTY'
        
        # Reset tracker states
        scan_state["is_running"] = True
        scan_state["tickets"] = []
        scan_state["status"] = "running"
        
        # Spin up task processing out-of-band so the HTTP response returns instantly
        threading.Thread(target=run_ex_scan_worker, args=(nj_field_id, jql), daemon=True).start()
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/check-ex-scan")
async def check_ex_scan():
    global scan_state
    return scan_state

@app.post("/stop-ex-scan")
async def stop_ex_scan():
    with open("stop_scan.flag", "w") as f:
        f.write("stop")
    return {"status": "Stop signal registered"}



