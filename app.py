import streamlit as st
import numpy as np
import pandas as pd
import random

st.set_page_config(page_title="Shrimp Inventory Game", layout="wide")
st.title("🦐 Shrimp Inventory Management Game")
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
        "cat_food_price": 0.00
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
current_day = shared["days"][shared["current_day_index"]]
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
        shared["cost_fresh"] = st.sidebar.number_input("Cost per Fresh Shrimp", min_value=0.0, value=shared["cost_fresh"], step=0.10, format="%.2f")
        shared["cost_frozen"] = st.sidebar.number_input("Cost per Frozen Shrimp", min_value=0.0, value=shared["cost_frozen"], step=0.05, format="%.2f")
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

## ==============================================================================
## 5. 👥 TEAM INTERFACE
## ==============================================================================
st.header("👥 Team Dashboard")
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
            fresh_order = st.number_input("Order Fresh Shrimp:", min_value=0, step=50, value=800, key=f"fresh_{selected_team}")
        with col2:
            frozen_order = st.number_input("Order Frozen Shrimp:", min_value=0, step=50, value=100, key=f"frozen_{selected_team}")
            
        if st.button(f"📥 Submit Decisions for {selected_team}"):
            shared["current_round_orders"][selected_team] = {"fresh": fresh_order, "frozen": frozen_order}
            st.success(f"Order saved for {selected_team}!")
            st.rerun()
            
    st.subheader(f"📊 Personal Ledger History: {selected_team}")
    if team_data['history']:
        df_history = pd.DataFrame(team_data['history'])
        st.dataframe(df_history.style.format({"Cost": "${:,.2f}", "Revenue": "${:,.2f}", "Profit": "${:,.2f}"}))
else:
    st.warning("No game running. Please wait for the instructor to start the simulation.")
Wees voorzichtig met code.If you try running this version, let me know:Does the app load successfully now?Are there any runtime errors when you test the "Submit Decisions" or "Reset" buttons?
