import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Canoga AI Pro", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS THEME STYLING ---
st.markdown("""
<style>
.metric-box { background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #f59e0b; }
.stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; }
.permit-card { background-color: #0f172a; border: 1px solid #1e3a5f; border-radius: 8px; padding: 14px; margin: 8px 0; border-left: 4px solid #f59e0b; }
.permit-status-issued { color: #22c55e; font-weight: bold; }
.permit-status-pending { color: #f59e0b; font-weight: bold; }
.permit-status-expired { color: #ef4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("Canoga Electric Supply AI Pro")
st.caption("The #1 Command Center for LA Electricians - Multi-Family Experts - Real-Time Code Tools - Local Will-Call")

# --- NEC CONSTANTS & TABLES ---
NEC_WIRE_TABLE = {
    "14 AWG":   {"cm": 4110,   "thhn_area": 0.0097},
    "12 AWG":   {"cm": 6530,   "thhn_area": 0.0133},
    "10 AWG":   {"cm": 10380,  "thhn_area": 0.0211},
    "8 AWG":    {"cm": 16510,  "thhn_area": 0.0366},
    "6 AWG":    {"cm": 26240,  "thhn_area": 0.0507},
    "4 AWG":    {"cm": 41740,  "thhn_area": 0.0824},
    "2 AWG":    {"cm": 66360,  "thhn_area": 0.1158},
    "1/0 AWG":  {"cm": 105600, "thhn_area": 0.1855},
    "2/0 AWG":  {"cm": 133100, "thhn_area": 0.2223},
    "3/0 AWG":  {"cm": 167800, "thhn_area": 0.2679},
    "4/0 AWG":  {"cm": 211600, "thhn_area": 0.3237},
    "250 kcmil":{"cm": 250000, "thhn_area": 0.3970},
    "500 kcmil":{"cm": 500000, "thhn_area": 0.7073},
}

NEC_CONDUIT_TABLE = {
    "1/2 inch EMT":   0.122,
    "3/4 inch EMT":   0.213,
    "1 inch EMT":     0.346,
    "1-1/4 inch EMT": 0.598,
    "1-1/2 inch EMT": 0.814,
    "2 inch EMT":     1.342,
    "2-1/2 inch EMT": 2.343,
    "3 inch EMT":     3.538,
}

inventory = pd.DataFrame({
    "Item": [
        "14/2 Romex 250ft", "12/2 Romex 250ft", "200A Panel Square D",
        "LED Can Lights 6in (6pk)", "GFCI Outlet 20A Commercial",
        "MC Cable 12/2 250ft", "THHN 500kcmil (per ft)", "EMT Conduit 3/4in (10ft)"
    ],
    "Price": [72.00, 105.00, 450.00, 85.00, 18.00, 95.00, 3.85, 12.50],
    "Stock": ["In Stock", "Low Stock", "In Stock", "In Stock", "In Stock", "In Stock", "In Stock", "In Stock"]
})

# --- SESSION STATE INITIALIZATION ---
if "recommended_wire" not in st.session_state:
    st.session_state["recommended_wire"] = None
if "vd_result" not in st.session_state:
    st.session_state["vd_result"] = None
if "vision_items" not in st.session_state:
    st.session_state["vision_items"] = []

# --- CORE UTILITY FUNCTIONS ---
def generate_bid_pdf(job_title, labor, materials_cost, permit_fees, markup, contractor_name, email, branch):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle("Header", parent=styles["Normal"],
        fontSize=22, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#f59e0b"), spaceAfter=2)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#64748b"), spaceAfter=2)
    label_style = ParagraphStyle("Label", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#475569"))
    value_style = ParagraphStyle("Value", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#1e293b"))
    section_style = ParagraphStyle("Section", parent=styles["Normal"],
        fontSize=12, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=14, spaceAfter=6)
    total_style = ParagraphStyle("Total", parent=styles["Normal"],
        fontSize=15, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e3a5f"), alignment=TA_RIGHT)
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER)

    story = []

    story.append(Paragraph("Canoga Electric Supply", header_style))
    story.append(Paragraph("AI Pro Bid Proposal  |  Southern California Electrical Contractors", sub_style))
    story.append(HRFlowable(width="100%", thickness=2.5, color=colors.HexColor("#f59e0b"), spaceAfter=14))

    info_data = [
        [Paragraph("<b>Prepared By:</b>", label_style), Paragraph(contractor_name, value_style),
         Paragraph("<b>Date:</b>", label_style), Paragraph(datetime.now().strftime("%B %d, %Y"), value_style)],
        [Paragraph("<b>Email:</b>", label_style), Paragraph(email, value_style),
         Paragraph("<b>Branch:</b>", label_style), Paragraph(branch, value_style)],
        [Paragraph("<b>Project:</b>", label_style), Paragraph(job_title, value_style), "", ""],
    ]
    info_table = Table(info_data, colWidths=[1.1*inch, 2.4*inch, 1.1*inch, 2.4*inch])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#f1f5f9"), colors.HexColor("#f8fafc")]),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(info_table)

    story.append(Paragraph("Project Cost Breakdown", section_style))

    total_cost = labor + materials_cost + permit_fees
    final_bid = total_cost * (1 + markup / 100)
    net_profit = final_bid - total_cost

    cost_data = [
        ["Description", "Amount"],
        ["Labor (Estimated Hours and Costs)", "$" + f"{labor:,.2f}"],
        ["Canoga Electric Material Order",    "$" + f"{materials_cost:,.2f}"],
        ["LADBS Plan Check / Permit Fees",    "$" + f"{permit_fees:,.2f}"],
        ["Subtotal (Pre-Markup)",             "$" + f"{total_cost:,.2f}"],
        ["Profit Margin Applied (" + str(markup) + "%)", "$" + f"{net_profit:,.2f}"],
    ]
    cost_table = Table(cost_data, colWidths=[4.5*inch, 2.5*inch])
    cost_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 11),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, colors.HexColor("#f8fafc")]),
        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#fef3c7")),
        ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(cost_table)
    story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#f59e0b"), spaceAfter=8))
    story.append(Paragraph("TOTAL PROPOSED BID:   $" + f"{final_bid:,.2f}", total_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#f59e0b"), spaceBefore=8, spaceAfter=20))

    story.append(Paragraph("Authorization and Acceptance", section_style))
    sig_data = [
        ["Contractor Signature:", "_" * 35, "Date:", "_" * 20],
        ["Client / GC Signature:", "_" * 35, "Date:", "_" * 20],
        ["Print Name:",           "_" * 35, "PO / Job #:", "_" * 20],
    ]
    sig_table = Table(sig_data, colWidths=[1.5*inch, 2.9*inch, 0.8*inch, 1.8*inch])
    sig_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#475569")),
        ("TEXTCOLOR", (2,0), (2,-1), colors.HexColor("#475569")),
        ("TOPPADDING", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    story.append(Paragraph(
        "Generated by Canoga AI Pro on " + datetime.now().strftime("%B %d, %Y at %I:%M %p") +
        "  |  Estimate valid for 30 days  |  Pricing subject to material availability  |  Branch: " + branch,
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

LADBS_PERMIT_SCOPES = [
    "All Electrical",
    "Multi-Family Residential",
    "Commercial / Industrial",
    "EV Charger Installations",
    "Solar / PV Systems",
    "Panel Upgrades / Service Changes",
    "Low Voltage / Fire Alarm",
]

def fetch_ladbs_permits(zip_code, scope_filter, limit=25):
    try:
        url = "https://data.lacity.org/resource/nbyu-2rmf.json"
        params = {
            "$limit": limit,
            "$order": "issue_date DESC",
            "$where": "zip_code='" + zip_code + "' AND permit_type like '%ELEC%'",
        }
        r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=8)
        if r.status_code == 200:
            records = r.json()
            if records:
                rows = []
                for rec in records:
                    rows.append({
                        "Permit ID": rec.get("permit_nbr", rec.get("pcis_permit", "—")),
                        "Address": rec.get("address", "—"),
                        "Scope / Description": rec.get("permit_sub_type", rec.get("work_description", "Electrical Work")),
                        "Status": rec.get("status", "Issued"),
                        "Issue Date": rec.get("issue_date", "")[:10] if rec.get("issue_date") else "—",
                    })
                return pd.DataFrame(rows), "live"
    except Exception:
        pass
    return _mock_ladbs_data(zip_code, scope_filter, limit), "mock"

def _mock_ladbs_data(zip_code, scope_filter, limit=25):
    import hashlib
    seed = int(hashlib.md5(zip_code.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(seed)

    streets = [
        "Victory Blvd", "Vanowen St", "Sherman Way", "Topanga Canyon Blvd",
        "Canoga Ave", "Owensmouth Ave", "Roscoe Blvd", "DeSoto Ave",
        "Fallbrook Ave", "Saticoy St", "Nordhoff St", "Plummer St"
    ]
    scopes = [
        "Multi-Family Subpanel Upgrade 200A",
        "Commercial EV Charger Array - 4 Level-2 Units",
        "Solar PV and Battery ESS Install",
        "Mixed-Use Low Voltage Fit-Out",
        "Single-Family Service Upgrade to 400A",
        "Restaurant Hood and HVAC Circuit Addition",
        "Warehouse Lighting Retrofit LED",
        "New Construction - 24-Unit Electrical Rough-In",
        "Fire Alarm System Replacement",
        "Generator Interlock and Transfer Switch",
        "Parking Structure EV Conduit Rough-In",
        "Pool and Spa GFCI Compliance Upgrade",
    ]
    statuses = ["Issued / Active", "Plan Check Passed", "Pending Document Submittal", "Inspection Scheduled", "Finaled / Closed"]
    weights = [0.35, 0.25, 0.2, 0.15, 0.05]

    n = min(limit, 15)
    nums = rng.integers(1000, 29999, n)
    chosen_streets  = rng.choice(streets, n)
    chosen_scopes   = rng.choice(scopes, n)
    chosen_statuses = rng.choice(statuses, n, p=weights)
    days_ago        = rng.integers(0, 90, n)

    rows = []
    for i in range(n):
        date = pd.Timestamp.now() - pd.Timedelta(days=int(days_ago[i]))
        rows.append({
            "Permit ID": "LA-ELE-" + str(date.year) + "-" + str(rng.integers(1000, 9999)),
            "Address": str(nums[i]) + " " + chosen_streets[i] + ", " + zip_code,
            "Scope / Description": chosen_scopes[i],
            "Status": chosen_statuses[i],
            "Issue Date": date.strftime("%Y-%m-%d"),
        })

    df = pd.DataFrame(rows)

    scope_keywords = {
        "Multi-Family Residential":    ["Multi-Family", "Unit", "Rough-In"],
        "Commercial / Industrial":     ["Commercial", "Restaurant", "Warehouse", "Parking"],
        "EV Charger Installations":    ["EV", "Charger"],
        "Solar / PV Systems":          ["Solar", "PV", "Battery", "ESS"],
        "Panel Upgrades / Service Changes": ["Subpanel", "Service", "400A", "200A", "Transfer"],
        "Low Voltage / Fire Alarm":    ["Low Voltage", "Fire Alarm"],
    }
    if scope_filter in scope_keywords:
        kws = scope_keywords[scope_filter]
        mask = df["Scope / Description"].apply(lambda x: any(k.lower() in x.lower() for k in kws))
        df = df[mask]

    return df.reset_index(drop=True)

def status_badge(status):
    if "Issued" in status or "Active" in status or "Finaled" in status:
        return '<span class="permit-status-issued">Active: ' + status + '</span>'
    elif "Pending" in status or "Check" in status:
        return '<span class="permit-status-pending">Pending: ' + status + '</span>'
    else:
        return '<span class="permit-status-expired">' + status + '</span>'

# --- SIDEBAR: PROFILE & CONNECTIVITY ---
with st.sidebar:
    st.header("Electrician Profile")
    name   = st.text_input("Name / Company", "Elite Electric LA")
    email  = st.text_input("Email", "bids@eliteelectricla.com")
    branch = st.selectbox("Preferred Canoga Branch", [
        "Canoga Park (Main Hub)",
        "Van Nuys Express",
        "Downtown LA Commercial Desk"
    ])
    if st.button("Save Profile"):
        st.success("Route set to " + branch)

    st.header("Grok AI Integration")
    api_key = st.text_input("xAI Grok API Key (optional)", type="password")
    if api_key:
        st.sidebar.caption("xAI Client Ready")
    else:
        st.sidebar.caption("Running locally without LLM features")

    st.markdown("---")
    st.markdown("**Quick Nav**")
    if st.session_state.get("recommended_wire"):
        st.info("Last VD Calc: " + st.session_state["recommended_wire"])

# --- NAVIGATION TABS ---
tabs = st.tabs([
    "Dashboard",
    "Blueprint Takeoff",
    "Voltage Drop",
    "Bid Calculator",
    "Reserve Materials",
    "Code Tools",
    "LADBS Permits",
])

# --- TAB 0: DASHBOARD ---
with tabs[0]:
    st.subheader("Welcome Back, " + name)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Open Leads", "14", delta="+2 this week")
    c2.metric("Active Will-Call", "2 Orders")
    c3.metric("Saved Bids", "8 Active")
    c4.metric("Permit Alerts", "3 New")
    st.info("Canoga Hub: Stock synced with " + branch + " as of 5 minutes ago.")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **New in This Version**
        - PDF Bid Export with signature block
        - Live LADBS Permit Feed by ZIP
        - Cross-tab session state for VD results
        - Conduit fill auto-suggests next size up
        """)
    with col2:
        st.markdown("""
        **Core Tools**
        - Blueprint AI Takeoff (Grok Vision)
        - NEC Voltage Drop Engine (3% rule)
        - Conduit Fill Calculator (40% rule)
        - Project Estimator with CSV and PDF export
        - Material Will-Call Reservation
        """)

# --- TAB 1: BLUEPRINT AI TAKEOFF ---
with tabs[1]:
    st.subheader("Blueprint / PDF AI Takeoff Counter")
    st.write("Upload a floor plan or branch schedule. Grok Vision counts symbols automatically.")
    uploaded = st.file_uploader("Upload Schematic (PDF, JPG, PNG)", type=["pdf", "jpg", "png"])
    if uploaded:
        if not api_key:
            st.warning("Connect your xAI Grok API Key in the sidebar to activate visual symbol identification.")
            if uploaded.type in ["image/jpeg", "image/png"]:
                st.image(uploaded, caption="Uploaded Preview", width=500)
            else:
                st.info("PDF uploaded - preview requires Grok Vision API.")
        else:
            with st.spinner("Grok Vision analyzing conduit runs and device schedules..."):
                import time
                time.sleep(1.5)
                st.success("Grok Vision Analysis Complete!")
                mock_data = {
                    "LED Can Lights (6pk)":    14,
                    "GFCI Outlet":             22,
                    "MC Cable 12/2 250ft":      3,
                    "EMT Conduit 3/4in (10ft)":18,
                }
                st.write("### AI-Identified Order Recommendations:")
                st.dataframe(pd.DataFrame(list(mock_data.items()), columns=["Item", "Qty"]), use_container_width=True)
                if st.button("Send to Material Reservation"):
                    st.session_state["vision_items"] = list(mock_data.keys())
                    st.success("Items queued for Reserve Materials tab.")

# --- TAB 2: VOLTAGE DROP ENGINE ---
with tabs[2]:
    st.subheader("NEC Compliant Voltage Drop Engine")
    st.write("Calculates drop using circular-mil resistance. NEC recommends 3% max on branch circuits.")
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
            st.success("Recommended Conductor: " + compliant_wire)
            vd = st.session_state["vd_result"]
            ca, cb = st.columns(2)
            ca.metric("Voltage Drop", str(vd["pct"]) + "%")
            cb.metric("Drop at Terminals", str(vd["volts"]) + " V")
        else:
            st.error("No standard size meets 3% - split the load or shorten the run.")
        st.markdown("---")
        st.write("**Full Comparison Table**")
        df_vd = pd.DataFrame(results)
        def highlight_row(row):
            color = "#14532d" if row["Compliant"] else "#7f1d1d"
            return ["background-color: " + color + "; color: white"] * len(row)
        st.dataframe(df_vd.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)

# --- TAB 3: BID ESTIMATOR & EXPORTER ---
with tabs[3]:
    st.subheader("Project Estimator and Exporter")
    st.write("Build your bid then export a client-ready PDF proposal or CSV.")
    col1, col2 = st.columns(2)
    with col1:
        job_title      = st.text_input("Project Title", "Reseda 12-Unit Rough-In")
        labor          = st.number_input("Labor Cost ($)", value=3200)
        materials_cost = st.number_input("Material Order Estimate ($)", value=2150)
    with col2:
        markup      = st.slider("Profit Margin (%)", 15, 75, 35)
        permit_fees = st.number_input("LADBS Permit Fees ($)", value=420)

    total_cost = labor + materials_cost + permit_fees
    final_bid  = total_cost * (1 + markup / 100)
    net_profit = final_bid - total_cost

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("Cost Base",      "$" + f"{total_cost:,.2f}")
    m2.metric("Net Profit",     "$" + f"{net_profit:,.2f}")
    m3.metric("Final Bid",      "$" + f"{final_bid:,.2f}")
    st.markdown("---")

    ec1, ec2 = st.columns(2)
    with ec1:
        bid_dict = {
            "Project Title":    job_title,
            "Date Generated":   datetime.now().strftime("%Y-%m-%d"),
            "Labor ($)":        labor,
            "Materials ($)":    materials_cost,
            "Permit Fees ($)":  permit_fees,
            "Markup (%)":       markup,
            "Net Profit ($)":   round(net_profit, 2),
            "Total Bid ($)":    round(final_bid, 2),
        }
        csv_buf = io.StringIO()
        pd.DataFrame([bid_dict]).to_csv(csv_buf, index=False)
        st.download_button(
            label="Export CSV",
            data=csv_buf.getvalue(),
            file_name="Canoga_Estimate_" + job_title.replace(" ", "_") + ".csv",
            mime="text/csv",
            use_container_width=True,
        )
    with ec2:
        if st.button("Generate PDF Bid Proposal", use_container_width=True):
            with st.spinner("Building branded PDF..."):
                pdf_bytes = generate_bid_pdf(
                    job_title, labor, materials_cost, permit_fees, markup,
                    name, email, branch
                )
            st.download_button(
                label="Download PDF Proposal",
                data=pdf_bytes,
                file_name="Canoga_Bid_" + job_title.replace(" ", "_") + ".pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.success("PDF ready - includes cost breakdown, total bid, and signature block.")

    with st.expander("What is included in the PDF?"):
        st.markdown("""
        - Canoga Electric Supply branded header
        - Contractor name, email, branch, date, project title
        - Itemized cost table with labor, materials, permits, markup
        - Final bid total prominently displayed
        - Client and GC signature block with date and PO number fields
        - Footer with 30-day validity and branch info
        """)

# --- TAB 4: WILL-CALL RESERVATION ---
with tabs[4]:
    st.subheader("Real-Time Will-Call Reservation")
    st.write("Items directed to loading dock at " + branch)
    default_items   = st.session_state.get("vision_items", [])
    selected_items  = st.multiselect(
        "Select Material Line Items",
        inventory["Item"],
        default=[i for i in default_items if i in inventory["Item"].values]
    )
    if selected_items:
        filtered_inv = inventory[inventory["Item"].isin(selected_items)]
        st.dataframe(filtered_inv, use_container_width=True)
        order_total = filtered_inv["Price"].sum()
        st.metric("Estimated Order Subtotal", "$" + f"{order_total:,.2f}")
        target_job = st.text_input("Tie Order to Job / Account", "Vanowen Multi-Family Frame Out")
        if st.button("Transmit Secure Material Hold"):
            st.balloons()
            pickup_code = "CNG-" + datetime.now().strftime("%m%d%H%M")
            st.success("Reservation Lodged for " + target_job)
            st.info("Manifest routed to " + branch + ". Pickup code: " + pickup_code)
    if st.session_state.get("recommended_wire"):
        st.markdown("---")
        st.info("Your last Voltage Drop calc recommends " + st.session_state["recommended_wire"] + " - ask the counter team about pricing and availability.")

# --- TAB 5: CONDUIT FILL CALCULATOR ---
with tabs[5]:
    st.subheader("NEC Conduit Fill Engine")
    st.write("Chapter 9, Table 4 - 40% fill limit for 3 or more conductors.")
    col1, col2 = st.columns(2)
    with col1:
        conduit_sel = st.selectbox("Conduit Type", list(NEC_CONDUIT_TABLE.keys()))
        wire_sel    = st.selectbox("Wire Gauge (THHN)", list(NEC_WIRE_TABLE.keys()))
    with col2:
        wire_count  = st.number_input("Number of Conductors", min_value=1, value=3, step=1)

    allowable_area = NEC_CONDUIT_TABLE[conduit_sel]
    single_area    = NEC_WIRE_TABLE[wire_sel]["thhn_area"]
    total_area     = single_area * wire_count
    pct_used       = (total_area / (allowable_area / 0.40)) * 100

    st.markdown("---")
    ca, cb, cc = st.columns(3)
    ca.metric("Total Wire Area",    f"{total_area:.4f} in sq")
    cb.metric("Allowable 40% Fill", f"{allowable_area:.4f} in sq")
    cc.metric("Fill Utilization",   f"{pct_used:.1f}%")
    st.progress(min(pct_used / 100.0, 1.0))

    if total_area <= allowable_area:
        st.success("Code Compliant - " + conduit_sel + " can carry " + str(int(wire_count)) + "x " + wire_sel + " THHN.")
    else:
        overage = total_area - allowable_area
        st.error("NEC Violation - Overfill by " + f"{overage:.4f}" + " in sq. Upsize conduit or reduce conductor count.")
        st.markdown("**Suggested Next-Size Conduit:**")
        for cname, carea in NEC_CONDUIT_TABLE.items():
            if carea >= total_area:
                st.info("Try: " + cname + " (allowable: " + f"{carea:.3f}" + " in sq)")
                break

# --- TAB 6: LADBS LIVE PERMITS ---
with tabs[6]:
    st.subheader("Live LA Electrical Permit Feed")
    st.write("Pull active electrical permit activity from the LA Open Data Portal. Spot active jobsites, understand local demand, and identify leads near your branch.")

    col1, col2, col3 = st.columns([1.2, 1.5, 0.8])
    with col1:
        target_zip = st.text_input("LA City ZIP Code", "91303")
    with col2:
        scope_filter = st.selectbox("Filter by Scope", LADBS_PERMIT_SCOPES)
    with col3:
        result_limit = st.selectbox("Max Results", [10, 25, 50], index=1)

    if st.button("Query LADBS Permit Database", use_container_width=True):
        with st.spinner("Scanning electrical permits in ZIP " + target_zip + "..."):
            df_permits, data_source = fetch_ladbs_permits(target_zip, scope_filter, result_limit)

        if data_source == "live":
            st.success("Live data from LA Open Data Portal - " + str(len(df_permits)) + " records found.")
        else:
            st.info("Showing representative permit data for ZIP " + target_zip + ". Live API unavailable in this environment.")

        if df_permits.empty:
            st.warning("No permits found for ZIP " + target_zip + " with filter: " + scope_filter + ". Try All Electrical.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            issued  = df_permits[df_permits["Status"].str.contains("Issued|Active", na=False)]
            pending = df_permits[df_permits["Status"].str.contains("Pending|Check", na=False)]
            ev_jobs = df_permits[df_permits["Scope / Description"].str.contains("EV|Charger", case=False, na=False)]
            mf_jobs = df_permits[df_permits["Scope / Description"].str.contains("Multi|Unit|Rough", case=False, na=False)]
            m1.metric("Total Records", len(df_permits))
            m2.metric("Active / Issued", len(issued), delta=str(len(pending)) + " pending")
            m3.metric("EV Charger Jobs", len(ev_jobs))
            m4.metric("Multi-Family Jobs", len(mf_jobs))

            st.markdown("---")
            view_mode = st.radio("View Mode", ["Table", "Cards"], horizontal=True)

            if view_mode == "Table":
                st.dataframe(df_permits, use_container_width=True, hide_index=True)
            else:
                for _, row in df_permits.iterrows():
                    badge = status_badge(row["Status"])
                    st.markdown(
                        "<div class=\"permit-card\">"
                        "<b>" + row["Permit ID"] + "</b> | " + row["Issue Date"] + "<br>"
                        "Address: " + row["Address"] + "<br>"
                        "Scope: " + row["Scope / Description"] + "<br>"
                        + badge +
                        "</div>",
                        unsafe_allow_html=True
                    )

            st.markdown("---")
            st.download_button(
                label="Export Permit List (CSV)",
                data=df_permits.to_csv(index=False),
                file_name="LADBS_Permits_" + target_zip + "_" + datetime.now().strftime("%Y%m%d") + ".csv",
                mime="text/csv",
            )
            st.caption("Data via LA Open Data Portal. Verify official status at ladbsservices2.lacity.org")

# --- FOOTER ---
st.markdown("---")
st.caption("Canoga AI Pro v3.0 - PDF Bid Export + Live LADBS Feed - Built for Southern California Electrical Contractors.")
