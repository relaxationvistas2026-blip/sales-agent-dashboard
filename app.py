import streamlit as st
import pandas as pd
import json
import os

# Set page config for a full-width experience and tab title
st.set_page_config(
    page_title="Mate Sales Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load data from Excel dynamically
excel_file = "Antigravity Sales Agent.xlsx"

@st.cache_data
def load_and_process_data(file_path):
    if not os.path.exists(file_path):
        return None, None, None
    
    # Read sheets
    df_customers = pd.read_excel(file_path, sheet_name="Customers")
    df_sales = pd.read_excel(file_path, sheet_name="Daily Sales")
    df_inventory = pd.read_excel(file_path, sheet_name="Inventory")
    
    # Clean sheet names and string spacing
    df_customers.columns = df_customers.columns.str.strip()
    df_sales.columns = df_sales.columns.str.strip()
    df_inventory.columns = df_inventory.columns.str.strip()
    
    # Handle dates
    df_sales["Date"] = pd.to_datetime(df_sales["Date"]).dt.strftime("%b %d")
    df_customers["Date"] = pd.to_datetime(df_customers["Date"]).dt.strftime("%b %d")
    
    # Group Sales into Orders by (Customer, Date)
    orders_grouped = df_sales.groupby(["Customer", "Date"])
    
    orders = []
    order_id_counter = 192530
    
    # Map customers to their contact info
    cust_info = {}
    for _, row in df_customers.iterrows():
        name = str(row["Customer Name"]).strip()
        cust_info[name] = {
            "email": str(row["Email Address"]) if pd.notna(row["Email Address"]) else f"{name.lower().replace(' ', '')}@gmail.com",
            "phone": str(row["Phone Number"]) if pd.notna(row["Phone Number"]) else "+1 (415) 555-2671",
            "address": str(row["Shipping Address"]) if pd.notna(row["Shipping Address"]) else "N/A"
        }
        
    for (customer_name, date), group in orders_grouped:
        customer_name_clean = str(customer_name).strip()
        info = cust_info.get(customer_name_clean, {
            "email": f"{customer_name_clean.lower().replace(' ', '')}@gmail.com",
            "phone": "+1 (415) 555-2671",
            "address": "N/A, USA"
        })
        
        # Calculate total revenue
        total_revenue = float(group["Revenue (USD)"].sum())
        
        # Determine status deterministically
        # Julia: Paid, Leo: Paid, Mary: Paid, AvrilLwin: Refunded, Jeneffer: Cancelled, others: Paid
        status = "Paid"
        if customer_name_clean == "Jeneffer":
            status = "Cancelled"
        elif customer_name_clean == "AvrilLwin":
            status = "Refunded"
            
        # Determine type based on address
        addr = info["address"]
        order_type = "Shipping" if ("Thailand" in addr or "," in addr) and "N/A" not in addr else "Pickups"
        
        # Collect product list
        products = []
        for _, row in group.iterrows():
            products.append({
                "id": str(row["Product ID"]),
                "name": str(row["Product Name"]),
                "units": int(row["Units Sold"]),
                "price": float(row["Revenue (USD)"]) / max(1, int(row["Units Sold"])),
                "total": float(row["Revenue (USD)"])
            })
            
        orders.append({
            "order_id": f"#{order_id_counter}",
            "customer": customer_name_clean,
            "email": info["email"],
            "phone": info["phone"],
            "address": info["address"],
            "type": order_type,
            "status": status,
            "products": products,
            "main_product": products[0]["name"] if len(products) > 0 else "N/A",
            "total": total_revenue,
            "date": date
        })
        order_id_counter += 1
        
    # Reversing to show latest first
    orders.reverse()
    
    # Calculate top sellers
    top_sellers_df = df_sales.groupby("Product Name").agg({
        "Units Sold": "sum",
        "Revenue (USD)": "sum"
    }).reset_index()
    top_sellers_df = top_sellers_df.sort_values(by="Units Sold", ascending=False)
    
    top_sellers = []
    for _, row in top_sellers_df.head(5).iterrows():
        top_sellers.append({
            "name": str(row["Product Name"]),
            "units": int(row["Units Sold"]),
            "revenue": float(row["Revenue (USD)"])
        })
        
    return orders, top_sellers, df_inventory.to_dict(orient="records")

orders, top_sellers, inventory = load_and_process_data(excel_file)

# If data loading fails, show a beautiful fallback
if not orders:
    st.error("Could not load data from 'Antigravity Sales Agent.xlsx'. Please ensure the file is present in the workspace directory.")
    st.stop()

# Aggregate dynamic stats for the sidebar
total_revenue = sum(o["total"] for o in orders)
total_orders_count = len(orders)
paid_count = sum(1 for o in orders if o["status"] == "Paid")
cancelled_count = sum(1 for o in orders if o["status"] == "Cancelled")
refunded_count = sum(1 for o in orders if o["status"] == "Refunded")

paid_pct = round((paid_count / total_orders_count) * 100) if total_orders_count > 0 else 0
cancelled_pct = round((cancelled_count / total_orders_count) * 100) if total_orders_count > 0 else 0
refunded_pct = 100 - paid_pct - cancelled_pct

# Calculate overview parameters
avg_order_value = total_revenue / total_orders_count if total_orders_count > 0 else 0
avg_items_per_order = sum(sum(p["units"] for p in o["products"]) for o in orders) / total_orders_count if total_orders_count > 0 else 0

# Prepare JSON data for client-side JavaScript interactions
orders_json = json.dumps(orders)

# High-fidelity custom CSS & HTML matching the dashboard reference image
html_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mate Sales Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
        }}
        
        body {{
            background-color: #f8fafc;
            color: #1e293b;
            overflow-x: hidden;
        }}

        .dashboard-container {{
            display: flex;
            min-height: 100vh;
            width: 100vw;
        }}

        /* Left Sidebar: Midnight Navy Theme */
        .sidebar {{
            width: 260px;
            background-color: #0b1329;
            color: #94a3b8;
            padding: 24px 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            flex-shrink: 0;
            border-right: 1px solid #1e293b;
        }}

        .sidebar-brand {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #ffffff;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 24px;
            padding: 0 8px;
        }}

        .brand-logo {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .brand-logo-icon {{
            width: 24px;
            height: 24px;
            background: linear-gradient(135deg, #6366f1, #3b82f6);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 14px;
            color: #ffffff;
        }}

        .sidebar-collapse-btn {{
            cursor: pointer;
            color: #475569;
            transition: color 0.2s;
        }}

        .sidebar-collapse-btn:hover {{
            color: #94a3b8;
        }}

        .search-box {{
            background-color: #111e3b;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 24px;
        }}

        .search-box input {{
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-size: 14px;
            width: 100%;
        }}

        .search-box input::placeholder {{
            color: #475569;
        }}

        .search-shortcut {{
            font-size: 11px;
            background-color: #1e293b;
            padding: 2px 6px;
            border-radius: 4px;
            color: #475569;
        }}

        .menu-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-bottom: auto;
        }}

        .menu-item a {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 12px;
            color: #94a3b8;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            border-radius: 8px;
            transition: all 0.2s;
        }}

        .menu-item.active a, .menu-item a:hover {{
            background-color: #111e3b;
            color: #ffffff;
        }}

        .menu-item .badge {{
            background-color: #ef4444;
            color: #ffffff;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 9999px;
            margin-left: auto;
        }}

        .sidebar-footer {{
            padding-top: 16px;
            border-top: 1px solid #1e293b;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .user-avatar {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #10b981, #059669);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-weight: 600;
            font-size: 14px;
        }}

        .user-info {{
            display: flex;
            flex-direction: column;
        }}

        .user-name {{
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
        }}

        .user-role {{
            color: #475569;
            font-size: 11px;
        }}

        /* Main Workspace: Grid Layout */
        .workspace {{
            flex-grow: 1;
            display: grid;
            grid-template-columns: 1fr 340px;
            background-color: #f8fafc;
        }}

        /* Main Content Section */
        .main-content {{
            padding: 32px;
            border-right: 1px solid #e2e8f0;
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow-y: auto;
            position: relative;
        }}

        .header-section {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}

        .header-title {{
            font-size: 28px;
            font-weight: 700;
            color: #0f172a;
        }}

        .header-actions {{
            display: flex;
            gap: 12px;
        }}

        .btn {{
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .btn-dark {{
            background-color: #0f172a;
            color: #ffffff;
            border: 1px solid #0f172a;
        }}

        .btn-dark:hover {{
            background-color: #1e293b;
        }}

        .btn-light {{
            background-color: #ffffff;
            color: #334155;
            border: 1px solid #e2e8f0;
        }}

        .btn-light:hover {{
            background-color: #f1f5f9;
        }}

        /* Filter Section */
        .filters-section {{
            display: flex;
            gap: 8px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}

        .filter-pill {{
            padding: 6px 14px;
            border-radius: 9999px;
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            color: #475569;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}

        .filter-pill:hover {{
            background-color: #f1f5f9;
            color: #0f172a;
        }}

        .filter-pill.active {{
            background-color: #0f172a;
            color: #ffffff;
            border-color: #0f172a;
        }}

        /* Orders Data Table */
        .table-container {{
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            flex-grow: 1;
            margin-bottom: 16px;
        }}

        .orders-table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 14px;
        }}

        .orders-table th {{
            background-color: #f8fafc;
            padding: 14px 16px;
            font-weight: 600;
            color: #64748b;
            border-bottom: 1px solid #e2e8f0;
        }}

        .orders-table td {{
            padding: 16px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
            vertical-align: middle;
        }}

        .orders-table tr:hover {{
            background-color: #f8fafc;
            cursor: pointer;
        }}

        /* Checkbox Styling */
        .checkbox-cell {{
            width: 48px;
            text-align: center;
        }}

        .custom-checkbox {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid #cbd5e1;
            cursor: pointer;
            display: inline-block;
            position: relative;
        }}

        .custom-checkbox.checked {{
            background-color: #0f172a;
            border-color: #0f172a;
        }}

        .custom-checkbox.checked::after {{
            content: "✓";
            color: #ffffff;
            font-size: 11px;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: bold;
        }}

        /* Customer Profile & Avatar */
        .customer-cell {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .cust-avatar {{
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 12px;
            color: #475569;
        }}

        .cust-name {{
            font-weight: 500;
            color: #0f172a;
        }}

        /* Badge Styling */
        .badge-status {{
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .badge-status.paid {{
            color: #10b981;
            background-color: #ecfdf5;
        }}

        .badge-status.paid::before {{
            content: "🟢";
            font-size: 8px;
        }}

        .badge-status.cancelled {{
            color: #ef4444;
            background-color: #fef2f2;
        }}

        .badge-status.cancelled::before {{
            content: "🔴";
            font-size: 8px;
        }}

        .badge-status.refunded {{
            color: #64748b;
            background-color: #f1f5f9;
        }}

        .badge-status.refunded::before {{
            content: "⚫";
            font-size: 8px;
        }}

        /* Action Menu dots */
        .action-dots {{
            color: #94a3b8;
            font-weight: bold;
            cursor: pointer;
            font-size: 18px;
            text-align: center;
            width: 24px;
        }}

        .action-dots:hover {{
            color: #334155;
        }}

        /* Right Analytics Sidebar */
        .analytics-sidebar {{
            background-color: #ffffff;
            padding: 32px 24px;
            overflow-y: auto;
            height: 100vh;
            display: flex;
            flex-direction: column;
            gap: 32px;
        }}

        .analytics-title {{
            font-size: 13px;
            font-weight: 700;
            color: #475569;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        /* Circular Progress Chart */
        .receipt-card {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 24px;
        }}

        .chart-box {{
            position: relative;
            width: 140px;
            height: 140px;
            margin: 0 auto;
        }}

        .chart-svg {{
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }}

        .chart-bg-circle {{
            fill: none;
            stroke: #e2e8f0;
            stroke-width: 12;
        }}

        .chart-progress-circle {{
            fill: none;
            stroke: #10b981;
            stroke-width: 12;
            stroke-dasharray: 339;
            stroke-dashoffset: 80;
            stroke-linecap: round;
            transition: stroke-dashoffset 1s ease-out;
        }}

        .chart-center-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .chart-val {{
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
        }}

        .chart-lbl {{
            font-size: 11px;
            color: #64748b;
            margin-top: 2px;
        }}

        .receipt-breakdown {{
            display: flex;
            justify-content: space-between;
            margin-top: 12px;
        }}

        .breakdown-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .breakdown-val {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
        }}

        .breakdown-lbl {{
            font-size: 11px;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .bullet {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}

        .bullet-green {{ background-color: #10b981; }}
        .bullet-blue {{ background-color: #3b82f6; }}

        /* Status Progress Bars */
        .status-card {{
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 24px;
        }}

        .status-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}

        .status-dropdown {{
            font-size: 12px;
            font-weight: 600;
            color: #475569;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        .progress-bar-container {{
            display: flex;
            height: 8px;
            border-radius: 9999px;
            overflow: hidden;
            background-color: #e2e8f0;
            margin-bottom: 16px;
        }}

        .progress-paid {{ background-color: #10b981; width: {paid_pct}%; }}
        .progress-cancelled {{ background-color: #ef4444; width: {cancelled_pct}%; }}
        .progress-refunded {{ background-color: #64748b; width: {refunded_pct}%; }}

        .status-legend {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .legend-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }}

        .legend-name {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: #475569;
        }}

        .legend-val {{
            font-weight: 600;
            color: #0f172a;
        }}

        /* Overview Metrics Grid */
        .overview-card {{
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 24px;
        }}

        .overview-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 16px;
        }}

        .metric-cell {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .metric-val {{
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
        }}

        .metric-lbl {{
            font-size: 11px;
            color: #64748b;
        }}

        /* Top Sellers list */
        .sellers-card {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .seller-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
        }}

        .seller-item {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .seller-icon {{
            width: 36px;
            height: 36px;
            background-color: #f1f5f9;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }}

        .seller-info {{
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}

        .seller-name {{
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
            max-width: 170px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .seller-desc {{
            font-size: 11px;
            color: #64748b;
        }}

        .seller-count {{
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
        }}

        /* Floating Bottom Action Overlay */
        .action-overlay {{
            position: fixed;
            bottom: 32px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background-color: #0f172a;
            color: #ffffff;
            padding: 12px 24px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            gap: 16px;
            z-index: 100;
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}

        .action-overlay.active {{
            transform: translateX(-50%) translateY(0);
        }}

        .action-overlay-close {{
            cursor: pointer;
            color: #475569;
            font-size: 16px;
            font-weight: bold;
            padding: 0 4px;
        }}

        .action-overlay-close:hover {{
            color: #ffffff;
        }}

        .selected-count-badge {{
            border-right: 1px solid #1e293b;
            padding-right: 16px;
            font-size: 14px;
            font-weight: 500;
            color: #94a3b8;
        }}

        .overlay-btns {{
            display: flex;
            gap: 8px;
        }}

        .btn-overlay {{
            background: transparent;
            border: none;
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .btn-overlay:hover {{
            background-color: #1e293b;
        }}

        /* Details Popover Card Modal (Order #4567 popup in image) */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(15, 23, 42, 0.4);
            backdrop-filter: blur(4px);
            z-index: 200;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease-out;
        }}

        .modal-overlay.active {{
            opacity: 1;
            pointer-events: auto;
        }}

        .modal-card {{
            width: 440px;
            background-color: #ffffff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            transform: scale(0.95);
            transition: transform 0.2s ease-out;
        }}

        .modal-overlay.active .modal-card {{
            transform: scale(1);
        }}

        .modal-header {{
            background-color: #0f172a;
            color: #ffffff;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .modal-title-box {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .modal-title {{
            font-size: 15px;
            font-weight: 600;
        }}

        .modal-actions-top {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}

        .modal-action-icon {{
            cursor: pointer;
            color: #94a3b8;
            transition: color 0.2s;
        }}

        .modal-action-icon:hover {{
            color: #ffffff;
        }}

        .modal-body {{
            padding: 24px 20px;
        }}

        .modal-customer-info {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 24px;
        }}

        .modal-info-row {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: #475569;
        }}

        .modal-info-row span.bold {{
            font-weight: 600;
            color: #0f172a;
        }}

        .modal-tabs {{
            display: flex;
            border-bottom: 1px solid #e2e8f0;
            margin-bottom: 20px;
        }}

        .modal-tab {{
            padding: 8px 16px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            color: #64748b;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }}

        .modal-tab.active {{
            color: #0f172a;
            border-bottom-color: #0f172a;
        }}

        .modal-item-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-bottom: 24px;
            max-height: 200px;
            overflow-y: auto;
        }}

        .modal-item-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}

        .modal-item-detail {{
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }}

        .modal-item-thumb {{
            width: 32px;
            height: 32px;
            background-color: #f1f5f9;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }}

        .modal-item-text {{
            display: flex;
            flex-direction: column;
            gap: 4px;
            max-width: 240px;
        }}

        .modal-item-name {{
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
            line-height: 1.4;
        }}

        .modal-item-meta {{
            font-size: 12px;
            color: #64748b;
        }}

        .modal-item-price {{
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
            text-align: right;
        }}

        .modal-total-section {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
            margin-bottom: 24px;
        }}

        .modal-total-lbl {{
            font-size: 13px;
            color: #475569;
            font-weight: 500;
        }}

        .modal-total-val {{
            font-size: 16px;
            font-weight: 700;
            color: #0f172a;
        }}

        .modal-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            background-color: #f8fafc;
            border-top: 1px solid #e2e8f0;
        }}

        .modal-footer-btns {{
            display: flex;
            gap: 8px;
        }}

        .btn-modal-action {{
            padding: 6px 12px;
            border: 1px solid #cbd5e1;
            background-color: #ffffff;
            color: #334155;
            font-size: 12px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .btn-modal-action:hover {{
            background-color: #f1f5f9;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar Navigation -->
        <aside class="sidebar">
            <div>
                <div class="sidebar-brand">
                    <div class="brand-logo">
                        <div class="brand-logo-icon">M</div>
                        <span>Mate</span>
                    </div>
                    <div class="sidebar-collapse-btn">←</div>
                </div>

                <div class="search-box">
                    <span>🔍</span>
                    <input type="text" id="searchInput" placeholder="Search orders..." onkeyup="filterTable()">
                    <span class="search-shortcut">⌘ F</span>
                </div>

                <ul class="menu-list">
                    <li class="menu-item"><a href="#">📊 Dashboard</a></li>
                    <li class="menu-item active"><a href="#">📋 Orders</a></li>
                    <li class="menu-item"><a href="#">📦 Inventory</a></li>
                    <li class="menu-item"><a href="#">💳 Payments</a></li>
                    <li class="menu-item"><a href="#">👥 Customers</a></li>
                    <li class="menu-item"><a href="#">🔔 Notifications <span class="badge">7</span></a></li>
                    <li class="menu-item"><a href="#">❓ Help & support</a></li>
                    <li class="menu-item"><a href="#">⚙️ Settings</a></li>
                </ul>
            </div>

            <div class="sidebar-footer">
                <div class="user-avatar">OW</div>
                <div class="user-info">
                    <span class="user-name">Olivia Williams</span>
                    <span class="user-role">Sales Manager</span>
                </div>
                <span style="margin-left: auto; cursor: pointer; color: #475569;">•••</span>
            </div>
        </aside>

        <!-- Main Workspace -->
        <div class="workspace">
            <!-- Table content area -->
            <main class="main-content">
                <div class="header-section">
                    <h1 class="header-title">Orders</h1>
                    <div class="header-actions">
                        <button class="btn btn-light">↓ Import</button>
                        <button class="btn btn-dark">↑ Export</button>
                    </div>
                </div>

                <!-- Filters -->
                <div class="filters-section">
                    <div class="filter-pill active" onclick="setFilter('status', 'all', this)">All status</div>
                    <div class="filter-pill" onclick="setFilter('status', 'Paid', this)">🟢 Paid</div>
                    <div class="filter-pill" onclick="setFilter('status', 'Cancelled', this)">🔴 Cancelled</div>
                    <div class="filter-pill" onclick="setFilter('status', 'Refunded', this)">⚫ Refunded</div>
                    <div class="filter-pill" onclick="setFilter('type', 'Shipping', this)">🚚 Shipping</div>
                    <div class="filter-pill" onclick="setFilter('type', 'Pickups', this)">🛍️ Pickups</div>
                </div>

                <!-- Table Container -->
                <div class="table-container">
                    <table class="orders-table" id="ordersTable">
                        <thead>
                            <tr>
                                <th class="checkbox-cell">
                                    <div class="custom-checkbox" id="headerCheckbox" onclick="toggleSelectAll()"></div>
                                </th>
                                <th>Order</th>
                                <th>Customer</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Product</th>
                                <th>Total</th>
                                <th>Date</th>
                                <th style="width: 48px;"></th>
                            </tr>
                        </thead>
                        <tbody>
                            <!-- Generated rows -->
                        </tbody>
                    </table>
                </div>
            </main>

            <!-- Right Analytics Sidebar -->
            <aside class="analytics-sidebar">
                <!-- Receipt of goods -->
                <div class="receipt-card">
                    <h2 class="analytics-title">Receipt of Goods</h2>
                    <div class="chart-box">
                        <svg class="chart-svg" viewBox="0 0 120 120">
                            <circle class="chart-bg-circle" cx="60" cy="60" r="54"></circle>
                            <circle class="chart-progress-circle" cx="60" cy="60" r="54"></circle>
                        </svg>
                        <div class="chart-center-text">
                            <div class="chart-val">${total_revenue / 1000:.1f}k</div>
                            <div class="chart-lbl">{total_orders_count} orders</div>
                        </div>
                    </div>
                    <div class="receipt-breakdown">
                        <div class="breakdown-item">
                            <div class="breakdown-lbl"><span class="bullet bullet-green"></span>Shipments</div>
                            <div class="breakdown-val">${sum(o["total"] for o in orders if o["type"] == "Shipping") / 1000:.1f}k</div>
                        </div>
                        <div class="breakdown-item" style="text-align: right;">
                            <div class="breakdown-lbl" style="justify-content: flex-end;">Pickups<span class="bullet bullet-blue"></span></div>
                            <div class="breakdown-val">${sum(o["total"] for o in orders if o["type"] == "Pickups") / 1000:.1f}k</div>
                        </div>
                    </div>
                </div>

                <!-- Orders Status -->
                <div class="status-card">
                    <div class="status-header">
                        <h2 class="analytics-title">Orders Status</h2>
                        <div class="status-dropdown">Active ▾</div>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-paid"></div>
                        <div class="progress-cancelled"></div>
                        <div class="progress-refunded"></div>
                    </div>
                    <div class="status-legend">
                        <div class="legend-row">
                            <div class="legend-name"><span class="bullet" style="background-color: #10b981;"></span> Paid</div>
                            <div class="legend-val">{paid_pct}%</div>
                        </div>
                        <div class="legend-row">
                            <div class="legend-name"><span class="bullet" style="background-color: #ef4444;"></span> Cancelled</div>
                            <div class="legend-val">{cancelled_pct}%</div>
                        </div>
                        <div class="legend-row">
                            <div class="legend-name"><span class="bullet" style="background-color: #64748b;"></span> Refunded</div>
                            <div class="legend-val">{refunded_pct}%</div>
                        </div>
                    </div>
                </div>

                <!-- Overview Metrics Grid -->
                <div class="overview-card">
                    <div class="status-header">
                        <h2 class="analytics-title">Overview</h2>
                        <div class="status-dropdown">This month ▾</div>
                    </div>
                    <div class="overview-grid">
                        <div class="metric-cell">
                            <div class="metric-val">${avg_order_value:.2f}</div>
                            <div class="metric-lbl">Average order</div>
                        </div>
                        <div class="metric-cell">
                            <div class="metric-val">${total_revenue / 1000:.1f}k</div>
                            <div class="metric-lbl">Total revenue</div>
                        </div>
                        <div class="metric-cell">
                            <div class="metric-val">16 min</div>
                            <div class="metric-lbl">Processing time</div>
                        </div>
                        <div class="metric-cell">
                            <div class="metric-val">{avg_items_per_order:.1f}</div>
                            <div class="metric-lbl">Avg. items/order</div>
                        </div>
                        <div class="metric-cell">
                            <div class="metric-val">0.32%</div>
                            <div class="metric-lbl">Pending orders</div>
                        </div>
                        <div class="metric-cell">
                            <div class="metric-val">0.51%</div>
                            <div class="metric-lbl">Reject rate</div>
                        </div>
                    </div>
                </div>

                <!-- Top Sellers -->
                <div class="sellers-card">
                    <div class="status-header">
                        <h2 class="analytics-title">Top Sellers</h2>
                        <div class="status-dropdown">This month ▾</div>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        {"".join(f'''
                        <div class="seller-row">
                            <div class="seller-item">
                                <div class="seller-icon">👕</div>
                                <div class="seller-info">
                                    <div class="seller-name">{s["name"]}</div>
                                    <div class="seller-desc">Revenue: ${s["revenue"]:.2f}</div>
                                </div>
                            </div>
                            <div class="seller-count">{s["units"]}</div>
                        </div>
                        ''' for s in top_sellers)}
                    </div>
                </div>
            </aside>
        </div>

        <!-- Floating action overlay when rows are checked -->
        <div class="action-overlay" id="actionOverlay">
            <div class="action-overlay-close" onclick="deselectAll()">✕</div>
            <div class="selected-count-badge" id="selectedCountText">Selected: 0</div>
            <div class="overlay-btns">
                <button class="btn-overlay" onclick="alert('Exporting selected orders...')">↑ Export</button>
                <button class="btn-overlay" onclick="alert('Printing selected orders...')">🖨️ Print</button>
                <button class="btn-overlay" onclick="alert('Duplicating selected orders...')">📋 Duplicate</button>
                <span class="action-dots" style="color: #ffffff; padding: 0 8px;">•••</span>
            </div>
        </div>

        <!-- Detail popup card (modal) -->
        <div class="modal-overlay" id="detailModal">
            <div class="modal-card">
                <div class="modal-header">
                    <div class="modal-title-box">
                        <span>📋</span>
                        <span class="modal-title" id="modalOrderId">Order #000000</span>
                    </div>
                    <div class="modal-actions-top">
                        <span class="modal-action-icon" style="font-size: 16px;" onclick="alert('Opening in new tab...')">↗</span>
                        <span class="modal-action-icon" style="font-size: 20px; font-weight: bold; line-height: 1;" onclick="closeModal()">×</span>
                    </div>
                </div>
                <div class="modal-body">
                    <div class="modal-customer-info">
                        <div class="modal-info-row">
                            <span>👤</span>
                            <span class="bold" id="modalCustomerName">Customer Name</span>
                        </div>
                        <div class="modal-info-row">
                            <span>✉️</span>
                            <span id="modalCustomerEmail">email@example.com</span>
                        </div>
                        <div class="modal-info-row">
                            <span>📞</span>
                            <span id="modalCustomerPhone">+1 (415) 555-2671</span>
                        </div>
                        <div class="modal-info-row">
                            <span>🚚</span>
                            <span id="modalCustomerAddress" style="font-size: 12px; line-height: 1.4;">Shipping Address</span>
                        </div>
                    </div>

                    <div class="modal-tabs">
                        <div class="modal-tab active">Order items</div>
                        <div class="modal-tab">Delivery</div>
                        <div class="modal-tab">Docs</div>
                    </div>

                    <div class="modal-item-list" id="modalItemsList">
                        <!-- Items list -->
                    </div>

                    <div class="modal-total-section">
                        <span class="modal-total-lbl">Total:</span>
                        <span class="modal-total-val" id="modalTotalVal">$0.00</span>
                    </div>
                </div>
                <div class="modal-footer">
                    <div class="modal-footer-btns">
                        <button class="btn-modal-action" onclick="alert('Exporting this order...')">↑ Export</button>
                        <button class="btn-modal-action" onclick="alert('Duplicating this order...')">📋 Duplicate</button>
                        <button class="btn-modal-action" onclick="alert('Printing this order...')">🖨️ Print</button>
                    </div>
                    <span class="action-dots" style="color: #64748b;">•••</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const ordersData = {orders_json};
        let selectedOrders = new Set();
        let currentFilterType = 'status';
        let currentFilterVal = 'all';

        // Render the orders table dynamically
        function renderTable() {{
            const tbody = document.querySelector("#ordersTable tbody");
            tbody.innerHTML = "";

            let filtered = ordersData;
            if (currentFilterVal !== 'all') {{
                filtered = ordersData.filter(o => {{
                    if (currentFilterType === 'status') return o.status === currentFilterVal;
                    if (currentFilterType === 'type') return o.type === currentFilterVal;
                    return true;
                }});
            }}

            filtered.forEach(order => {{
                const tr = document.createElement("tr");
                tr.setAttribute("onclick", `showOrderDetails("${{order.order_id}}", event)`);
                
                const isChecked = selectedOrders.has(order.order_id) ? "checked" : "";
                
                tr.innerHTML = `
                    <td class="checkbox-cell" onclick="event.stopPropagation()">
                        <div class="custom-checkbox ${{isChecked}}" onclick="toggleSelectRow('${{order.order_id}}', this)"></div>
                    </td>
                    <td style="font-weight: 600; color: #0f172a;">${{order.order_id}}</td>
                    <td>
                        <div class="customer-cell">
                            <div class="cust-avatar">${{order.customer.substring(0,2).toUpperCase()}}</div>
                            <span class="cust-name">${{order.customer}}</span>
                        </div>
                    </td>
                    <td>${{order.type}}</td>
                    <td>
                        <span class="badge-status ${{order.status.toLowerCase()}}">${{order.status}}</span>
                    </td>
                    <td style="color: #475569; max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${{order.main_product}}</td>
                    <td style="font-weight: 600; color: #0f172a;">$${{order.total.toFixed(2)}}</td>
                    <td style="color: #64748b;">${{order.date}}</td>
                    <td onclick="event.stopPropagation()">
                        <span class="action-dots">•••</span>
                    </td>
                `;
                tbody.appendChild(tr);
            }});
            
            updateHeaderCheckbox();
            updateActionOverlay();
        }}

        // Checkbox functions
        function toggleSelectRow(orderId, el) {{
            if (selectedOrders.has(orderId)) {{
                selectedOrders.delete(orderId);
                el.classList.remove("checked");
            }} else {{
                selectedOrders.add(orderId);
                el.classList.add("checked");
            }}
            updateHeaderCheckbox();
            updateActionOverlay();
        }}

        function toggleSelectAll() {{
            const el = document.getElementById("headerCheckbox");
            const isAllChecked = el.classList.contains("checked");
            
            let filtered = ordersData;
            if (currentFilterVal !== 'all') {{
                filtered = ordersData.filter(o => {{
                    if (currentFilterType === 'status') return o.status === currentFilterVal;
                    if (currentFilterType === 'type') return o.type === currentFilterVal;
                    return true;
                }});
            }}

            if (isAllChecked) {{
                filtered.forEach(o => selectedOrders.delete(o.order_id));
                el.classList.remove("checked");
            }} else {{
                filtered.forEach(o => selectedOrders.add(o.order_id));
                el.classList.add("checked");
            }}
            
            renderTable();
        }}

        function updateHeaderCheckbox() {{
            const el = document.getElementById("headerCheckbox");
            
            let filtered = ordersData;
            if (currentFilterVal !== 'all') {{
                filtered = ordersData.filter(o => {{
                    if (currentFilterType === 'status') return o.status === currentFilterVal;
                    if (currentFilterType === 'type') return o.type === currentFilterVal;
                    return true;
                }});
            }}

            if (filtered.length === 0) {{
                el.classList.remove("checked");
                return;
            }}

            const allSelected = filtered.every(o => selectedOrders.has(o.order_id));
            if (allSelected) {{
                el.classList.add("checked");
            }} else {{
                el.classList.remove("checked");
            }}
        }}

        function deselectAll() {{
            selectedOrders.clear();
            renderTable();
        }}

        function updateActionOverlay() {{
            const overlay = document.getElementById("actionOverlay");
            const badge = document.getElementById("selectedCountText");
            
            if (selectedOrders.size > 0) {{
                badge.innerText = `Selected: ${{selectedOrders.size}}`;
                overlay.classList.add("active");
            }} else {{
                overlay.classList.remove("active");
            }}
        }}

        // Modal popover functions
        function showOrderDetails(orderId, event) {{
            const order = ordersData.find(o => o.order_id === orderId);
            if (!order) return;

            document.getElementById("modalOrderId").innerText = `Order ${{order.order_id}}`;
            document.getElementById("modalCustomerName").innerText = order.customer;
            document.getElementById("modalCustomerEmail").innerText = order.email;
            document.getElementById("modalCustomerPhone").innerText = order.phone;
            document.getElementById("modalCustomerAddress").innerText = order.address;
            document.getElementById("modalTotalVal").innerText = `$${{order.total.toFixed(2)}}`;

            const list = document.getElementById("modalItemsList");
            list.innerHTML = "";
            
            order.products.forEach(p => {{
                const row = document.createElement("div");
                row.className = "modal-item-row";
                row.innerHTML = `
                    <div class="modal-item-detail">
                        <div class="modal-item-thumb">📦</div>
                        <div class="modal-item-text">
                            <span class="modal-item-name">${{p.name}}</span>
                            <span class="modal-item-meta">${{p.units}} × $${{p.price.toFixed(2)}}</span>
                        </div>
                    </div>
                    <span class="modal-item-price">$${{p.total.toFixed(2)}}</span>
                `;
                list.appendChild(row);
            }});

            document.getElementById("detailModal").classList.add("active");
        }}

        function closeModal() {{
            document.getElementById("detailModal").classList.remove("active");
        }}

        // Filter functions
        function setFilter(type, value, pillEl) {{
            currentFilterType = type;
            currentFilterVal = value;

            // Update active pill
            document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
            pillEl.classList.add("active");

            renderTable();
        }}

        function filterTable() {{
            const query = document.getElementById("searchInput").value.toLowerCase();
            const tbody = document.querySelector("#ordersTable tbody");
            const rows = tbody.querySelectorAll("tr");

            rows.forEach(row => {{
                const text = row.innerText.toLowerCase();
                if (text.includes(query)) {{
                    row.style.display = "";
                }} else {{
                    row.style.display = "none";
                }}
            }});
        }}

        // Initial setup
        window.onload = () => {{
            renderTable();
        }};
    </script>
</body>
</html>
"""

# Render dynamic layout in Streamlit
st.components.v1.html(html_code, height=920, scrolling=True)
