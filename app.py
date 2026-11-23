import os
import json
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="SpendLens | Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Colors ----------
NAVY = "#0A2540"
BLUE = "#0F4C81"
GREEN = "#1E8E5A"
RED = "#C0392B"
AMBER = "#E0A100"
PALETTE = ["#0A2540", "#0F4C81", "#1C7ED6", "#4DABF7",
           "#1E8E5A", "#E0A100", "#E67E22", "#7F8C9A"]

# ---------- Custom styling (CSS) ----------
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1250px;}
.hero {background: linear-gradient(120deg, #0A2540 0%, #0F4C81 60%, #1C7ED6 100%);
       padding: 26px 32px; border-radius: 16px; margin-bottom: 18px;}
.hero .title {color: #FFFFFF; font-size: 2rem; font-weight: 800;}
.hero .subtitle {color: #D6E4F5; font-size: 1rem; margin-top: 4px;}
.kpi {background: #FFFFFF; border-radius: 14px; padding: 18px 20px;
      border-left: 6px solid #0F4C81; box-shadow: 0 2px 8px rgba(10,37,64,0.10);}
.kpi .label {color: #5B6B7F; font-size: 0.8rem; text-transform: uppercase;
             letter-spacing: 0.05em; font-weight: 600;}
.kpi .value {color: #0A2540; font-size: 1.8rem; font-weight: 800; margin-top: 4px;}
.kpi .sub {color: #5B6B7F; font-size: 0.8rem; margin-top: 2px;}
.bcard {background: #FFFFFF; border-radius: 14px; padding: 16px 20px;
        margin-bottom: 12px; box-shadow: 0 2px 8px rgba(10,37,64,0.08);}
.bcard .brow {display: flex; justify-content: space-between;
              color: #0A2540; margin-bottom: 8px;}
.bar-bg {background: #E6ECF4; border-radius: 8px; height: 12px; overflow: hidden;}
.bar-fill {height: 12px; border-radius: 8px;}
.bcard .bsub {font-size: 0.85rem; margin-top: 6px; font-weight: 600;}
div[data-testid="stTabs"] button p {font-size: 1.05rem; font-weight: 600;}
</style>
""", unsafe_allow_html=True)


# ---------- Small helper functions ----------
def money(x):
    sign = "-" if x < 0 else ""
    return f"{sign}₹{abs(x):,.0f}"


def kpi(label, value, sub="", color=BLUE):
    return (f'<div class="kpi" style="border-left-color:{color}">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="sub">{sub}</div></div>')


def stretch(func, *args, **kwargs):
    """Make a table or chart use the full width (works on old and new Streamlit)."""
    try:
        return func(*args, width="stretch", **kwargs)
    except Exception:
        return func(*args, use_container_width=True, **kwargs)


def safe_index(options, value):
    return options.index(value) if value in options else 0


# ---------- Files where we save data permanently ----------
DATA_FILE = "transactions.csv"
BUDGET_FILE = "budgets.json"
COLUMNS = ["Date", "Type", "Category", "Amount", "Description"]


def load_transactions():
    if os.path.exists(DATA_FILE):
        try:
            data = pd.read_csv(DATA_FILE)
            data["Description"] = data["Description"].fillna("")
            return data
        except Exception:
            pass
    return pd.DataFrame(columns=COLUMNS)


def save_transactions():
    st.session_state.transactions.to_csv(DATA_FILE, index=False)


def load_budgets():
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_budgets():
    with open(BUDGET_FILE, "w") as f:
        json.dump(st.session_state.budgets, f)


if "transactions" not in st.session_state:
    st.session_state.transactions = load_transactions()
if "budgets" not in st.session_state:
    st.session_state.budgets = load_budgets()

EXPENSE_CATEGORIES = ["Food", "Travel", "Shopping", "Bills",
                      "Entertainment", "Health", "Education", "Other"]
CATEGORIES = EXPENSE_CATEGORIES + ["Salary", "Freelance", "Other Income"]
TYPES = ["Expense", "Income"]


# ---------- Demo data ----------
def make_demo_data():
    today = date.today()
    template = [
        (1, "Income", "Salary", 30000, "Monthly allowance"),
        (2, "Expense", "Bills", 1200, "Mobile and internet recharge"),
        (3, "Expense", "Food", 900, "Groceries"),
        (5, "Expense", "Travel", 600, "Metro and bus pass"),
        (7, "Expense", "Food", 650, "Dinner with friends"),
        (9, "Expense", "Shopping", 1800, "Clothes"),
        (12, "Expense", "Entertainment", 700, "Movie and snacks"),
        (14, "Expense", "Food", 800, "Groceries"),
        (16, "Expense", "Education", 1500, "Books and course fee"),
        (18, "Expense", "Health", 500, "Pharmacy"),
        (20, "Expense", "Travel", 900, "Cab rides"),
        (22, "Expense", "Food", 1100, "Weekend outing"),
        (24, "Expense", "Bills", 2500, "Electricity bill"),
        (26, "Expense", "Entertainment", 600, "Streaming subscription"),
    ]
    multipliers = {2: 0.9, 1: 1.0, 0: 1.25}
    rows = []
    for months_back in [2, 1, 0]:
        month = today.month - months_back
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        for day, t_type, category, base, desc in template:
            if months_back == 0 and day > today.day:
                continue
            amount = base
            if t_type == "Expense":
                amount = round(base * multipliers[months_back] / 10) * 10
            rows.append({
                "Date": date(year, month, day),
                "Type": t_type,
                "Category": category,
                "Amount": float(amount),
                "Description": desc,
            })
    return pd.DataFrame(rows, columns=COLUMNS)


# ---------- Sidebar ----------
st.sidebar.markdown("## 💰 SpendLens")
st.sidebar.caption("Track income and expenses, set budgets, and get AI insights.")
st.sidebar.divider()
st.sidebar.subheader("Demo tools")

if st.sidebar.button("Load demo data"):
    st.session_state.transactions = make_demo_data()
    st.session_state.budgets = {
        "Food": 4000, "Travel": 2500, "Shopping": 3000,
        "Bills": 6000, "Entertainment": 2500,
    }
    save_transactions()
    save_budgets()
    st.rerun()

sure = st.sidebar.checkbox("I'm sure I want to clear everything")
if st.sidebar.button("Clear all data"):
    if sure:
        st.session_state.transactions = pd.DataFrame(columns=COLUMNS)
        st.session_state.budgets = {}
        save_transactions()
        save_budgets()
        st.rerun()
    else:
        st.sidebar.warning("Tick the box above first.")
st.sidebar.caption("Load demo data replaces everything currently in the app.")

# ---------- Prepare the data ----------
df = st.session_state.transactions.copy()
df["Amount"] = pd.to_numeric(df["Amount"])
df["Date"] = pd.to_datetime(df["Date"])
df["Month"] = df["Date"].dt.strftime("%Y-%m")

# ---------- Header banner ----------
st.markdown(
    '<div class="hero"><div class="title">💰 SpendLens</div>'
    '<div class="subtitle">Smart personal expense management: record, '
    'budget, visualize and forecast your money.</div></div>',
    unsafe_allow_html=True,
)

tab_dash, tab_tx, tab_budget, tab_ai, tab_bill = st.tabs(
    ["📊 Dashboard", "💳 Transactions", "🎯 Budgets", "🤖 AI Insights",
     "🧾 Bills"]
)

# =====================================================================
# TAB 1: DASHBOARD
# =====================================================================
with tab_dash:
    if df.empty:
        st.info("No data yet. Click **Load demo data** in the left sidebar, "
                "or add your first transaction in the Transactions tab.")
    else:
        months = sorted(df["Month"].unique(), reverse=True)
        choice = st.selectbox("Period", ["All time"] + months)
        view = df if choice == "All time" else df[df["Month"] == choice]

        income = view[view["Type"] == "Income"]["Amount"].sum()
        expense = view[view["Type"] == "Expense"]["Amount"].sum()
        balance = income - expense
        rate = (balance / income * 100) if income > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(kpi("Available balance", money(balance), choice, BLUE),
                    unsafe_allow_html=True)
        k2.markdown(kpi("Total income", money(income), "money in", GREEN),
                    unsafe_allow_html=True)
        k3.markdown(kpi("Total expenses", money(expense), "money out", RED),
                    unsafe_allow_html=True)
        k4.markdown(kpi("Savings rate", f"{rate:.0f}%", "of income saved", AMBER),
                    unsafe_allow_html=True)

        st.write("")
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Spending by category")
            exp = (view[view["Type"] == "Expense"]
                   .groupby("Category", as_index=False)["Amount"].sum())
            if exp.empty:
                st.info("No expenses in this period.")
            else:
                donut = alt.Chart(exp).mark_arc(innerRadius=70).encode(
                    theta=alt.Theta("Amount:Q"),
                    color=alt.Color("Category:N",
                                    scale=alt.Scale(range=PALETTE),
                                    legend=alt.Legend(title=None)),
                    tooltip=["Category:N",
                             alt.Tooltip("Amount:Q", format=",.0f")],
                ).properties(height=320)
                stretch(st.altair_chart, donut)

        with c2:
            st.subheader("Income vs expenses by month")
            trend = df.groupby(["Month", "Type"], as_index=False)["Amount"].sum()
            bars = alt.Chart(trend).mark_bar().encode(
                x=alt.X("Month:N", title=None),
                y=alt.Y("Amount:Q", title="Amount (₹)"),
                xOffset="Type:N",
                color=alt.Color("Type:N",
                                scale=alt.Scale(domain=["Income", "Expense"],
                                                range=[GREEN, RED]),
                                legend=alt.Legend(title=None)),
                tooltip=["Month:N", "Type:N",
                         alt.Tooltip("Amount:Q", format=",.0f")],
            ).properties(height=320)
            stretch(st.altair_chart, bars)

        r1, r2 = st.columns(2)
        with r1:
            st.subheader("Top 5 biggest expenses")
            top = (view[view["Type"] == "Expense"]
                   .nlargest(5, "Amount")[["Date", "Category", "Amount", "Description"]]
                   .copy())
            top["Date"] = top["Date"].dt.date
            stretch(st.dataframe, top, hide_index=True)
        with r2:
            st.subheader("Recent transactions")
            recent = (df.sort_values("Date", ascending=False).head(5)
                      [["Date", "Type", "Category", "Amount"]].copy())
            recent["Date"] = recent["Date"].dt.date
            stretch(st.dataframe, recent, hide_index=True)

# =====================================================================
# TAB 2: TRANSACTIONS
# =====================================================================
with tab_tx:
    left, right = st.columns([1, 2])

    with left:
        st.subheader("Add a transaction")
        with st.form("add_form", clear_on_submit=True):
            t_date = st.date_input("Date", value=date.today())
            t_type = st.selectbox("Type", TYPES)
            t_category = st.selectbox("Category", CATEGORIES)
            t_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
            t_desc = st.text_input("Description")
            submitted = st.form_submit_button("➕ Add transaction")

        if submitted:
            if t_amount <= 0:
                st.error("Please enter an amount greater than 0.")
            else:
                new_row = pd.DataFrame([{
                    "Date": t_date, "Type": t_type, "Category": t_category,
                    "Amount": t_amount, "Description": t_desc,
                }])
                st.session_state.transactions = pd.concat(
                    [st.session_state.transactions, new_row], ignore_index=True
                )
                save_transactions()
                st.toast("Transaction added!")
                st.rerun()

    with right:
        st.subheader("Transaction history")
        if df.empty:
            st.info("No transactions yet. Add your first one on the left!")
        else:
            f1, f2 = st.columns(2)
            search = f1.text_input("🔍 Search",
                                   placeholder="category, description, type...")
            type_filter = f2.selectbox("Type filter", ["All"] + TYPES)
            f3, f4 = st.columns(2)
            from_date = f3.date_input("From", value=df["Date"].min().date())
            to_date = f4.date_input("To", value=df["Date"].max().date())

            mask = ((df["Date"].dt.date >= from_date)
                    & (df["Date"].dt.date <= to_date))
            if type_filter != "All":
                mask = mask & (df["Type"] == type_filter)
            if search:
                text = (df["Category"].astype(str) + " "
                        + df["Description"].astype(str) + " "
                        + df["Type"].astype(str)).str.lower()
                mask = mask & text.str.contains(search.lower(), regex=False)

            shown = df[mask].sort_values("Date", ascending=False).copy()
            shown["Date"] = shown["Date"].dt.date
            table = shown[COLUMNS].copy()
            table.insert(0, "ID", shown.index)
            stretch(st.dataframe, table, hide_index=True)
            st.caption(f"Showing {len(shown)} of {len(df)} transactions")

            d1, d2 = st.columns(2)
            d1.download_button(
                "⬇️ Download shown rows as CSV",
                data=shown[COLUMNS].to_csv(index=False).encode("utf-8"),
                file_name="transactions_filtered.csv", mime="text/csv",
            )
            d2.download_button(
                "⬇️ Download all transactions as CSV",
                data=df[COLUMNS].to_csv(index=False).encode("utf-8"),
                file_name="transactions.csv", mime="text/csv",
            )

    st.divider()
    st.subheader("✏️ Edit or delete a transaction")
    if df.empty:
        st.info("No transactions to edit yet.")
    else:
        def make_label(i):
            r = df.loc[i]
            return (f"ID {i} | {r['Date'].strftime('%d %b %Y')} | {r['Type']} | "
                    f"{r['Category']} | ₹{r['Amount']:,.0f} | {r['Description']}")

        selected = st.selectbox("Choose a transaction", list(df.index),
                                format_func=make_label)
        row = df.loc[selected]

        with st.form(f"edit_form_{selected}"):
            e1, e2, e3 = st.columns(3)
            e_date = e1.date_input("Date", value=row["Date"].date())
            e_type = e2.selectbox("Type", TYPES,
                                  index=safe_index(TYPES, row["Type"]))
            e_category = e3.selectbox("Category", CATEGORIES,
                                      index=safe_index(CATEGORIES, row["Category"]))
            e4, e5 = st.columns(2)
            e_amount = e4.number_input("Amount (₹)", min_value=0.0, step=10.0,
                                       value=float(row["Amount"]))
            e_desc = e5.text_input("Description", value=str(row["Description"]))
            b1, b2 = st.columns(2)
            save_clicked = b1.form_submit_button("💾 Save changes")
            delete_clicked = b2.form_submit_button("🗑️ Delete transaction")

        if save_clicked:
            if e_amount <= 0:
                st.error("Please enter an amount greater than 0.")
            else:
                st.session_state.transactions.loc[selected, COLUMNS] = [
                    e_date, e_type, e_category, e_amount, e_desc
                ]
                save_transactions()
                st.toast("Transaction updated!")
                st.rerun()

        if delete_clicked:
            st.session_state.transactions = (
                st.session_state.transactions.drop(selected).reset_index(drop=True)
            )
            save_transactions()
            st.toast("Transaction deleted!")
            st.rerun()

# =====================================================================
# TAB 3: BUDGETS
# =====================================================================
with tab_budget:
    bl, br = st.columns([1, 2])

    with bl:
        st.subheader("Set a monthly budget")
        with st.form("budget_form"):
            b_category = st.selectbox("Category", EXPENSE_CATEGORIES)
            b_amount = st.number_input("Monthly budget (₹)", min_value=0.0,
                                       step=100.0)
            b_submitted = st.form_submit_button("💾 Save budget")

        if b_submitted:
            if b_amount <= 0:
                st.error("Please enter a budget greater than 0.")
            else:
                st.session_state.budgets[b_category] = b_amount
                save_budgets()
                st.toast(f"Budget saved for {b_category}!")
                st.rerun()

        if st.session_state.budgets:
            st.write("")
            remove_cat = st.selectbox("Remove a budget",
                                      list(st.session_state.budgets.keys()))
            if st.button("🗑️ Remove this budget"):
                st.session_state.budgets.pop(remove_cat, None)
                save_budgets()
                st.rerun()

    with br:
        st.subheader("Budget utilization")
        if df.empty:
            st.info("Add some transactions to see budget utilization.")
        elif not st.session_state.budgets:
            st.info("Set a monthly budget on the left to see utilization.")
        else:
            b_months = sorted(df["Month"].unique(), reverse=True)
            b_month = st.selectbox("Month", b_months, key="budget_month")
            spent = (df[(df["Type"] == "Expense") & (df["Month"] == b_month)]
                     .groupby("Category")["Amount"].sum())

            for cat, bud in st.session_state.budgets.items():
                amount_spent = float(spent.get(cat, 0))
                pct = amount_spent / bud if bud > 0 else 0
                if pct > 1:
                    color = RED
                    status = f"Over budget by {money(amount_spent - bud)}"
                elif pct >= 0.8:
                    color = AMBER
                    status = "Close to the limit"
                else:
                    color = GREEN
                    status = "On track"
                width = min(pct, 1.0) * 100
                st.markdown(
                    f'<div class="bcard"><div class="brow">'
                    f'<b>{cat}</b><span>{money(amount_spent)} of {money(bud)}</span>'
                    f'</div><div class="bar-bg"><div class="bar-fill" '
                    f'style="width:{width:.0f}%;background:{color}"></div></div>'
                    f'<div class="bsub" style="color:{color}">'
                    f'{status} · {pct * 100:.0f}% used</div></div>',
                    unsafe_allow_html=True,
                )

# =====================================================================
# TAB 4: AI INSIGHTS
# =====================================================================
with tab_ai:
    ai_df = df.copy()
    ai_df["Period"] = ai_df["Date"].dt.to_period("M")
    ai_expenses = ai_df[ai_df["Type"] == "Expense"]

    if ai_expenses.empty:
        st.info("Add some expenses (or load the demo data) to see insights.")
    else:
        monthly = ai_expenses.pivot_table(
            index="Period", columns="Category", values="Amount",
            aggfunc="sum", fill_value=0,
        ).sort_index()
        monthly = monthly.reindex(
            pd.period_range(monthly.index.min(), monthly.index.max(), freq="M"),
            fill_value=0,
        )

        latest = monthly.index[-1]
        latest_total = monthly.loc[latest].sum()
        month_income = ai_df[(ai_df["Type"] == "Income")
                             & (ai_df["Period"] == latest)]["Amount"].sum()

        ins_col, score_col = st.columns([2, 1])

        # ----- Smart insights -----
        with ins_col:
            st.subheader("Smart insights")
            st.write(f"💸 In **{latest}** you spent **{money(latest_total)}** in total.")
            top_cat = monthly.loc[latest].idxmax()
            top_share = monthly.loc[latest, top_cat] / latest_total * 100
            st.write(f"🏆 Your biggest spending category is **{top_cat}** "
                     f"({top_share:.0f}% of the month).")

            if len(monthly) >= 2:
                previous = monthly.index[-2]
                for cat in monthly.columns:
                    now_value = monthly.loc[latest, cat]
                    before_value = monthly.loc[previous, cat]
                    if before_value > 0 and now_value > 0:
                        change = (now_value - before_value) / before_value * 100
                        if change >= 15:
                            st.warning(f"📈 You spent {change:.0f}% more on "
                                       f"**{cat}** than last month.")
                        elif change <= -15:
                            st.success(f"📉 You spent {abs(change):.0f}% less on "
                                       f"**{cat}** than last month. Great job!")

            if month_income > 0:
                saved = month_income - latest_total
                s_rate = saved / month_income * 100
                if saved >= 0:
                    st.success(f"🏦 You saved {money(saved)} this month "
                               f"({s_rate:.0f}% of your income).")
                else:
                    st.error(f"⚠️ You spent {money(abs(saved))} more than you "
                             f"earned this month.")

        # ----- Financial health score -----
        with score_col:
            st.subheader("Financial health score")
            if month_income > 0:
                s_rate = (month_income - latest_total) / month_income * 100
                savings_part = min(max(s_rate, 0) / 30, 1) * 50
                if st.session_state.budgets:
                    ok = sum(
                        1 for c, b in st.session_state.budgets.items()
                        if float(monthly.loc[latest].get(c, 0)) <= b
                    )
                    budget_part = ok / len(st.session_state.budgets) * 50
                else:
                    budget_part = 25
                score = round(savings_part + budget_part)
                if score >= 75:
                    label, s_color = "Excellent", GREEN
                elif score >= 50:
                    label, s_color = "Good", BLUE
                elif score >= 30:
                    label, s_color = "Needs attention", AMBER
                else:
                    label, s_color = "At risk", RED
                st.markdown(kpi("Score out of 100", f"{score}", label, s_color),
                            unsafe_allow_html=True)
                st.caption("Half of the score comes from your savings rate "
                           "(30% saved = full marks). The other half comes from "
                           "how many budgets you stayed within.")
            else:
                st.info("Add some income this month to see your score.")

        st.divider()

        # ----- Forecast -----
        st.subheader("Next month forecast")
        if len(monthly) < 2:
            st.info("The forecast needs at least 2 months of data.")
        else:
            x = np.arange(len(monthly))
            next_x = len(monthly)
            forecast = {}
            for cat in monthly.columns:
                slope, intercept = np.polyfit(x, monthly[cat].values, 1)
                forecast[cat] = max(0.0, slope * next_x + intercept)

            total_forecast = sum(forecast.values())
            next_month = monthly.index[-1] + 1
            last_total = monthly.iloc[-1].sum()

            fc1, fc2 = st.columns([2, 1])
            with fc1:
                totals = monthly.sum(axis=1)
                labels = [str(m) for m in totals.index] + [f"{next_month}"]
                chart_df = pd.DataFrame({
                    "Month": labels,
                    "Spending": list(totals.values) + [total_forecast],
                    "Kind": ["Actual"] * len(totals) + ["Forecast"],
                })
                fchart = alt.Chart(chart_df).mark_bar().encode(
                    x=alt.X("Month:N", sort=None, title=None),
                    y=alt.Y("Spending:Q", title="Spending (₹)"),
                    color=alt.Color("Kind:N",
                                    scale=alt.Scale(domain=["Actual", "Forecast"],
                                                    range=[BLUE, AMBER]),
                                    legend=alt.Legend(title=None)),
                    tooltip=["Month:N", "Kind:N",
                             alt.Tooltip("Spending:Q", format=",.0f")],
                ).properties(height=300)
                stretch(st.altair_chart, fchart)
            with fc2:
                diff = total_forecast - last_total
                st.markdown(
                    kpi(f"Predicted spending for {next_month}",
                        money(total_forecast),
                        f"{money(diff)} vs {latest}", AMBER),
                    unsafe_allow_html=True,
                )
                forecast_table = pd.DataFrame({
                    "Category": list(forecast.keys()),
                    "Forecast (₹)": [round(v) for v in forecast.values()],
                }).sort_values("Forecast (₹)", ascending=False)
                st.write("")
                stretch(st.dataframe, forecast_table, hide_index=True)

            for cat, budget in st.session_state.budgets.items():
                if forecast.get(cat, 0) > budget:
                    st.warning(f"🔮 At this pace you may go over your **{cat}** "
                               f"budget next month (forecast "
                               f"{money(forecast[cat])} vs budget {money(budget)}).")

            st.caption("Forecast method: linear regression (a straight-line trend "
                       "through your past monthly spending).")

# =====================================================================
# TAB 5: BILLS AND STATEMENTS
# =====================================================================
import html as html_lib
import streamlit.components.v1 as components

BRAND_NAME = "FinTrack"  # change this name later when we do the branding

BILL_CSS = """
body {font-family: 'Courier New', monospace; background: #EEF2F7;
      margin: 0; padding: 16px; color: #0A2540;}
.noprint {text-align: center; margin-bottom: 14px;}
.noprint button {background: #0F4C81; color: white; border: none;
      padding: 10px 22px; border-radius: 8px; font-size: 15px;
      cursor: pointer; font-weight: bold;}
.paper {background: #FFFFFF; max-width: 560px; margin: 0 auto;
      padding: 28px 30px; border-radius: 6px; position: relative;
      box-shadow: 0 4px 18px rgba(10,37,64,0.18);
      border-top: 8px solid #0F4C81;}
.brand {font-size: 26px; font-weight: bold; text-align: center;}
.muted {color: #6B7A8C; font-size: 12px; text-align: center; margin-top: 2px;}
hr.dash {border: none; border-top: 2px dashed #B8C4D2; margin: 16px 0;}
.line {display: flex; justify-content: space-between; padding: 5px 0;
      font-size: 14px;}
.total {display: flex; justify-content: space-between; font-size: 22px;
      font-weight: bold; padding: 10px 0; border-top: 2px solid #0A2540;
      border-bottom: 2px solid #0A2540; margin-top: 10px;}
.stamp {position: absolute; right: 26px; top: 110px;
      transform: rotate(-14deg); border: 4px solid; padding: 4px 14px;
      font-size: 26px; font-weight: bold; border-radius: 8px; opacity: 0.55;}
table {width: 100%; border-collapse: collapse; font-size: 12px;
      margin-top: 8px;}
th {text-align: left; border-bottom: 2px solid #0A2540; padding: 5px 4px;}
td {padding: 5px 4px; border-bottom: 1px solid #E3E9F0;}
.right {text-align: right;}
h3 {font-size: 14px; margin: 18px 0 4px 0; text-transform: uppercase;
    letter-spacing: 0.05em;}
.sign {margin-top: 30px; display: flex; justify-content: space-between;
      font-size: 11px; color: #6B7A8C;}
@media print {
  .noprint {display: none;}
  body {background: white; padding: 0;}
  .paper {box-shadow: none; max-width: 100%;}
}
"""


def wrap_page(inner):
    return ("<html><head><meta charset='utf-8'><style>" + BILL_CSS
            + "</style></head><body><div class='noprint'>"
            "<button onclick='window.print()'>🖨️ Print / Save as PDF"
            "</button></div>" + inner + "</body></html>")


def receipt_html(r, tx_id):
    is_income = r["Type"] == "Income"
    stamp = "RECEIVED" if is_income else "PAID"
    color = "#1E8E5A" if is_income else "#C0392B"
    receipt_no = f"{BRAND_NAME[:2].upper()}-{r['Date'].strftime('%y%m%d')}-{int(tx_id):04d}"
    desc = html_lib.escape(str(r["Description"])) or "-"
    return (
        '<div class="paper">'
        f'<div class="brand">💰 {html_lib.escape(BRAND_NAME)}</div>'
        '<div class="muted">Personal Finance Receipt</div>'
        '<hr class="dash">'
        f'<div class="line"><span>Receipt No.</span><span>{receipt_no}</span></div>'
        f'<div class="line"><span>Date</span><span>{r["Date"].strftime("%d %b %Y")}</span></div>'
        f'<div class="line"><span>Type</span><span>{r["Type"]}</span></div>'
        f'<div class="line"><span>Category</span><span>{html_lib.escape(str(r["Category"]))}</span></div>'
        f'<div class="line"><span>Description</span><span>{desc}</span></div>'
        '<div style="height:10px"></div>'
        f'<div class="total"><span>AMOUNT</span><span>₹{r["Amount"]:,.2f}</span></div>'
        f'<div class="stamp" style="color:{color};border-color:{color}">{stamp}</div>'
        '<hr class="dash">'
        '<div class="muted">Thank you for tracking smart!</div>'
        f'<div class="muted">Generated on {date.today().strftime("%d %b %Y")}</div>'
        '</div>'
    )


def statement_html(month_df, month_label, budgets):
    income = month_df[month_df["Type"] == "Income"]["Amount"].sum()
    expense = month_df[month_df["Type"] == "Expense"]["Amount"].sum()
    net = income - expense

    rows = ""
    for _, t in month_df.sort_values("Date").iterrows():
        sign = "+" if t["Type"] == "Income" else "-"
        rows += (
            f'<tr><td>{t["Date"].strftime("%d %b")}</td>'
            f'<td>{html_lib.escape(str(t["Category"]))}</td>'
            f'<td>{html_lib.escape(str(t["Description"]))}</td>'
            f'<td class="right">{sign}₹{t["Amount"]:,.0f}</td></tr>'
        )

    exp_by_cat = (month_df[month_df["Type"] == "Expense"]
                  .groupby("Category")["Amount"].sum()
                  .sort_values(ascending=False))
    cat_rows = ""
    for cat, amt in exp_by_cat.items():
        share = amt / expense * 100 if expense > 0 else 0
        cat_rows += (f'<tr><td>{html_lib.escape(str(cat))}</td>'
                     f'<td class="right">₹{amt:,.0f}</td>'
                     f'<td class="right">{share:.0f}%</td></tr>')

    budget_rows = ""
    for cat, bud in budgets.items():
        spent = float(exp_by_cat.get(cat, 0))
        status = "OVER" if spent > bud else "OK"
        budget_rows += (f'<tr><td>{html_lib.escape(str(cat))}</td>'
                        f'<td class="right">₹{spent:,.0f}</td>'
                        f'<td class="right">₹{bud:,.0f}</td>'
                        f'<td class="right">{status}</td></tr>')
    budget_section = ""
    if budget_rows:
        budget_section = (
            '<h3>Budget check</h3><table><tr><th>Category</th>'
            '<th class="right">Spent</th><th class="right">Budget</th>'
            '<th class="right">Status</th></tr>' + budget_rows + '</table>')

    net_color = "#1E8E5A" if net >= 0 else "#C0392B"
    return (
        '<div class="paper" style="max-width:720px">'
        f'<div class="brand">💰 {html_lib.escape(BRAND_NAME)}</div>'
        f'<div class="muted">Monthly Statement · {month_label}</div>'
        '<hr class="dash">'
        f'<div class="line"><span>Total income</span><span>₹{income:,.2f}</span></div>'
        f'<div class="line"><span>Total expenses</span><span>₹{expense:,.2f}</span></div>'
        f'<div class="total" style="color:{net_color}"><span>NET BALANCE</span>'
        f'<span>₹{net:,.2f}</span></div>'
        '<h3>Spending by category</h3><table><tr><th>Category</th>'
        '<th class="right">Amount</th><th class="right">Share</th></tr>'
        + cat_rows + '</table>'
        + budget_section +
        '<h3>All transactions</h3><table><tr><th>Date</th><th>Category</th>'
        '<th>Description</th><th class="right">Amount</th></tr>'
        + rows + '</table>'
        '<div class="sign"><span>Generated on '
        f'{date.today().strftime("%d %b %Y")}</span>'
        f'<span>{html_lib.escape(BRAND_NAME)} · Authorized statement</span></div>'
        '</div>'
    )


with tab_bill:
    st.subheader("🧾 Bills and statements")
    st.caption("Create a printable receipt or a monthly statement, like a real "
               "bank or shop bill.")

    if df.empty:
        st.info("Add some transactions (or load the demo data) to create bills.")
    else:
        kind = st.radio("What do you want to create?",
                        ["Single transaction receipt", "Monthly statement"],
                        horizontal=True)

        if kind == "Single transaction receipt":
            def bill_label(i):
                r = df.loc[i]
                return (f"ID {i} | {r['Date'].strftime('%d %b %Y')} | "
                        f"{r['Type']} | {r['Category']} | ₹{r['Amount']:,.0f}")

            tx_id = st.selectbox("Choose a transaction", list(df.index),
                                 format_func=bill_label, key="bill_tx")
            page = wrap_page(receipt_html(df.loc[tx_id], tx_id))
            file_name = f"receipt_{tx_id}.html"
            height = 620
        else:
            stmt_month = st.selectbox(
                "Month", sorted(df["Month"].unique(), reverse=True),
                key="stmt_month")
            page = wrap_page(statement_html(
                df[df["Month"] == stmt_month], stmt_month,
                st.session_state.budgets))
            file_name = f"statement_{stmt_month}.html"
            height = 950

        st.download_button(
            "⬇️ Download this bill as a file",
            data=page.encode("utf-8"), file_name=file_name, mime="text/html",
        )
        st.caption("To print: click the 🖨️ button inside the bill below. If "
                   "nothing happens, download the file, open it, and press "
                   "Cmd + P (or Ctrl + P).")
        components.html(page, height=height, scrolling=True)
