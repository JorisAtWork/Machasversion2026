import streamlit as st
import numpy as np
import pandas as pd
import random

import base64

# ==============================================================================
# 🎨 BULLETPROOF CUSTOM BACKGROUND (BASE64 INJECTION)
# ==============================================================================
def set_custom_background(image_file_path):
    """Encodes a local image file into a base64 string and embeds it safely into CSS."""
    try:
        with open(image_file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            
        st.markdown(
            f"""
            <style>
            /* Targets the master background container layer */
            [data-testid="stAppViewContainer"] {{
                background-image: linear-gradient(rgba(255, 255, 255, 0.78), rgba(255, 255, 255, 0.78)), 
                                  url("data:image/png;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            
            /* Ensures top bar header navigation context remains clean and transparent */
            [data-testid="stHeader"] {{
                background: transparent !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        # Fallback safeguard warning if your path name doesn't match the folder deployment
        st.sidebar.warning(f"⚠️ Background asset not found at path target: '{image_file_path}'")

# Execute background injection (Update file name string to match your exact file extension)
set_custom_background("machasalaparmesana.png") 

st.set_page_config(page_title="Ordenamos Machas!", layout="wide")
st.title("🦐 Ordenar Machas (a la parmesana)!")
# ==============================================================================# 0. 🌐 SHARED GLOBAL DATA STATION (Connects all browsers together)# ==============================================================================
@st.cache_resource
def get_shared_state():
    """This function creates a single, global memory bank shared by all users."""
    return {
        "game_started": False,
        "game_over": False,
        "game_mode": "class",
        "game_seed": 42,
        "days": [],
        "team_names": [],
        "current_day_index": 0,
        "teams": {},
        "current_round_orders": {},
        "daily_demand": {},
        "demand_calculated": False,
        "demand_mean": 800,
        "demand_std": 100,
        "cost_fresh": 3.50,
        "cost_frozen": 4.00,
        "cost_holding": 1.00,
        "revenue_price": 7.00,
        "cat_food_price": 0.00,
        "max_teams_allowed": 8,
        "registration_open": False
    }
# Connect this user's tab to the master server stateshared = get_shared_state()
# Auto-refresh helper button for students to poll latest data
st.sidebar.markdown("### 🔄 Sync Network")
if st.sidebar.button("🔄 Refresh Screen / Check Admin Updates"):
    st.rerun()
# ==============================================================================# 1. DYNAMIC CONFIGURATION (Controlled by the Admin/First User)# ==============================================================================if not shared["game_started"]:
    st.subheader("⚙️ Game & Team Configuration (Instructor Panel)")
    st.info("📢 Instructors: Configure and launch the game here. Students, please wait and refresh your page once the instructor starts the game.")
    
    game_mode = st.radio(
        "Select Game Mode:",
        ["🏫 Live Class Mode (Synchronized turns)", "🏠 Practice Mode (Play at your own pace)"],
        help="Class Mode locks rounds until the admin advances everyone. Practice Mode allows instant turn progression."
    )
    temp_mode = "class" if "Live Class" in game_mode else "practice"
    
    use_custom_seed = st.checkbox("Set specific Game Seed? (Ensures exact same demand sequence)", value=False)
    if use_custom_seed:
        temp_seed = st.number_input("Enter integer Seed Code:", min_value=1, max_value=999999, value=42, step=1)
    else:
        temp_seed = random.randint(1000, 9999)
        st.write(f"Generated Random Seed: **{temp_seed}**")

    total_days = st.number_input("Number of game rounds (days):", min_value=1, max_value=30, value=5, step=1)
    
    default_teams = 3 if temp_mode == "class" else 1
    num_teams = st.number_input("Number of participating teams:", min_value=1, max_value=10, value=default_teams, step=1)
    
    st.markdown("#### 👥 Team Names")
    team_names = []
    cols = st.columns(int(num_teams))
    for i in range(int(num_teams)):
        with cols[i]:
            default_name = f"Team {i+1}"
            name = st.text_input(f"Name for {default_name}:", value=default_name, key=f"setup_team_{i}")
            team_names.append(name)
            
    if st.button("🚀 Start Game for Everyone"):
        shared["game_mode"] = temp_mode
        shared["game_seed"] = temp_seed
        shared["days"] = [f"Day {d+1}" for d in range(int(total_days))]
        shared["team_names"] = team_names
        shared["teams"] = {team: {"inventory": 0, "history": []} for team in team_names}
        shared["game_started"] = True
        st.rerun()
        
    st.stop()
# Cache individual loop states down to the master architecture
shared = get_shared_state()

# ==============================================================================
# 👨‍🏫 INSTRUCTOR CONTROL PANEL
# ==============================================================================
st.sidebar.title("👨‍🏫 Instructor Panel")

if not shared["game_started"]:
    st.sidebar.subheader("Setup Game Parameters")
    
    # 1. Beheer het aantal dagen
    num_days = st.sidebar.number_input("Number of Days to Simulate:", min_value=1, max_value=30, value=5, step=1)
    
    # 2. Beheer het aantal teams
    max_teams = st.sidebar.number_input("Maximum Number of Teams Allowed:", min_value=1, max_value=20, value=3, step=1)
    
    # Knop om de registratie te openen (het spel start pas als de docent écht op 'Start' drukt)
    if st.sidebar.button("🚀 Lock Settings & Open Registration"):
        # Genereer de dagen lijst op basis van de invoer
        shared["days"] = [f"Day {i}" for i in range(1, num_days + 1)]
        shared["current_day_index"] = 0
        shared["max_teams_allowed"] = max_teams  # Sla dit op in de shared state
        shared["registration_open"] = True
        st.toast("Registration is now open for students!")
        st.rerun()

# Als de registratie open is óf het spel al loopt, tonen we de status
if "registration_open" in shared and shared["registration_open"] and not shared["game_started"]:
    st.sidebar.warning("Waiting for teams to register...")
    st.sidebar.write(f"Registered: {len(shared['team_names'])} / {shared['max_teams_allowed']} teams")
    
    # De definitieve startknop voor de docent als de teams compleet zijn
    if len(shared["team_names"]) > 0:
        if st.sidebar.button("🎮 Start Simulation Now"):
            shared["game_started"] = True
            shared["registration_open"] = False
            st.toast("The simulation has officially started!")
            st.rerun()

if shared["game_started"]:
    st.sidebar.success("🎮 Game is currently running!")
    st.sidebar.write(f"📅 Current: {shared['days'][shared['current_day_index']]}")

if shared["game_started"] and shared["days"]:
    current_day = shared["days"][shared["current_day_index"]]
else:
    current_day = None
teams_submitted = list(shared["current_round_orders"].keys())
if shared["game_mode"] == "class":
    all_teams_submitted = set(shared["team_names"]) == set(teams_submitted)
else:
    all_teams_submitted = len(teams_submitted) > 0
# ==============================================================================# 3. 👑 ADMIN PANEL & PARAMETERS # ==============================================================================
st.sidebar.header("👑 Admin Control Panel")
st.sidebar.markdown(f"**Mode:** {shared['game_mode'].upper()} | **Seed:** `{shared['game_seed']}`")
if shared["game_over"]:
    st.sidebar.error("🏁 The game has ended.")
else:
    st.sidebar.subheader(f"Current Phase: {current_day}")

    with st.sidebar.expander("⚙️ Configure Game Parameters", expanded=True):
        st.markdown("### 📊 Demand Parameters")
        shared["demand_mean"] = st.sidebar.number_input("Demand Mean (μ)", min_value=1, value=shared["demand_mean"], step=10)
        shared["demand_std"] = st.sidebar.number_input("Demand Std Dev (σ)", min_value=0, value=shared["demand_std"], step=5)
        
        st.markdown("### 💰 Costs & Pricing")
        shared["cost_fresh"] = st.sidebar.number_input("Cost of Machas per dozen", min_value=0.0, value=shared["cost_fresh"], step=0.10, format="%.2f")
        shared["cost_frozen"] = st.sidebar.number_input("Cost of Frozen Machas per dozen", min_value=0.0, value=shared["cost_frozen"], step=0.05, format="%.2f")
        shared["cost_holding"] = st.sidebar.number_input("Holding Cost (Frozen)", min_value=0.0, value=shared["cost_holding"], step=0.10, format="%.2f")
        shared["revenue_price"] = st.sidebar.number_input("Selling Price to Customers", min_value=0.0, value=shared["revenue_price"], step=0.25, format="%.2f")
        shared["cat_food_price"] = st.sidebar.number_input("Cat Food Price", min_value=0.0, value=shared["cat_food_price"], step=0.10, format="%.2f")

    st.sidebar.markdown("---")

    if not all_teams_submitted:
        if shared["game_mode"] == "class":
            st.sidebar.info("⏳ Waiting for all submissions...")
            missing_teams = set(shared["team_names"]) - set(teams_submitted)
            st.sidebar.warning(f"Pending: {', '.join(missing_teams)}")
    else:
        if not shared["demand_calculated"]:
            button_label = "🎲 Generate Demand & Calculate Results" if shared["game_mode"] == "class" else "⚡ Process My Order"
            
            if st.sidebar.button(button_label) or shared["game_mode"] == "practice":
                rng = random.Random(shared["game_seed"])
                demand = 0
                for _ in range(shared["current_day_index"] + 1):
                    demand = max(0, int(rng.normalvariate(shared["demand_mean"], shared["demand_std"])))
                
                shared["daily_demand"][current_day] = demand
                
                for team in teams_submitted:
                    team_data = shared["teams"][team]
                    orders = shared["current_round_orders"][team]
                    
                    fresh_order = orders["fresh"]
                    frozen_order = orders["frozen"]
                    starting_inv = team_data['inventory']
                    
                    total_available = starting_inv + fresh_order + frozen_order
                    actual_sales = min(total_available, demand)
                    
                    if actual_sales <= (starting_inv + fresh_order):
                        leftover_frozen = frozen_order
                        unsold_fresh = (starting_inv + fresh_order) - actual_sales
                    else:
                        leftover_frozen = total_available - actual_sales
                        unsold_fresh = 0
                        
                    cost_inv = starting_inv * shared["cost_holding"]
                    cost_purchase_fresh = fresh_order * shared["cost_fresh"]
                    cost_purchase_frozen = frozen_order * shared["cost_frozen"]
                    total_cost = cost_inv + cost_purchase_fresh + cost_purchase_frozen
                    
                    revenue = (actual_sales * shared["revenue_price"]) + (unsold_fresh * shared["cat_food_price"])
                    profit = revenue - total_cost
                    
                    record = {
                        "Day": current_day, "Starting Inv": starting_inv, "Fresh Ordered": fresh_order,
                        "Frozen Ordered": frozen_order, "Demand": demand, "Sales": actual_sales,
                        "Unsold Fresh": unsold_fresh, "Cost": total_cost, "Revenue": revenue, "Profit": profit,
                        "Ending Inv (Frozen)": leftover_frozen
                    }
                    team_data['history'].append(record)
                    team_data['inventory'] = leftover_frozen
                
                shared["demand_calculated"] = True
                st.rerun()

    if shared["demand_calculated"]:
        st.sidebar.success(f"Today's Demand: **{shared['daily_demand'][current_day]} units**")
        
        if shared["game_mode"] == "practice" or st.sidebar.button("⏭️ Advance to Next Day"):
            if shared["current_day_index"] < len(shared["days"]) - 1:
                shared["current_day_index"] += 1
                shared["current_round_orders"] = {} 
                shared["demand_calculated"] = False 
                st.rerun()
            else:
                shared["game_over"] = True
                st.rerun()
        st.sidebar.markdown("---")
        if st.sidebar.button("🚨 Reset/End Game Early"):
            shared["game_started"] = False
            shared["game_over"] = False
            shared["current_round_orders"] = {}
            shared["teams"] = {}
            st.rerun()

st.sidebar.markdown("---") # Visuele scheidingslijn

if st.sidebar.button("🔄 Reset Entire Session", help="Wipes all teams, history, and parameter settings to start completely fresh."):
    # 1. Herstel alle basisvariabelen naar de beginstatus
    shared["game_started"] = False
    shared["game_over"] = False
    shared["registration_open"] = False
    shared["days"] = []
    shared["team_names"] = []
    shared["current_day_index"] = 0
    shared["teams"] = {}
    shared["current_round_orders"] = {}
    shared["daily_demand"] = {}
    shared["demand_calculated"] = False
    
    # 2. Optioneel: Herstel ook de standaard marktinstellingen (als je die hebt aangepast)
    shared["demand_mean"] = 800
    shared["demand_std"] = 100
    
    # Herlaad de app direct zodat iedereen weer het startskerm ziet
    st.toast("Session reset successfully! Ready for a new game.")
    st.rerun()


# ==============================================================================
# 4. 🏆 LEADERBOARD 
# ==============================================================================
if shared["game_over"]:
    st.header("🏁 FINAL RESULTS: Game Over!")
else:
    st.header("🏆 Live Standing Leaderboard")

leaderboard_data = []
all_games_history = []

for team_name, data in shared["teams"].items():
    total_profit = sum(round_data["Profit"] for round_data in data["history"])
    total_revenue = sum(round_data["Revenue"] for round_data in data["history"])
    total_cost = sum(round_data["Cost"] for round_data in data["history"])
    rounds_played = len(data["history"])
    
    leaderboard_data.append({
        "Team": team_name, 
        "Total Profit": total_profit, 
        "Total Revenue": total_revenue,
        "Total Cost": total_cost, 
        "Current Frozen Stock": data["inventory"], 
        "Rounds Completed": rounds_played
    })
    
    for record in data["history"]:
        export_record = {"Team": team_name}
        export_record.update(record)
        all_games_history.append(export_record)

df_leaderboard = pd.DataFrame(leaderboard_data)

if not df_leaderboard.empty:
    df_leaderboard = df_leaderboard.sort_values(by="Total Profit", ascending=False).reset_index(drop=True)
    df_leaderboard.index = df_leaderboard.index + 1
    df_leaderboard.index.name = "Rank"
    st.dataframe(df_leaderboard.style.format({
        "Total Profit": "${:,.2f}", 
        "Total Revenue": "${:,.2f}", 
        "Total Cost": "${:,.2f}"
    }))
else:
    st.info("Waiting for the instructor to launch the session and calculate Day 1.")

## --- EXPORT SECTION AT GAME OVER ---
if shared["game_over"]:
    st.balloons()
    st.success("Congratulations to the winner! Download all session data below for analysis.")
    if all_games_history:
        df_export = pd.DataFrame(all_games_history)
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download All Game Metrics (CSV)",
            data=csv_data,
            file_name=f"shrimp_game_seed_{shared['game_seed']}.csv",
            mime="text/csv"
        )
        st.markdown("### 📊 Exported Data Preview")
        st.dataframe(df_export)
        st.stop()

st.markdown("---")

# ==============================================================================
# 👥 5. TEAM INTERFACE SECTION
# ==============================================================================

if not shared["game_over"]:
    st.header("👥 Team Dashboard")
    
    # 🔄 LIVE MULTIPLAYER SYNC PROMPT
    sync_col1, sync_col2 = st.columns([3, 1])
    with sync_col1:
        st.info("💡 **Multiplayer Sync:** Has the instructor advanced the round? Click refresh to pull the latest market standings and inventory balances.")
    with sync_col2:
        if st.button("🔄 Sync & Refresh Data", use_container_width=True, type="primary"):
            st.rerun()
            
    st.markdown("---") # Neat visual separator before team controls


# SCENARIO A: Het spel is nog niet gestart, maar de registratie is OPEN
if "registration_open" in shared and shared["registration_open"] and not shared["game_started"]:
    st.subheader("📝 Register Your Team")
    
    if len(shared["team_names"]) >= shared["max_teams_allowed"]:
        st.error("Registration is full! Please wait for the instructor to start the game.")
    else:
        new_team_name = st.text_input("Enter a unique name for your team:", placeholder="e.g., Las Machillas").strip()
        
        if st.button("Submit Team Registration"):
            if not new_team_name:
                st.warning("Please enter a valid name.")
            elif new_team_name in shared["team_names"]:
                st.error("This team name is already taken! Choose another one.")
            else:
                # Voeg het team toe aan de gedeelde systemen
                shared["team_names"].append(new_team_name)
                shared["teams"][new_team_name] = {
                    "inventory": 0,  # Beginkapitaal aan diepvries shrimp (of pas aan naar wens)
                    "history": []
                }
                st.success(f"🎉 Team '{new_team_name}' successfully registered!")
                st.rerun()

# SCENARIO B: Het spel is bezig (Jouw bestaande code, nu veilig achter de check)
elif shared["game_started"]:
    if shared["team_names"]:
        selected_team = st.selectbox("Select your team to submit an order:", list(shared["teams"].keys()))
        team_data = shared["teams"][selected_team]
        
        st.metric(label="Your Current Frozen Inventory Balance", value=f"{team_data['inventory']} units")
        
        has_ordered_today = selected_team in shared["current_round_orders"]
        if has_ordered_today:
            st.success(f"✅ {selected_team} has successfully submitted! Please wait for the Instructor to process the day.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                fresh_order = st.number_input("Order Fresh Machas:", min_value=0, step=50, value=800, key=f"fresh_{selected_team}")
            with col2:
                frozen_order = st.number_input("Order Frozen Machas:", min_value=0, step=50, value=100, key=f"frozen_{selected_team}")
                
            if st.button(f"📥 Submit Decisions for {selected_team}"):
                shared["current_round_orders"][selected_team] = {"fresh": fresh_order, "frozen": frozen_order}
                st.success(f"Order saved for {selected_team}!")
                st.rerun()
                
        st.subheader(f"📊 Personal Ledger History: {selected_team}")
        if team_data['history']:
            df_history = pd.DataFrame(team_data['history'])
            st.dataframe(df_history.style.format({"Cost": "${:,.2f}", "Revenue": "${:,.2f}", "Profit": "${:,.2f}"}))

# SCENARIO C: Er is nog niks gestart en registratie zit dicht
else:
    st.warning("No game running. Please wait for the instructor to open registration.")

