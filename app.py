import os
import json
import html as html_lib
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
import streamlit.components.v1 as components
from datetime import date

# The PDF tool is optional: if it is missing, the app still works.
try:
    from fpdf import FPDF
    PDF_OK = True
except Exception:
    PDF_OK = False

# ---------- Brand identity ----------
BRAND_NAME = "Finora"
BRAND_SLOGAN = "Smart Money, Smarter You"
BRAND_TAGLINE = "Where Money Meets Clarity"

st.set_page_config(
    page_title=f"{BRAND_NAME} | {BRAND_SLOGAN}",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Colors (navy and blue finance theme) ----------
ACCENT = "#0F4C81"   # royal blue
VIOLET = "#0F4C81"   # used for "actual" bars in the forecast chart
SKY = "#1C7ED6"
GREEN = "#1E8E5A"    # income / good
RED = "#C0392B"      # expense / bad
AMBER = "#E0A100"    # warning / forecast
PALETTE = ["#0A2540", "#0F4C81", "#1C7ED6", "#4DABF7",
           "#1E8E5A", "#E0A100", "#E67E22", "#7F8C9A"]

# ---------- Custom styling (CSS) ----------
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1250px;}
.hero {background: linear-gradient(120deg, #0A2540 0%, #0F4C81 60%, #1C7ED6 100%);
       background-size: 200% 200%; animation: heroflow 8s ease infinite;
       padding: 26px 32px; border-radius: 16px; margin-bottom: 18px;}
@keyframes heroflow {0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;}}
.hero-row {display: flex; align-items: center; gap: 16px;}
.logo {width: 62px; height: 62px; border-radius: 18px; color: #FFFFFF;
       background: linear-gradient(135deg, #4DABF7, #1E8E5A);
       font-size: 36px; font-weight: 800; display: flex;
       align-items: center; justify-content: center;
       box-shadow: 0 4px 14px rgba(0,0,0,0.30);}
.hero .title {color: #FFFFFF; font-size: 2.2rem; font-weight: 800;
              letter-spacing: 0.02em; line-height: 1.1;}
.hero .slogan {color: #D6E4F5; font-size: 1.05rem; margin-top: 4px;}
.hero .tagline {margin-top: 14px; display: inline-block; color: #FFFFFF;
                background: rgba(255,255,255,0.16); padding: 5px 16px;
                border-radius: 20px; font-size: 0.9rem; letter-spacing: 0.05em;}
.kpi {background: #FFFFFF; border-radius: 14px; padding: 18px 20px;
      border-left: 6px solid #0F4C81; box-shadow: 0 2px 8px rgba(10,37,64,0.10);
      transition: transform .2s ease, box-shadow .2s ease;
      animation: rise .6s ease both;}
.kpi:hover {transform: translateY(-4px);
            box-shadow: 0 8px 18px rgba(10,37,64,0.18);}
.kpi .label {color: #5B6B7F; font-size: 0.8rem; text-transform: uppercase;
             letter-spacing: 0.05em; font-weight: 600;}
.kpi .value {color: #0A2540; font-size: 1.8rem; font-weight: 800; margin-top: 4px;}
.kpi .sub {color: #5B6B7F; font-size: 0.8rem; margin-top: 2px;}
.bcard {background: #FFFFFF; border-radius: 14px; padding: 16px 20px;
        margin-bottom: 12px; box-shadow: 0 2px 8px rgba(10,37,64,0.08);
        transition: transform .2s ease;}
.bcard:hover {transform: translateX(4px);}
.bcard .brow {display: flex; justify-content: space-between;
              color: #0A2540; margin-bottom: 8px;}
.bar-bg {background: #E6ECF4; border-radius: 8px; height: 12px; overflow: hidden;}
.bar-fill {height: 12px; border-radius: 8px; animation: grow 1s ease-out;}
.bcard .bsub {font-size: 0.85rem; margin-top: 6px; font-weight: 600;}
@keyframes rise {from {opacity: 0; transform: translateY(14px);}
    to {opacity: 1; transform: translateY(0);}}
@keyframes grow {from {width: 0;}}
div[data-testid="stTabs"] button p {font-size: 1.05rem; font-weight: 600;}
.footer {text-align: center; color: #5B6B7F; font-size: 0.85rem;
         margin-top: 30px; padding: 14px; border-top: 1px solid #D6DEE9;}
</style>
""", unsafe_allow_html=True)


# ---------- Small helper functions ----------
def money(x):
    sign = "-" if x < 0 else ""
    return f"{sign}₹{abs(x):,.0f}"


def kpi(label, value, sub="", color=ACCENT):
    return (f'<div class="kpi" style="border-left-color:{color}">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="sub">{sub}</div></div>')


def stretch(func, *args, **kwargs):
    """Make a table or chart use the full width (old and new Streamlit)."""
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
st.sidebar.markdown(f"## 💠 {BRAND_NAME}")
st.sidebar.caption(f"**{BRAND_SLOGAN}**")
st.sidebar.caption(BRAND_TAGLINE)
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
st.sidebar.caption("Load demo data replaces everything in the app.")

# ---------- Prepare the data ----------
df = st.session_state.transactions.copy()
df["Amount"] = pd.to_numeric(df["Amount"])
df["Date"] = pd.to_datetime(df["Date"])
df["Month"] = df["Date"].dt.strftime("%Y-%m")

# ---------- Header banner ----------
st.markdown(
    f'<div class="hero"><div class="hero-row">'
    f'<div class="logo">F</div>'
    f'<div><div class="title">{BRAND_NAME}</div>'
    f'<div class="slogan">{BRAND_SLOGAN}</div></div></div>'
    f'<div class="tagline">✦ {BRAND_TAGLINE}</div></div>',
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
        k1.markdown(kpi("Available balance", money(balance), choice, ACCENT),
                    unsafe_allow_html=True)
        k2.markdown(kpi("Total income", money(income), "money in", GREEN),
                    unsafe_allow_html=True)
        k3.markdown(kpi("Total expenses", money(expense), "money out", RED),
                    unsafe_allow_html=True)
        k4.markdown(kpi("Savings rate", f"{rate:.0f}%", "of income saved",
                        AMBER), unsafe_allow_html=True)

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
            trend = df.groupby(["Month", "Type"],
                               as_index=False)["Amount"].sum()
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
                   .nlargest(5, "Amount")
                   [["Date", "Category", "Amount", "Description"]]
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
                    [st.session_state.transactions, new_row],
                    ignore_index=True,
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
                                   placeholder="category, description, type")
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
            return (f"ID {i} | {r['Date'].strftime('%d %b %Y')} | "
                    f"{r['Type']} | {r['Category']} | "
                    f"₹{r['Amount']:,.0f} | {r['Description']}")

        selected = st.selectbox("Choose a transaction", list(df.index),
                                format_func=make_label)
        row = df.loc[selected]

        with st.form(f"edit_form_{selected}"):
            e1, e2, e3 = st.columns(3)
            e_date = e1.date_input("Date", value=row["Date"].date())
            e_type = e2.selectbox("Type", TYPES,
                                  index=safe_index(TYPES, row["Type"]))
            e_category = e3.selectbox(
                "Category", CATEGORIES,
                index=safe_index(CATEGORIES, row["Category"]))
            e4, e5 = st.columns(2)
            e_amount = e4.number_input("Amount (₹)", min_value=0.0, step=10.0,
                                       value=float(row["Amount"]))
            e_desc = e5.text_input("Description",
                                   value=str(row["Description"]))
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
                st.session_state.transactions.drop(selected)
                .reset_index(drop=True)
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
                    f'<b>{cat}</b>'
                    f'<span>{money(amount_spent)} of {money(bud)}</span>'
                    f'</div><div class="bar-bg"><div class="bar-fill" '
                    f'style="width:{width:.0f}%;'
                    f'background:{color}">'
                    f'</div></div><div class="bsub" style="color:{color}">'
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
            pd.period_range(monthly.index.min(), monthly.index.max(),
                            freq="M"),
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
            st.write(f"💸 In **{latest}** you spent "
                     f"**{money(latest_total)}** in total.")
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
                            st.success(f"📉 You spent {abs(change):.0f}% less "
                                       f"on **{cat}** than last month. "
                                       f"Great job!")

            if month_income > 0:
                saved = month_income - latest_total
                s_rate = saved / month_income * 100
                if saved >= 0:
                    st.success(f"🏦 You saved {money(saved)} this month "
                               f"({s_rate:.0f}% of your income).")
                else:
                    st.error(f"⚠️ You spent {money(abs(saved))} more than "
                             f"you earned this month.")

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
                    label, s_color = "Good", ACCENT
                elif score >= 30:
                    label, s_color = "Needs attention", AMBER
                else:
                    label, s_color = "At risk", RED
                st.markdown(kpi("Score out of 100", f"{score}", label,
                                s_color), unsafe_allow_html=True)
                st.caption("Half of the score is your savings rate "
                           "(30% saved = full marks). The other half is "
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
                    color=alt.Color(
                        "Kind:N",
                        scale=alt.Scale(domain=["Actual", "Forecast"],
                                        range=[VIOLET, AMBER]),
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
                    st.warning(f"🔮 At this pace you may go over your "
                               f"**{cat}** budget next month (forecast "
                               f"{money(forecast[cat])} vs budget "
                               f"{money(budget)}).")

            st.caption("Forecast method: linear regression (a straight-line "
                       "trend through your past monthly spending).")

# =====================================================================
# TAB 5: BILL PRINTER
# =====================================================================
PRINTER_CSS = """
body{margin:0;padding:10px 0 24px;background:transparent;
     font-family:'Courier New',monospace;color:#0A2540;}
.stage{max-width:380px;margin:0 auto;text-align:center;}
.controls{display:flex;gap:14px;justify-content:center;align-items:center;
     margin-bottom:12px;font-family:Arial,sans-serif;font-size:13px;}
.btn{background:#0F4C81;color:#fff;border:none;padding:10px 20px;
     border-radius:8px;font-size:15px;font-weight:bold;cursor:pointer;}
.btn:disabled{background:#8FA3BA;cursor:wait;}
.printer{position:relative;z-index:3;
     background:linear-gradient(#1B3A5C,#0A2540);
     border-radius:18px 18px 10px 10px;padding:14px 18px 22px;
     box-shadow:0 8px 18px rgba(10,37,64,.35);}
.printer .top{display:flex;justify-content:space-between;align-items:center;
     color:#9DB4CF;font-family:Arial,sans-serif;font-size:12px;
     letter-spacing:.08em;}
.led{width:10px;height:10px;border-radius:50%;background:#3b4b5e;
     display:inline-block;margin-right:6px;}
.led.on{background:#2ECC71;box-shadow:0 0 8px #2ECC71;
     animation:blink .35s infinite alternate;}
@keyframes blink{from{opacity:.4}to{opacity:1}}
.screen{background:#0b1a2b;color:#5CE1A0;border-radius:6px;padding:6px 10px;
     margin:10px 0;font-size:13px;text-align:left;}
.slot{height:10px;background:#02060c;border-radius:5px;margin:0 6px;
     box-shadow:inset 0 3px 4px rgba(0,0,0,.8);}
.printer.working{animation:shake .12s infinite;}
@keyframes shake{0%{transform:translateY(0)}50%{transform:translateY(1px)}
     100%{transform:translateY(0)}}
.window{position:relative;z-index:1;overflow:hidden;margin:-6px 22px 0;
     padding:0 0 24px;}
.receipt{background:#fff;padding:18px 18px 8px;text-align:left;
     transform:translateY(-100%);position:relative;
     filter:drop-shadow(0 3px 4px rgba(10,37,64,.25));}
.receipt.go{animation:feed 5s steps(60,end) forwards;}
@keyframes feed{from{transform:translateY(-100%)}to{transform:translateY(0)}}
.edge{height:10px;margin:0 -18px;
     background:radial-gradient(circle at 5px 10px,transparent 5px,#fff 5.5px);
     background-size:10px 10px;}
.brand{font-size:20px;font-weight:bold;text-align:center;}
.mut{color:#6B7A8C;font-size:11px;text-align:center;margin-top:2px;}
.dash{border-top:2px dashed #B8C4D2;margin:10px 0;}
.ln{display:flex;justify-content:space-between;font-size:12px;padding:3px 0;}
.tot{display:flex;justify-content:space-between;font-size:18px;
     font-weight:bold;border-top:2px solid #0A2540;
     border-bottom:2px solid #0A2540;padding:7px 0;margin:8px 0;}
.stamp{display:block;width:fit-content;margin:12px auto 4px;
     transform:rotate(-8deg);border:3px solid;padding:2px 12px;
     font-size:20px;font-weight:bold;border-radius:6px;opacity:.65;}
.sec{font-size:12px;font-weight:bold;text-transform:uppercase;
     letter-spacing:.05em;margin:12px 0 2px;}
.barcode{height:36px;margin:12px 14px 4px;
     background:repeating-linear-gradient(90deg,#0A2540 0 2px,#fff 2px 4px,
     #0A2540 4px 5px,#fff 5px 8px,#0A2540 8px 11px,#fff 11px 13px);}
"""

PRINTER_JS = """
function brrr(sec){
  try{
    var ctx=new (window.AudioContext||window.webkitAudioContext)();
    var o=ctx.createOscillator(),g=ctx.createGain();
    var l=ctx.createOscillator(),lg=ctx.createGain();
    o.type='square';o.frequency.value=110;
    l.type='square';l.frequency.value=22;
    g.gain.value=0.04;lg.gain.value=0.04;
    l.connect(lg);lg.connect(g.gain);o.connect(g);g.connect(ctx.destination);
    o.start();l.start();
    o.stop(ctx.currentTime+sec);l.stop(ctx.currentTime+sec);
  }catch(e){}
}
var timer=null;
function startPrint(){
  var btn=document.getElementById('pbtn'),rec=document.getElementById('rec');
  var pr=document.getElementById('printer'),led=document.getElementById('led');
  var scr=document.getElementById('scr');
  btn.disabled=true;
  rec.classList.remove('go');
  rec.style.animationDuration=SECS+'s';
  void rec.offsetWidth;
  rec.classList.add('go');
  pr.classList.add('working');led.classList.add('on');
  scr.textContent='PRINTING...';
  if(document.getElementById('snd').checked){brrr(SECS);}
  clearTimeout(timer);
  timer=setTimeout(function(){
    pr.classList.remove('working');led.classList.remove('on');
    scr.textContent='DONE - TAKE YOUR BILL';
    btn.disabled=false;btn.textContent='🖨️ Print again';
  },SECS*1000);
}
"""


def printer_page(inner, secs=5):
    brand = html_lib.escape(BRAND_NAME).upper()
    return (
        "<html><head><meta charset='utf-8'><style>" + PRINTER_CSS
        + "</style></head><body><div class='stage'>"
        "<div class='controls'><button class='btn' id='pbtn' "
        "onclick='startPrint()'>🖨️ Print bill</button>"
        "<label><input type='checkbox' id='snd' checked> 🔊 Sound</label>"
        "</div>"
        "<div class='printer' id='printer'><div class='top'><span>"
        "<span class='led' id='led'></span>" + brand + " PRINTER</span>"
        "<span>MODEL FT-80</span></div>"
        "<div class='screen' id='scr'>READY</div><div class='slot'></div>"
        "</div>"
        "<div class='window'><div class='receipt' id='rec'>" + inner
        + "<div class='edge'></div></div></div></div>"
        "<script>var SECS=" + str(secs) + ";" + PRINTER_JS + "</script>"
        "</body></html>"
    )


def ln(label, value):
    return ('<div class="ln"><span>' + html_lib.escape(str(label))
            + '</span><span>' + html_lib.escape(str(value)) + '</span></div>')


def thermal_receipt(r, tx_id):
    is_income = r["Type"] == "Income"
    stamp = "RECEIVED" if is_income else "PAID"
    color = "#1E8E5A" if is_income else "#C0392B"
    no = (f"{BRAND_NAME[:2].upper()}-{r['Date'].strftime('%y%m%d')}-"
          f"{int(tx_id):04d}")
    desc = str(r["Description"]) or "-"
    return (
        '<div class="brand">💠 ' + html_lib.escape(BRAND_NAME) + '</div>'
        '<div class="mut">' + html_lib.escape(BRAND_SLOGAN) + '</div>'
        '<div class="mut">Personal Finance Receipt</div>'
        '<div class="dash"></div>'
        + ln("Receipt No.", no)
        + ln("Date", r["Date"].strftime("%d %b %Y"))
        + ln("Type", r["Type"])
        + ln("Category", r["Category"])
        + ln("Description", desc)
        + '<div class="tot"><span>AMOUNT</span><span>₹'
        + f'{r["Amount"]:,.2f}' + '</span></div>'
        + '<span class="stamp" style="color:' + color + ';border-color:'
        + color + '">' + stamp + '</span>'
        + '<div class="barcode"></div>'
        + '<div class="mut">' + html_lib.escape(BRAND_TAGLINE) + '</div>'
        + '<div class="mut">Printed on '
        + date.today().strftime("%d %b %Y") + '</div>'
    )


def thermal_statement(month_df, month_label, budgets):
    income = month_df[month_df["Type"] == "Income"]["Amount"].sum()
    expense = month_df[month_df["Type"] == "Expense"]["Amount"].sum()
    net = income - expense
    net_color = "#1E8E5A" if net >= 0 else "#C0392B"

    exp_by_cat = (month_df[month_df["Type"] == "Expense"]
                  .groupby("Category")["Amount"].sum()
                  .sort_values(ascending=False))
    cats = "".join(ln(c, f"₹{a:,.0f}") for c, a in exp_by_cat.items())

    buds = ""
    for cat, bud in budgets.items():
        spent = float(exp_by_cat.get(cat, 0))
        status = "OVER" if spent > bud else "OK"
        buds += ln(cat, f"₹{spent:,.0f} / ₹{bud:,.0f}  {status}")

    recent = month_df.sort_values("Date", ascending=False).head(8)
    txs = ""
    for _, t in recent.iterrows():
        sign = "+" if t["Type"] == "Income" else "-"
        txs += ln(t["Date"].strftime("%d %b") + " " + str(t["Category"]),
                  f"{sign}₹{t['Amount']:,.0f}")

    out = (
        '<div class="brand">💠 ' + html_lib.escape(BRAND_NAME) + '</div>'
        '<div class="mut">' + html_lib.escape(BRAND_SLOGAN) + '</div>'
        '<div class="mut">Monthly Statement · '
        + html_lib.escape(month_label)
        + '</div><div class="dash"></div>'
        + ln("Total income", f"₹{income:,.2f}")
        + ln("Total expenses", f"₹{expense:,.2f}")
        + '<div class="tot" style="color:' + net_color
        + '"><span>NET</span><span>₹' + f"{net:,.2f}" + '</span></div>'
        + '<div class="sec">Spending by category</div>' + cats
    )
    if buds:
        out += '<div class="sec">Budget check</div>' + buds
    out += (
        '<div class="sec">Latest transactions</div>' + txs
        + '<div class="barcode"></div>'
        '<div class="mut">Authorized statement · '
        + html_lib.escape(BRAND_NAME) + '</div>'
        '<div class="mut">' + html_lib.escape(BRAND_TAGLINE) + '</div>'
        '<div class="mut">Printed on ' + date.today().strftime("%d %b %Y")
        + '</div>'
    )
    return out


# ---------- PDF versions of the bills ----------
def clean(text):
    """The PDF font cannot show emojis or the rupee sign, so we clean text."""
    text = str(text).replace("₹", "Rs. ")
    return text.encode("latin-1", "replace").decode("latin-1")


def inr(x):
    return f"Rs. {x:,.2f}"


def receipt_pdf(r, tx_id):
    is_income = r["Type"] == "Income"
    stamp = "RECEIVED" if is_income else "PAID"
    color = (30, 142, 90) if is_income else (192, 57, 43)
    receipt_no = (f"{BRAND_NAME[:2].upper()}-"
                  f"{r['Date'].strftime('%y%m%d')}-{int(tx_id):04d}")

    pdf = FPDF(format="A5")
    pdf.set_auto_page_break(False)
    pdf.add_page()

    pdf.set_fill_color(10, 37, 64)
    pdf.rect(0, 0, 148, 34, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(0, 7)
    pdf.cell(148, 10, clean(BRAND_NAME), align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(0, 18)
    pdf.cell(148, 6, clean(BRAND_SLOGAN), align="C")
    pdf.set_xy(0, 25)
    pdf.cell(148, 6, "Personal Finance Receipt", align="C")

    pdf.set_text_color(10, 37, 64)
    y = 48
    details = [
        ("Receipt No.", receipt_no),
        ("Date", r["Date"].strftime("%d %b %Y")),
        ("Type", r["Type"]),
        ("Category", r["Category"]),
        ("Description", r["Description"] or "-"),
    ]
    for label, value in details:
        pdf.set_xy(14, y)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(40, 8, label)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(80, 8, clean(value)[:40], align="R")
        y += 10

    pdf.set_draw_color(150, 165, 185)
    pdf.set_line_width(0.3)
    pdf.set_dash_pattern(dash=2, gap=2)
    pdf.line(14, y + 2, 134, y + 2)
    pdf.set_dash_pattern()

    y += 8
    pdf.set_draw_color(10, 37, 64)
    pdf.set_line_width(0.6)
    pdf.line(14, y, 134, y)
    pdf.line(14, y + 14, 134, y + 14)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_xy(14, y + 2)
    pdf.cell(40, 10, "AMOUNT")
    pdf.cell(80, 10, inr(r["Amount"]), align="R")

    pdf.set_draw_color(*color)
    pdf.set_text_color(*color)
    pdf.set_line_width(1)
    with pdf.rotation(angle=15, x=100, y=y + 40):
        pdf.rect(72, y + 32, 56, 16)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_xy(72, y + 34)
        pdf.cell(56, 12, stamp, align="C")

    pdf.set_text_color(107, 122, 140)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(0, y + 66)
    pdf.cell(148, 6, clean(BRAND_TAGLINE), align="C")
    pdf.set_xy(0, y + 72)
    pdf.cell(148, 6, f"Generated on {date.today().strftime('%d %b %Y')}",
             align="C")
    return bytes(pdf.output())


def statement_pdf(month_df, month_label, budgets):
    income = month_df[month_df["Type"] == "Income"]["Amount"].sum()
    expense = month_df[month_df["Type"] == "Expense"]["Amount"].sum()
    net = income - expense

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()

    pdf.set_fill_color(10, 37, 64)
    pdf.rect(0, 0, 210, 32, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(0, 6)
    pdf.cell(210, 10, clean(BRAND_NAME), align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(0, 16)
    pdf.cell(210, 6, clean(BRAND_SLOGAN), align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(0, 23)
    pdf.cell(210, 6, f"Monthly Statement - {month_label}", align="C")

    pdf.set_text_color(10, 37, 64)
    pdf.set_y(40)

    def heading(text):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")

    def table_row(values, widths, aligns, bold=False, shade=False):
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        if shade:
            pdf.set_fill_color(230, 236, 244)
        for i, (v, w, a) in enumerate(zip(values, widths, aligns)):
            if i == len(values) - 1:
                pdf.cell(w, 7, clean(v)[:45], border="B", align=a,
                         fill=shade, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(w, 7, clean(v)[:45], border="B", align=a,
                         fill=shade)

    pdf.set_font("Helvetica", "", 12)
    pdf.cell(100, 8, "Total income")
    pdf.cell(90, 8, inr(income), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(100, 8, "Total expenses")
    pdf.cell(90, 8, inr(expense), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 14)
    if net >= 0:
        pdf.set_text_color(30, 142, 90)
    else:
        pdf.set_text_color(192, 57, 43)
    pdf.cell(100, 10, "NET BALANCE", border="TB")
    pdf.cell(90, 10, inr(net), border="TB", align="R",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(10, 37, 64)

    exp_by_cat = (month_df[month_df["Type"] == "Expense"]
                  .groupby("Category")["Amount"].sum()
                  .sort_values(ascending=False))
    heading("Spending by category")
    table_row(["Category", "Amount", "Share"], [100, 50, 40],
              ["L", "R", "R"], bold=True, shade=True)
    for cat, amt in exp_by_cat.items():
        share = amt / expense * 100 if expense > 0 else 0
        table_row([cat, inr(amt), f"{share:.0f}%"], [100, 50, 40],
                  ["L", "R", "R"])

    if budgets:
        heading("Budget check")
        table_row(["Category", "Spent", "Budget", "Status"],
                  [70, 40, 40, 40], ["L", "R", "R", "R"],
                  bold=True, shade=True)
        for cat, bud in budgets.items():
            spent = float(exp_by_cat.get(cat, 0))
            status = "OVER" if spent > bud else "OK"
            table_row([cat, inr(spent), inr(bud), status],
                      [70, 40, 40, 40], ["L", "R", "R", "R"])

    heading("All transactions")
    table_row(["Date", "Category", "Description", "Amount"],
              [22, 40, 78, 50], ["L", "L", "L", "R"],
              bold=True, shade=True)
    for _, t in month_df.sort_values("Date").iterrows():
        sign = "+" if t["Type"] == "Income" else "-"
        table_row([t["Date"].strftime("%d %b"), t["Category"],
                   t["Description"], f"{sign}Rs. {t['Amount']:,.0f}"],
                  [22, 40, 78, 50], ["L", "L", "L", "R"])

    pdf.ln(6)
    pdf.set_text_color(107, 122, 140)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6,
             f"Generated on {date.today().strftime('%d %b %Y')} - "
             f"{clean(BRAND_NAME)} authorized statement - "
             f"{clean(BRAND_TAGLINE)}")
    return bytes(pdf.output())


with tab_bill:
    st.subheader("🧾 Bill printer")
    st.caption("Pick a bill and press Print bill.")

    if df.empty:
        st.info("Add some transactions (or load the demo data) to print bills.")
    else:
        kind = st.radio("What do you want to print?",
                        ["Single transaction receipt", "Monthly statement"],
                        horizontal=True)

        pdf_bytes = None
        if kind == "Single transaction receipt":
            def bill_label(i):
                r = df.loc[i]
                return (f"ID {i} | {r['Date'].strftime('%d %b %Y')} | "
                        f"{r['Type']} | {r['Category']} | "
                        f"₹{r['Amount']:,.0f}")

            tx_id = st.selectbox("Choose a transaction", list(df.index),
                                 format_func=bill_label, key="bill_tx")
            page = printer_page(thermal_receipt(df.loc[tx_id], tx_id), secs=4)
            pdf_name = f"receipt_{tx_id}.pdf"
            height = 720
            if PDF_OK:
                try:
                    pdf_bytes = receipt_pdf(df.loc[tx_id], tx_id)
                except Exception:
                    pdf_bytes = None
        else:
            stmt_month = st.selectbox(
                "Month", sorted(df["Month"].unique(), reverse=True),
                key="stmt_month")
            month_data = df[df["Month"] == stmt_month]
            page = printer_page(thermal_statement(
                month_data, stmt_month, st.session_state.budgets), secs=7)
            pdf_name = f"statement_{stmt_month}.pdf"
            height = 1050
            if PDF_OK:
                try:
                    pdf_bytes = statement_pdf(
                        month_data, stmt_month, st.session_state.budgets)
                except Exception:
                    pdf_bytes = None

        components.html(page, height=height, scrolling=True)

        if pdf_bytes:
            st.download_button(
                "⬇️ Download PDF (for real paper printing)",
                data=pdf_bytes, file_name=pdf_name, mime="application/pdf",
            )
        else:
            st.caption("PDF download is unavailable. Add fpdf2 to "
                       "requirements.txt.")

# ---------- Footer ----------
st.markdown(
    f'<div class="footer"><b>{BRAND_NAME}</b> · {BRAND_SLOGAN} · '
    f'{BRAND_TAGLINE}</div>',
    unsafe_allow_html=True,
)
