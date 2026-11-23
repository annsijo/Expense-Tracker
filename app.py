import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Expense Tracker", page_icon="💰")
st.title("💰 Personal Expense Tracker")

# This is where we keep all data while the app is open
if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=["Date", "Type", "Category", "Amount", "Description"]
    )
if "budgets" not in st.session_state:
    st.session_state.budgets = {}

EXPENSE_CATEGORIES = ["Food", "Travel", "Shopping", "Bills",
                      "Entertainment", "Health", "Education", "Other"]
CATEGORIES = EXPENSE_CATEGORIES + ["Salary"]

# ---------- Add a transaction ----------
st.header("Add a transaction")
with st.form("add_form", clear_on_submit=True):
    t_date = st.date_input("Date", value=date.today())
    t_type = st.selectbox("Type", ["Expense", "Income"])
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

# ---------- History ----------
st.header("Transaction history")
if df.empty:
    st.info("No transactions yet. Add your first one above!")
else:
    st.dataframe(df, use_container_width=True)

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
