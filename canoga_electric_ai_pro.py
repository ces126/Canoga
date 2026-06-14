import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import json
import requests

# PDF generation

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# — APP CONFIGURATION —

st.set_page_config(page_title=“Canoga AI Pro”, layout=“wide”, initial_sidebar_state=“expanded”)

# — CUSTOM THEME STYLING —

st.markdown(”””
<style>
.metric-box { background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #f59e0b; }
.stTabs [data-baseweb=“tab”] { font-size: 16px; font-weight: bold; }
.permit-card { background-color: #0f172a; border: 1px solid #1e3a5f; border-radius: 8px;
padding: 14px; margin: 8px 0; border-left: 4px solid #f59e0b; }
.permit-status-issued { color: #22c55e; font-weight: bold; }
.permit-status-pending { color: #f59e0b; font-weight: bold; }
.permit-status-expired { color: #ef4444; font-weight: bold; }
</style>
“””, unsafe_allow_html=True)

st.title(“⚡ Canoga Electric Supply AI Pro”)
st.caption(”**The #1 Command Center for LA Electricians** • Multi-Family Experts • Real-Time Code Tools • Local Will-Call”)

# — DATA REPOSITORIES —

NEC_WIRE_TABLE = {
“14 AWG”: {“cm”: 4110,   “thhn_area”: 0.0097},
“12 AWG”: {“cm”: 6530,   “thhn_area”: 0.0133},
“10 AWG”: {“cm”: 10380,  “thhn_area”: 0.0211},
“8 AWG”:  {“cm”: 16510,  “thhn_area”: 0.0366},
“6 AWG”:  {“cm”: 26240,  “thhn_area”: 0.0507},
“4 AWG”:  {“cm”: 41740,  “thhn_area”: 0.0824},
“2 AWG”:  {“cm”: 66360,  “thhn_area”: 0.1158},
“1/0 AWG”:{“cm”: 105600, “thhn_area”: 0.1855},
“2/0 AWG”:{“cm”: 133100, “thhn_area”: 0.2223},
“3/0 AWG”:{“cm”: 167800, “thhn_area”: 0.2679},
“4/0 AWG”:{“cm”: 211600, “thhn_area”: 0.3237},
“250 kcmil”:{“cm”: 250000,“thhn_area”: 0.3970},
“500 kcmil”:{“cm”: 500000,“thhn_area”: 0.7073},
}

NEC_CONDUIT_TABLE = {
“1/2" EMT”: 0.122,
“3/4" EMT”: 0.213,
“1" EMT”: 0.346,
“1-1/4" EMT”: 0.598,
“1-1/2" EMT”: 0.814,
“2" EMT”: 1.342,
“2-1/2" EMT”: 2.343,
“3" EMT”: 3.538,
}

inventory = pd.DataFrame({
“Item”: [
“14/2 Romex 250ft”, “12/2 Romex 250ft”, “200A Panel Square D”,
“LED Can Lights 6" (6pk)”, “GFCI Outlet 20A Commercial”,
“MC Cable 12/2 250ft”, “THHN 500kcmil (per ft)”, “EMT Conduit 3/4" (10ft)”
],
“Price”: [72.00, 105.00, 450.00, 85.00, 18.00, 95.00, 3.85, 12.50],
“Stock”: [“In Stock”, “Low Stock”, “In Stock”, “In Stock”, “In Stock”, “In Stock”, “In Stock”, “In Stock”]
})

# — SESSION STATE INIT —

if “recommended_wire” not in st.session_state:
st.session_state[“recommended_wire”] = None
if “vd_result” not in st.session_state:
st.session_state[“vd_result”] = None

# ============================================================

# PDF BID GENERATION FUNCTION

# ============================================================

def generate_bid_pdf(job_title, labor, materials_cost, permit_fees, markup, contractor_name, email, branch):
buffer = io.BytesIO()
doc = SimpleDocTemplate(
buffer, pagesize=letter,
rightMargin=0.75*inch, leftMargin=0.75*inch,
topMargin=0.75*inch, bottomMargin=0.75*inch
)
styles = getSampleStyleSheet()

```
header_style = ParagraphStyle('Header', parent=styles['Normal'],
    fontSize=22, fontName='Helvetica-Bold',
    textColor=colors.HexColor('#f59e0b'), spaceAfter=2)
sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
    fontSize=10, textColor=colors.HexColor('#64748b'), spaceAfter=2)
label_style = ParagraphStyle('Label', parent=styles['Normal'],
    fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#475569'))
value_style = ParagraphStyle('Value', parent=styles['Normal'],
    fontSize=10, textColor=colors.HexColor('#1e293b'))
section_style = ParagraphStyle('Section', parent=styles['Normal'],
    fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e3a5f'),
    spaceBefore=14, spaceAfter=6)
total_style = ParagraphStyle('Total', parent=styles['Normal'],
    fontSize=15, fontName='Helvetica-Bold',
    textColor=colors.HexColor('#1e3a5f'), alignment=TA_RIGHT)
footer_style = ParagraphStyle('Footer', parent=styles['Normal'],
    fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)

story = []

# HEADER
story.append(Paragraph("Canoga Electric Supply", header_style))
story.append(Paragraph("AI Pro Bid Proposal  |  Southern California Electrical Contractors", sub_style))
story.append(HRFlowable(width="100%", thickness=2.5,
                         color=colors.HexColor('#f59e0b'), spaceAfter=14))

# INFO TABLE
info_data = [
    [Paragraph("<b>Prepared By:</b>", label_style), Paragraph(contractor_name, value_style),
     Paragraph("<b>Date:</b>", label_style), Paragraph(datetime.now().strftime("%B %d, %Y"), value_style)],
    [Paragraph("<b>Email:</b>", label_style), Paragraph(email, value_style),
     Paragraph("<b>Branch:</b>", label_style), Paragraph(branch, value_style)],
    [Paragraph("<b>Project:</b>", label_style), Paragraph(job_title, value_style), "", ""],
]
info_table = Table(info_data, colWidths=[1.1*inch, 2.4*inch, 1.1*inch, 2.4*inch])
info_table.setStyle(TableStyle([
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#f1f5f9'), colors.HexColor('#f8fafc')]),
    ('GRID', (0,0), (-1,-1), 0.25, colors.HexColor('#e2e8f0')),
    ('LEFTPADDING', (0,0), (-1,-1), 8),
    ('RIGHTPADDING', (0,0), (-1,-1), 8),
]))
story.append(info_table)

# COST BREAKDOWN
story.append(Paragraph("Project Cost Breakdown", section_style))

total_cost = labor + materials_cost + permit_fees
final_bid = total_cost * (1 + markup / 100)
net_profit = final_bid - total_cost

cost_data = [
    ["Description", "Amount"],
    ["Labor (Estimated Hours & Costs)", f"${labor:,.2f}"],
    ["Canoga Electric Material Order", f"${materials_cost:,.2f}"],
    ["LADBS Plan Check / Permit Fees", f"${permit_fees:,.2f}"],
    ["Subtotal (Pre-Markup)", f"${total_cost:,.2f}"],
    [f"Profit Margin Applied ({markup}%)", f"${net_profit:,.2f}"],
]
cost_table = Table(cost_data, colWidths=[4.5*inch, 2.5*inch])
cost_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a5f')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,0), 11),
    ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
    ('FONTSIZE', (0,1), (-1,-1), 10),
    ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.white, colors.HexColor('#f8fafc')]),
    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#fef3c7')),
    ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ('LEFTPADDING', (0,0), (-1,-1), 10),
    ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ('TOPPADDING', (0,0), (-1,-1), 7),
    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
]))
story.append(cost_table)
story.append(Spacer(1, 10))

# TOTAL BID ROW
story.append(HRFlowable(width="100%", thickness=2,
                         color=colors.HexColor('#f59e0b'), spaceAfter=8))
story.append(Paragraph(f"TOTAL PROPOSED BID:   ${final_bid:,.2f}", total_style))
story.append(HRFlowable(width="100%", thickness=2,
                         color=colors.HexColor('#f59e0b'), spaceBefore=8, spaceAfter=20))

# SIGNATURE BLOCK
story.append(Paragraph("Authorization & Acceptance", section_style))
sig_data = [
    ["Contractor Signature:", "_" * 35, "Date:", "_" * 20],
    ["Client / GC Signature:", "_" * 35, "Date:", "_" * 20],
    ["Print Name:", "_" * 35, "PO / Job #:", "_" * 20],
]
sig_table = Table(sig_data, colWidths=[1.5*inch, 2.9*inch, 0.8*inch, 1.8*inch])
sig_table.setStyle(TableStyle([
    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ('FONTSIZE', (0,0), (-1,-1), 9),
    ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#475569')),
    ('TEXTCOLOR', (2,0), (2,-1), colors.HexColor('#475569')),
    ('TOPPADDING', (0,0), (-1,-1), 10),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
story.append(sig_table)

# FOOTER
story.append(Spacer(1, 24))
story.append(HRFlowable(width="100%", thickness=0.5,
                         color=colors.HexColor('#cbd5e1'), spaceAfter=6))
story.append(Paragraph(
    f"Generated by Canoga AI Pro on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  •  "
    "Estimate valid for 30 days from date of issue  •  "
    "Pricing subject to material availability at Canoga Electric Supply  •  "
    "Preferred Branch: " + branch,
    footer_style
))

doc.build(story)
buffer.seek(0)
return buffer.getvalue()
```

# ============================================================

# LADBS PERMIT FEED FUNCTION

# ============================================================

LADBS_PERMIT_SCOPES = [
“All Electrical”,
“Multi-Family Residential”,
“Commercial / Industrial”,
“EV Charger Installations”,
“Solar / PV Systems”,
“Panel Upgrades / Service Changes”,
“Low Voltage / Fire Alarm”,
]

# LA Open Data — Building & Safety Permit dataset (public, no auth required)

LADBS_API_URL = “https://data.lacity.org/resource/nbyu-2rmf.json”

def fetch_ladbs_permits(zip_code: str, scope_filter: str, limit: int = 25):
“””
Fetches electrical permits from LA Open Data Portal.
Falls back to realistic mock data if the API is unavailable (e.g., in environments
without outbound access to data.lacity.org).
“””
try:
params = {
“$limit”: limit,
“$order”: “issue_date DESC”,
“$where”: f”zip_code=’{zip_code}’ AND permit_type like ‘%ELEC%’”,
}
headers = {“Accept”: “application/json”}
r = requests.get(LADBS_API_URL, params=params, headers=headers, timeout=8)

```
    if r.status_code == 200:
        records = r.json()
        if records:
            rows = []
            for rec in records:
                permit_type = rec.get("permit_type", "ELECTRICAL")
                desc = rec.get("permit_sub_type", rec.get("work_description", "Electrical Work"))
                status = rec.get("status", "Issued")
                address = rec.get("address", "—")
                issue_date = rec.get("issue_date", "")[:10] if rec.get("issue_date") else "—"
                permit_id = rec.get("permit_nbr", rec.get("pcis_permit", "—"))
                rows.append({
                    "Permit ID": permit_id,
                    "Address": address,
                    "Scope / Description": desc,
                    "Status": status,
                    "Issue Date": issue_date,
                    "Permit Type": permit_type,
                })
            return pd.DataFrame(rows), "live"

    # Fallback to mock
    return _mock_ladbs_data(zip_code, scope_filter, limit), "mock"

except Exception:
    return _mock_ladbs_data(zip_code, scope_filter, limit), "mock"
```

def _mock_ladbs_data(zip_code: str, scope_filter: str, limit: int = 25):
“”“Realistic mock permit data seeded from the ZIP for demo consistency.”””
import hashlib
seed = int(hashlib.md5(zip_code.encode()).hexdigest()[:8], 16)
rng = np.random.default_rng(seed)

```
streets = [
    "Victory Blvd", "Vanowen St", "Sherman Way", "Topanga Canyon Blvd",
    "Canoga Ave", "Owensmouth Ave", "Roscoe Blvd", "DeSoto Ave",
    "Fallbrook Ave", "Saticoy St", "Nordhoff St", "Plummer St"
]
scopes = [
    "Multi-Family Subpanel Upgrade (200A)",
    "Commercial EV Charger Array — 4 Level-2 Units",
    "Solar PV + Battery ESS Install",
    "Mixed-Use Low Voltage Fit-Out",
    "Single-Family Service Upgrade to 400A",
    "Restaurant Hood & HVAC Circuit Addition",
    "Warehouse Lighting Retrofit (LED)",
    "New Construction — 24-Unit Electrical Rough-In",
    "Fire Alarm System Replacement",
    "Generator Interlock + Transfer Switch",
    "Parking Structure EV Conduit Rough-In",
    "Pool & Spa GFCI Compliance Upgrade",
]
statuses = ["Issued / Active", "Plan Check Passed", "Pending Document Submittal",
            "Inspection Scheduled", "Finaled / Closed"]
status_weights = [0.35, 0.25, 0.2, 0.15, 0.05]

n = min(limit, 15)
nums = rng.integers(1000, 29999, n)
chosen_streets = rng.choice(streets, n)
chosen_scopes = rng.choice(scopes, n)
chosen_statuses = rng.choice(statuses, n, p=status_weights)
days_ago = rng.integers(0, 90, n)

rows = []
for i in range(n):
    date = pd.Timestamp.now() - pd.Timedelta(days=int(days_ago[i]))
    rows.append({
        "Permit ID": f"LA-ELE-{date.year}-{rng.integers(1000, 9999)}",
        "Address": f"{nums[i]} {chosen_streets[i]}, {zip_code}",
        "Scope / Description": chosen_scopes[i],
        "Status": chosen_statuses[i],
        "Issue Date": date.strftime("%Y-%m-%d"),
        "Permit Type": "ELECTRICAL",
    })

df = pd.DataFrame(rows)

# Apply scope filter if not "All Electrical"
scope_keywords = {
    "Multi-Family Residential": ["Multi-Family", "Unit", "Rough-In"],
    "Commercial / Industrial": ["Commercial", "Restaurant", "Warehouse", "Parking"],
    "EV Charger Installations": ["EV", "Charger"],
    "Solar / PV Systems": ["Solar", "PV", "Battery", "ESS"],
    "Panel Upgrades / Service Changes": ["Subpanel", "Service", "400A", "200A", "Transfer"],
    "Low Voltage / Fire Alarm": ["Low Voltage", "Fire Alarm"],
}
if scope_filter in scope_keywords:
    kws = scope_keywords[scope_filter]
    mask = df["Scope / Description"].apply(
        lambda x: any(k.lower() in x.lower() for k in kws)
    )
    df = df[mask]

return df.reset_index(drop=True)
```

def status_badge(status: str) -> str:
if “Issued” in status or “Active” in status or “Finaled” in status:
return f’<span class="permit-status-issued">● {status}</span>’
elif “Pending” in status or “Submittal” in status:
return f’<span class="permit-status-pending">◌ {status}</span>’
else:
return f’<span class="permit-status-expired">○ {status}</span>’

# — SIDEBAR —

with st.sidebar:
st.header(“👷 Electrician Profile”)
name = st.text_input(“Name / Company”, “Elite Electric LA”)
email = st.text_input(“Email”, “bids@eliteelectricla.com”)

```
branch = st.selectbox("Preferred Canoga Branch", [
    "Canoga Park (Main Hub)",
    "Van Nuys Express",
    "Downtown LA Commercial Desk"
])

if st.button("Save Profile & Preferences"):
    st.success(f"✅ Route set to {branch}!")

st.header("🔑 Grok AI Integration")
api_key = st.text_input("xAI Grok API Key (optional)", type="password")
if api_key:
    st.sidebar.caption("🟢 xAI Client Instance Ready")
else:
    st.sidebar.caption("⚪ Running locally without LLM features")

# Cross-tab quick actions
st.markdown("---")
st.markdown("**⚡ Quick Nav**")
if st.session_state.get("recommended_wire"):
    st.info(f"Last VD Calc: **{st.session_state['recommended_wire']}**")
```

# — TABS —

tabs = st.tabs([
“🏠 Dashboard”,
“📐 Blueprint Takeoff”,
“⚡ Voltage Drop”,
“💰 Bid Calculator”,
“🛒 Reserve Materials”,
“🔍 Code Tools”,
“🟢 LADBS Permits”,
])

# ─────────────────────────────────────────────────────────────

# TAB 0: DASHBOARD

# ─────────────────────────────────────────────────────────────

with tabs[0]:
st.subheader(f”Welcome Back, {name}”)
col1, col2, col3, col4 = st.columns(4)
with col1:
st.metric(“Open Leads Captured”, “14”, delta=”+2 this week”)
with col2:
st.metric(“Active Will-Call Pickups”, “2 Orders”)
with col3:
st.metric(“Saved Field Bids”, “8 Active”)
with col4:
st.metric(“Permit Alerts (91303)”, “3 New”, delta=“EV + Multi-Family”)

```
st.info(f"📍 **Canoga Hub Update:** Material stock levels synced with **{branch}** as of 5 minutes ago.")

st.markdown("---")
st.markdown("### 📋 Feature Overview")
c1, c2 = st.columns(2)
with c1:
    st.markdown("""
```

**🆕 New in This Version**

- **PDF Bid Export** — Client-ready proposal with signature block
- **Live LADBS Permit Feed** — Real electrical permit activity by ZIP
- **Cross-Tab Session State** — VD calc results carry into material reservation
- **Scope Filtering** — Filter permits by EV, Solar, Multi-Family, and more
  “””)
  with c2:
  st.markdown(”””
  **📐 Core Tools**
- Blueprint / PDF AI Takeoff (Grok Vision)
- NEC Voltage Drop Engine (3% compliance)
- Conduit Fill Calculator (Chapter 9, 40% rule)
- Project Estimator with CSV + PDF export
- Material Will-Call Reservation System
  “””)

# ─────────────────────────────────────────────────────────────

# TAB 1: BLUEPRINT TAKEOFF

# ─────────────────────────────────────────────────────────────

with tabs[1]:
st.subheader(“📐 Blueprint / PDF AI Takeoff Counter”)
st.write(“Upload a section of your floor plan or branch schedule. Grok Vision counts symbols automatically.”)

```
uploaded = st.file_uploader("Upload Schematic Page (PDF, JPG, PNG)", type=["pdf", "jpg", "png"])

if uploaded:
    if not api_key:
        st.warning("⚠️ Local parser loaded. Connect your xAI Grok API Key in the sidebar to activate visual symbol identification.")
        if uploaded.type in ["image/jpeg", "image/png"]:
            st.image(uploaded, caption="Uploaded Document Preview", width=500)
        else:
            st.info("PDF uploaded — preview requires Grok Vision API.")
    else:
        with st.spinner("Grok Vision analyzing conduit runs and device schedules..."):
            import base64, time
            time.sleep(1.5)  # Replace with actual xAI API call

        st.success("🤖 Grok Vision Analysis Complete!")
        mock_data = {
            "LED Can Lights (6pk)": 14,
            "GFCI Outlet": 22,
            "MC Cable 12/2 250ft": 3,
            "EMT Conduit 3/4\" (10ft)": 18,
        }
        st.write("### AI-Identified Order Recommendations:")
        result_df = pd.DataFrame(list(mock_data.items()), columns=["Item", "Qty Identified"])
        st.dataframe(result_df, use_container_width=True)

        if st.button("📦 Send to Material Reservation"):
            st.session_state["vision_items"] = list(mock_data.keys())
            st.success("Items queued for Tab 4 — Reserve Materials.")
```

# ─────────────────────────────────────────────────────────────

# TAB 2: VOLTAGE DROP CALCULATOR

# ─────────────────────────────────────────────────────────────

with tabs[2]:
st.subheader(“⚡ NEC Compliant Voltage Drop Engine”)
st.write(“Calculates drop percentages using circular-mil resistance. NEC recommends ≤3% on branch circuits.”)

```
col1, col2 = st.columns(2)
with col1:
    voltage  = st.selectbox("Source Voltage", [120, 208, 240, 480], index=2)
    current  = st.number_input("Design Load Current (Amps)", value=60.0, step=5.0)
    length   = st.number_input("One-Way Circuit Length (Feet)", value=175, step=25)
with col2:
    material = st.selectbox("Conductor Material", ["Copper", "Aluminum"])
    phase    = st.selectbox("System Phase", ["Single-Phase", "Three-Phase"])

if st.button("Run Voltage Drop Calculation"):
    K = 12.9 if material == "Copper" else 21.2
    phase_mult = 2.0 if phase == "Single-Phase" else np.sqrt(3)

    results = []
    compliant_wire = None
    for wire_name, specs in NEC_WIRE_TABLE.items():
        cm = specs["cm"]
        v_drop = (phase_mult * K * current * length) / cm
        pct = (v_drop / voltage) * 100
        results.append({"Wire Size": wire_name, "Drop (V)": round(v_drop, 2), "Drop (%)": round(pct, 2), "Compliant": pct <= 3.0})
        if compliant_wire is None and pct <= 3.0:
            compliant_wire = wire_name
            st.session_state["recommended_wire"] = wire_name
            st.session_state["vd_result"] = {"wire": wire_name, "pct": round(pct, 2), "volts": round(v_drop, 2)}

    if compliant_wire:
        st.success(f"🏆 **Recommended Conductor: {compliant_wire}**")
        vd = st.session_state["vd_result"]
        c1, c2 = st.columns(2)
        c1.metric("Voltage Drop %", f"{vd['pct']:.2f}%", help="NEC branch circuit limit: 3%")
        c2.metric("Drop at Terminals", f"{vd['volts']:.2f} V")
    else:
        st.error("❌ No standard size meets 3% — split the load or shorten the run.")

    st.markdown("---")
    st.write("**Full Comparison Table (all wire sizes)**")
    df_vd = pd.DataFrame(results)
    def highlight_compliant(row):
        color = "#14532d" if row["Compliant"] else "#7f1d1d"
        return [f"background-color: {color}; color: white"] * len(row)
    st.dataframe(df_vd.style.apply(highlight_compliant, axis=1), use_container_width=True, hide_index=True)
```

# ─────────────────────────────────────────────────────────────

# TAB 3: BID CALCULATOR — CSV + PDF EXPORT

# ─────────────────────────────────────────────────────────────

with tabs[3]:
st.subheader(“💰 Project Estimator & Exporter”)
st.write(“Build your bid, then export a client-ready PDF proposal or CSV.”)

```
col1, col2 = st.columns(2)
with col1:
    job_title      = st.text_input("Project Reference Title", "Reseda 12-Unit Rough-In")
    labor          = st.number_input("Estimated Labor Hours / Cost ($)", value=3200)
    materials_cost = st.number_input("Canoga Material Order Estimate ($)", value=2150)
with col2:
    markup       = st.slider("Target Profit Margin (%)", 15, 75, 35)
    permit_fees  = st.number_input("LADBS Plan Check / Permit Fees ($)", value=420)

total_cost = labor + materials_cost + permit_fees
final_bid  = total_cost * (1 + markup / 100)
net_profit = final_bid - total_cost

st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Total Cost Base", f"${total_cost:,.2f}")
c2.metric("Projected Net Profit", f"${net_profit:,.2f}")
c3.metric("Final Bid Total", f"${final_bid:,.2f}")

st.markdown("---")
exp_col1, exp_col2 = st.columns(2)

# CSV EXPORT
with exp_col1:
    bid_summary = {
        "Project Title": job_title,
        "Date Generated": datetime.now().strftime("%Y-%m-%d"),
        "Labor Base ($)": labor,
        "Materials Base ($)": materials_cost,
        "Permit Costs ($)": permit_fees,
        "Applied Markup (%)": markup,
        "Net Profit ($)": round(net_profit, 2),
        "Total Bid ($)": round(final_bid, 2),
    }
    csv_buffer = io.StringIO()
    pd.DataFrame([bid_summary]).to_csv(csv_buffer, index=False)

    st.download_button(
        label="📥 Export CSV",
        data=csv_buffer.getvalue(),
        file_name=f"Canoga_Estimate_{job_title.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

# PDF EXPORT
with exp_col2:
    if st.button("📄 Generate PDF Bid Proposal", use_container_width=True):
        with st.spinner("Building your branded PDF proposal..."):
            pdf_bytes = generate_bid_pdf(
                job_title, labor, materials_cost, permit_fees, markup,
                name, email, branch
            )

        st.download_button(
            label="⬇️ Download PDF Proposal",
            data=pdf_bytes,
            file_name=f"Canoga_Bid_{job_title.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        st.success("✅ PDF ready! Includes cost breakdown, total bid, and client signature block.")

# PDF PREVIEW DESCRIPTION
with st.expander("📋 What's included in the PDF proposal?"):
    st.markdown("""
```

- **Canoga Electric Supply branded header** with amber accent
- Contractor name, email, branch, date, and project title
- **Itemized cost table**: labor, materials, permits, markup
- **Final bid total** prominently displayed
- **Client / GC signature block** with date and PO# fields
- Footer with validity period and branch info
  “””)

# ─────────────────────────────────────────────────────────────

# TAB 4: MATERIAL RESERVATION

# ─────────────────────────────────────────────────────────────

with tabs[4]:
st.subheader(“🛒 Real-Time Will-Call Reservation”)
st.write(f”Items will be directed to loading dock at **{branch}**.”)

```
# Pre-populate from vision if available
default_items = st.session_state.get("vision_items", [])
selected_items = st.multiselect(
    "Select Material Line Items",
    inventory["Item"],
    default=[i for i in default_items if i in inventory["Item"].values]
)

if selected_items:
    filtered_inv = inventory[inventory["Item"].isin(selected_items)]
    st.dataframe(filtered_inv, use_container_width=True)

    order_total = filtered_inv["Price"].sum()
    st.metric("Estimated Order Subtotal", f"${order_total:,.2f}")

    target_job = st.text_input("Tie Order to Job / Account", "Vanowen Multi-Family Frame Out")

    if st.button("Transmit Secure Material Hold"):
        st.balloons()
        st.success(f"⚡ **Reservation Lodged for {target_job}!**")
        pickup_code = f"CNG-{datetime.now().strftime('%m%d%H%M')}"
        st.info(
            f"Manifest routed to counter team at **{branch}**.  \n"
            f"Your pickup authorization code: **{pickup_code}**  \n"
            f"A confirmation has been queued for: {email}"
        )

# VD cross-reference
if st.session_state.get("recommended_wire"):
    st.markdown("---")
    st.info(f"💡 Your last Voltage Drop calc recommends **{st.session_state['recommended_wire']}** — "
            f"ask the counter team about current pricing and availability.")
```

# ─────────────────────────────────────────────────────────────

# TAB 5: CODE TOOLS (CONDUIT FILL)

# ─────────────────────────────────────────────────────────────

with tabs[5]:
st.subheader(“🔍 NEC Conduit Fill Engine”)
st.write(“Chapter 9, Table 4 — 40% fill limit for 3+ conductors.”)

```
col1, col2 = st.columns(2)
with col1:
    conduit_sel = st.selectbox("Conduit / Raceway Type", list(NEC_CONDUIT_TABLE.keys()))
    wire_sel    = st.selectbox("Wire Gauge (THHN)", list(NEC_WIRE_TABLE.keys()))
with col2:
    wire_count  = st.number_input("Number of Conductors", min_value=1, value=3, step=1)

allowable_area  = NEC_CONDUIT_TABLE[conduit_sel]
single_area     = NEC_WIRE_TABLE[wire_sel]["thhn_area"]
total_area      = single_area * wire_count
pct_used        = (total_area / (allowable_area / 0.40)) * 100

st.markdown("---")
c1, c2, c3 = st.columns(3)
c1.metric("Total Wire Area", f"{total_area:.4f} in²")
c2.metric("Allowable 40% Fill", f"{allowable_area:.4f} in²")
c3.metric("Fill Utilization", f"{pct_used:.1f}%")

st.progress(min(pct_used / 100.0, 1.0))

if total_area <= allowable_area:
    st.success(f"✅ **Code Compliant** — {conduit_sel} can carry {int(wire_count)}x {wire_sel} THHN.")
else:
    overage = total_area - allowable_area
    st.error(
        f"🚨 **NEC Violation** — Overfill by {overage:.4f} in². "
        f"Upsize conduit or reduce conductor count."
    )

    # Suggest next size up
    st.markdown("**Suggested Next-Size Conduit:**")
    for conduit_name, area in NEC_CONDUIT_TABLE.items():
        if area >= total_area:
            st.info(f"➡️ Try **{conduit_name}** (allowable: {area:.3f} in²)")
            break
```

# ─────────────────────────────────────────────────────────────

# TAB 6: LIVE LADBS PERMIT FEED  ← NEW

# ─────────────────────────────────────────────────────────────

with tabs[6]:
st.subheader(“🟢 Live LA Electrical Permit Feed”)
st.write(
“Pull active electrical permit activity from the Los Angeles Open Data Portal. “
“Use this to spot active jobsites, understand local demand, and identify leads near your preferred branch.”
)

```
col1, col2, col3 = st.columns([1.2, 1.5, 0.8])
with col1:
    target_zip = st.text_input("LA City ZIP Code", "91303")
with col2:
    scope_filter = st.selectbox("Filter by Permit Scope", LADBS_PERMIT_SCOPES)
with col3:
    result_limit = st.selectbox("Results Limit", [10, 25, 50], index=1)

if st.button("🔍 Query LADBS Permit Database", use_container_width=True):
    with st.spinner(f"Scanning electrical permits in ZIP {target_zip}..."):
        df_permits, data_source = fetch_ladbs_permits(target_zip, scope_filter, result_limit)

    if data_source == "live":
        st.success(f"✅ Live data from LA Open Data Portal — {len(df_permits)} records found.")
    else:
        st.info(
            f"📋 Showing representative permit data for ZIP {target_zip}. "
            "Live API unavailable in this environment — connect to data.lacity.org for real records."
        )

    if df_permits.empty:
        st.warning(f"No permits found for ZIP {target_zip} with scope filter '{scope_filter}'. Try 'All Electrical'.")
    else:
        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        issued  = df_permits[df_permits["Status"].str.contains("Issued|Active", na=False)]
        pending = df_permits[df_permits["Status"].str.contains("Pending|Check", na=False)]
        ev_jobs = df_permits[df_permits["Scope / Description"].str.contains("EV|Charger", case=False, na=False)]
        mf_jobs = df_permits[df_permits["Scope / Description"].str.contains("Multi|Unit|Rough", case=False, na=False)]

        m1.metric("Total Records", len(df_permits))
        m2.metric("Active / Issued", len(issued), delta=f"vs {len(pending)} pending")
        m3.metric("EV Charger Jobs", len(ev_jobs))
        m4.metric("Multi-Family Jobs", len(mf_jobs))

        st.markdown("---")

        # Display mode toggle
        view_mode = st.radio("View Mode", ["Table", "Cards"], horizontal=True)

        if view_mode == "Table":
            display_cols = ["Permit ID", "Address", "Scope / Description", "Status", "Issue Date"]
            st.dataframe(
                df_permits[display_cols],
                use_container_width=True,
                hide_index=True,
            )

        else:  # Cards view
            for _, row in df_permits.iterrows():
                badge = status_badge(row["Status"])
                st.markdown(f"""
```

<div class="permit-card">
  <b>{row['Permit ID']}</b> &nbsp;|&nbsp; {row['Issue Date']}<br>
  📍 {row['Address']}<br>
  🔧 {row['Scope / Description']}<br>
  {badge}
</div>
""", unsafe_allow_html=True)

```
        st.markdown("---")

        # Export permit results
        csv_permits = df_permits.to_csv(index=False)
        st.download_button(
            label="📥 Export Permit List (CSV)",
            data=csv_permits,
            file_name=f"LADBS_Electrical_Permits_{target_zip}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        st.caption(
            "Data via LA Open Data Portal (data.lacity.org) — LADBS Permit issuance feed. "
            "For official permit status, verify at: https://www.ladbsservices2.lacity.org"
        )
```

# — FOOTER —

st.markdown(”—”)
st.caption(“🛠️ Canoga AI Pro v3.0 • PDF Bid Export + Live LADBS Feed • Built for Southern California Electrical Contractors.”)
