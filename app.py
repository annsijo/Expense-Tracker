import os
import json
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Expense Tracker", page_icon="💰")
st.title("💰 Personal Expense Tracker")

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


# This is where we keep all data while the app is open
if "transactions" not in st.session_state:
    st.session_state.transactions = load_transactions()
if "budgets" not in st.session_state:
    st.session_state.budgets = load_budgets()

EXPENSE_CATEGORIES = ["Food", "Travel", "Shopping", "Bills",
                      "Entertainment", "Health", "Education", "Other"]
CATEGORIES = EXPENSE_CATEGORIES + ["Salary"]
TYPES = ["Expense", "Income"]

# ---------- Demo data (left sidebar) ----------
def make_demo_data():
    today = date.today()
    # (day, type, category, base amount, description)
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
    # spending grows a little each month, so the charts look interesting
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
                continue  # no transactions in the future
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


st.sidebar.header("Demo tools")
if st.sidebar.button("Load demo data"):
    st.session_state.transactions = make_demo_data()
    st.session_state.budgets = {
        "Food": 4000, "Travel": 2500, "Shopping": 3000,
        "Bills": 6000, "Entertainment": 2500,
    }
    save_transactions()
    save_budgets()
    st.rerun()

if st.sidebar.button("Clear all data"):
    st.session_state.transactions = pd.DataFrame(columns=COLUMNS)
    st.session_state.budgets = {}
    save_transactions()
    save_budgets()
    st.rerun()

st.sidebar.caption("Load demo data replaces everything currently in the app.")

# ---------- Add a transaction ----------
st.header("Add a transaction")
with st.form("add_form", clear_on_submit=True):
    t_date = st.date_input("Date", value=date.today())
    t_type = st.selectbox("Type", TYPES)
    t_category = st.selectbox("Category", CATEGORIES)
    t_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    t_desc = st.text_input("Description")
    submitted = st.form_submit_button("Add transaction")

if submitted:
    if t_amount <= 0:
        st.error("Please enter an amount greater than 0.")
    else:
        new_row = pd.DataFrame([{
            "Date": t_date,
            "Type": t_type,
            "Category": t_category,
            "Amount": t_amount,
            "Description": t_desc,
        }])
        st.session_state.transactions = pd.concat(
            [st.session_state.transactions, new_row], ignore_index=True
        )
        save_transactions()
        st.success("Transaction added!")

df = st.session_state.transactions.copy()
df["Amount"] = pd.to_numeric(df["Amount"])

# ---------- Summary ----------
st.header("Summary")
total_income = df[df["Type"] == "Income"]["Amount"].sum()
total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
balance = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"₹{total_income:,.2f}")
col2.metric("Total Expenses", f"₹{total_expense:,.2f}")
col3.metric("Balance", f"₹{balance:,.2f}")

# ---------- History with search and date filters ----------
st.header("Transaction history")
if df.empty:
    st.info("No transactions yet. Add your first one above!")
else:
    hist = df.copy()
    hist["Date"] = pd.to_datetime(hist["Date"])

    f1, f2, f3 = st.columns(3)
    search = f1.text_input("Search (category, description, type)")
    from_date = f2.date_input("From", value=hist["Date"].min().date())
    to_date = f3.date_input("To", value=hist["Date"].max().date())

    mask = (hist["Date"].dt.date >= from_date) & (hist["Date"].dt.date <= to_date)
    if search:
        text = (
            hist["Category"].astype(str) + " "
            + hist["Description"].astype(str) + " "
            + hist["Type"].astype(str)
        ).str.lower()
        mask = mask & text.str.contains(search.lower(), regex=False)

    shown = hist[mask].copy()
    shown["Date"] = shown["Date"].dt.date
    st.dataframe(shown, use_container_width=True)
    st.caption(f"Showing {len(shown)} of {len(hist)} transactions")

    # ---------- CSV export ----------
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download all transactions as CSV",
        data=csv_data,
        file_name="transactions.csv",
        mime="text/csv",
    )

# ---------- Edit or delete ----------
st.header("Edit or delete a transaction")
if df.empty:
    st.info("No transactions to edit yet.")
else:
    def make_label(i):
        r = df.loc[i]
        return (f"#{i} | {r['Date']} | {r['Type']} | {r['Category']} | "
                f"₹{r['Amount']:,.2f} | {r['Description']}")

    selected = st.selectbox("Choose a transaction", list(df.index),
                            format_func=make_label)
    row = df.loc[selected]

    with st.form(f"edit_form_{selected}"):
        e_date = st.date_input("Date", value=pd.to_datetime(row["Date"]).date())
        e_type = st.selectbox("Type", TYPES, index=TYPES.index(row["Type"]))
        e_category = st.selectbox("Category", CATEGORIES,
                                  index=CATEGORIES.index(row["Category"]))
        e_amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0,
                                   value=float(row["Amount"]))
        e_desc = st.text_input("Description", value=str(row["Description"]))
        b1, b2 = st.columns(2)
        save_clicked = b1.form_submit_button("Save changes")
        delete_clicked = b2.form_submit_button("Delete transaction")

    if save_clicked:
        if e_amount <= 0:
            st.error("Please enter an amount greater than 0.")
        else:
            st.session_state.transactions.loc[
                selected, COLUMNS
            ] = [e_date, e_type, e_category, e_amount, e_desc]
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

# ---------- Set monthly budgets ----------
st.header("Monthly budgets")
with st.form("budget_form"):
    b_category = st.selectbox("Category", EXPENSE_CATEGORIES)
    b_amount = st.number_input("Monthly budget (₹)", min_value=0.0, step=100.0)
    b_submitted = st.form_submit_button("Save budget")

if b_submitted:
    if b_amount <= 0:
        st.error("Please enter a budget greater than 0.")
    else:
        st.session_state.budgets[b_category] = b_amount
        save_budgets()
        st.success(f"Budget saved for {b_category}!")

if st.session_state.budgets:
    budget_table = pd.DataFrame(
        list(st.session_state.budgets.items()),
        columns=["Category", "Monthly Budget (₹)"],
    )
    st.table(budget_table)

# ---------- Charts and budget utilization ----------
st.header("Charts and budget utilization")
if df.empty:
    st.info("Add some transactions to see charts.")
else:
    chart_df = df.copy()
    chart_df["Date"] = pd.to_datetime(chart_df["Date"])
    chart_df["Month"] = chart_df["Date"].dt.strftime("%Y-%m")

    months = sorted(chart_df["Month"].unique(), reverse=True)
    selected_month = st.selectbox("Select month", months)

    month_expenses = chart_df[
        (chart_df["Type"] == "Expense") & (chart_df["Month"] == selected_month)
    ]
    spent = month_expenses.groupby("Category")["Amount"].sum()

    st.subheader("Spending by category")
    if spent.empty:
        st.info("No expenses in this month.")
    else:
        st.bar_chart(spent)

    st.subheader("Budget utilization")
    if not st.session_state.budgets:
        st.info("Set a monthly budget above to see utilization.")
    else:
        for category, budget in st.session_state.budgets.items():
            amount_spent = float(spent.get(category, 0))
            percent = amount_spent / budget
            st.write(
                f"**{category}**: ₹{amount_spent:,.2f} of ₹{budget:,.2f} "
                f"({percent * 100:.0f}%)"
            )
            st.progress(min(percent, 1.0))
            if percent > 1:
                st.error(f"Over budget on {category}!")
            elif percent >= 0.8:
                st.warning(f"Close to the limit on {category}.")

# ---------- AI insights and forecast ----------
import numpy as np

st.header("🤖 Smart insights and forecast")

ai_df = df.copy()
ai_df["Date"] = pd.to_datetime(ai_df["Date"])
ai_df["Month"] = ai_df["Date"].dt.to_period("M")
ai_expenses = ai_df[ai_df["Type"] == "Expense"]

if ai_expenses.empty:
    st.info("Add some expenses (or load the demo data) to see insights.")
else:
    # Table of spending: one row per month, one column per category
    monthly = ai_expenses.pivot_table(
        index="Month", columns="Category", values="Amount",
        aggfunc="sum", fill_value=0,
    ).sort_index()
    monthly = monthly.reindex(
        pd.period_range(monthly.index.min(), monthly.index.max(), freq="M"),
        fill_value=0,
    )

    # ----- Smart insights -----
    st.subheader("Smart insights")
    latest = monthly.index[-1]
    latest_total = monthly.loc[latest].sum()
    st.write(f"💸 In **{latest}** you spent **₹{latest_total:,.0f}** in total.")

    top_cat = monthly.loc[latest].idxmax()
    top_share = monthly.loc[latest, top_cat] / latest_total * 100
    st.write(
        f"🏆 Your biggest spending category is **{top_cat}** "
        f"({top_share:.0f}% of the month)."
    )

    if len(monthly) >= 2:
        previous = monthly.index[-2]
        for cat in monthly.columns:
            now_value = monthly.loc[latest, cat]
            before_value = monthly.loc[previous, cat]
            if before_value > 0 and now_value > 0:
                change = (now_value - before_value) / before_value * 100
                if change >= 15:
                    st.warning(
                        f"📈 You spent {change:.0f}% more on **{cat}** "
                        f"than last month."
                    )
                elif change <= -15:
                    st.success(
                        f"📉 You spent {abs(change):.0f}% less on **{cat}** "
                        f"than last month. Great job!"
                    )

    month_income = ai_df[
        (ai_df["Type"] == "Income") & (ai_df["Month"] == latest)
    ]["Amount"].sum()
    if month_income > 0:
        saved = month_income - latest_total
        rate = saved / month_income * 100
        if saved >= 0:
            st.success(
                f"🏦 You saved ₹{saved:,.0f} this month "
                f"({rate:.0f}% of your income)."
            )
        else:
            st.error(
                f"⚠️ You spent ₹{abs(saved):,.0f} more than you earned "
                f"this month."
            )

    # ----- Forecast -----
    st.subheader("Next month forecast")
    if len(monthly) < 2:
        st.info("The forecast needs at least 2 months of data.")
    else:
        x = np.arange(len(monthly))
        next_x = len(monthly)
        forecast = {}
        for cat in monthly.columns:
            # draw the best straight line through the past months
            slope, intercept = np.polyfit(x, monthly[cat].values, 1)
            forecast[cat] = max(0.0, slope * next_x + intercept)

        total_forecast = sum(forecast.values())
        next_month = monthly.index[-1] + 1
        last_total = monthly.iloc[-1].sum()

        st.metric(
            f"Predicted spending for {next_month}",
            f"₹{total_forecast:,.0f}",
            delta=f"₹{total_forecast - last_total:,.0f} vs {latest}",
            delta_color="inverse",
        )

        totals = monthly.sum(axis=1)
        chart_data = pd.DataFrame(
            {"Spending (₹)": list(totals.values) + [total_forecast]},
            index=[str(m) for m in totals.index] + [f"{next_month} (forecast)"],
        )
        st.bar_chart(chart_data)

        forecast_table = pd.DataFrame({
            "Category": list(forecast.keys()),
            "Forecast (₹)": [round(v) for v in forecast.values()],
        }).sort_values("Forecast (₹)", ascending=False).reset_index(drop=True)
        st.table(forecast_table)

        for cat, budget in st.session_state.budgets.items():
            if forecast.get(cat, 0) > budget:
                st.warning(
                    f"🔮 At this pace you may go over your **{cat}** budget "
                    f"next month (forecast ₹{forecast[cat]:,.0f} vs "
                    f"budget ₹{budget:,.0f})."
                )

        st.caption(
            "Forecast method: linear regression (a straight-line trend "
            "through your past monthly spending)."
        )
