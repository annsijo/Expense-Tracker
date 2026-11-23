import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Expense Tracker", page_icon="💰")
st.title("💰 Personal Expense Tracker")

# This is where we keep all transactions while the app is open
if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=["Date", "Type", "Category", "Amount", "Description"]
    )

CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Entertainment",
              "Health", "Education", "Salary", "Other"]

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
