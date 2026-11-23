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
TYPES = ["Expense", "Income"]

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
                selected, ["Date", "Type", "Category", "Amount", "Description"]
            ] = [e_date, e_type, e_category, e_amount, e_desc]
            st.toast("Transaction updated!")
            st.rerun()

    if delete_clicked:
        st.session_state.transactions = (
            st.session_state.transactions.drop(selected).reset_index(drop=True)
        )
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
