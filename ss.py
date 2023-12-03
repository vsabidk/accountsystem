import tkinter as tk
from tkinter import ttk
import sqlite3
from tkcalendar import DateEntry
import customtkinter as ctk



# SQLite Database
conn = sqlite3.connect('chart_of_accounts.db')
c = conn.cursor()

# Create table if not exists
c.execute('''CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                balance REAL,
                created_date TEXT
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY,
                date TEXT,
                account_id INTEGER,
                debit REAL,
                credit REAL,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
             )''')
conn.commit()

# Tkinter setup
root = ctk.CTk()
root.resizable(False, False)

root.title("E-Accounting System")
ctk.set_default_color_theme("green")

def add_journal_entry():
    date = cal_journal.get_date()
    account_id = list(account_options.keys())[list(account_options.values()).index(accounts_combo.get())]
    debit = debit_entry.get()
    credit = credit_entry.get()

    if not (account_id and debit and credit):
        messagebox.showerror("Error", "Please fill all fields")
        return

    try:
        debit = float(debit)
        credit = float(credit)
    except ValueError:
        messagebox.showerror("Error", "Invalid debit or credit amount")
        return

    if debit <= 0 or credit <= 0:
        messagebox.showerror("Error", "Debit and Credit should be greater than zero")
        return

    # Update the journal entries
    c.execute("INSERT INTO journal_entries (date, account_id, debit, credit) VALUES (?, ?, ?, ?)",
              (date, account_id, debit, credit))
    conn.commit()

    # Update the account balances
    c.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (debit - credit, account_id))
    conn.commit()

    update_journal_treeview()
    update_treeview()





# Function to update journal Treeview
def update_journal_treeview():
    journal_tree.delete(*journal_tree.get_children())

    c.execute('''SELECT je.id, je.date, a.name, je.debit, je.credit
                 FROM journal_entries as je
                 INNER JOIN accounts as a ON je.account_id = a.id''')
    rows = c.fetchall()

    for row in rows:
        journal_tree.insert('', 'end', values=row)



# Function to add account
def add_account():
    name = name_entry.get()
    type = type_combo.get()
    balance = balance_entry.get()
    created_date = cal.get_date()

    c.execute("INSERT INTO accounts (name, type, balance, created_date) VALUES (?, ?, ?, ?)",
              (name, type, balance, created_date))
    conn.commit()
    update_treeview()
    update_account_options()


def update_account_options():
    # Fetch updated account options
    c.execute("SELECT id, name FROM accounts")
    account_rows = c.fetchall()
    account_options = {str(row[0]): row[1] for row in account_rows}

    # Update the options in the accounts_combo
    accounts_combo['values'] = list(account_options.values())


# Function to update account
def update_account():
    selected_item = tree.focus()
    values = tree.item(selected_item, 'values')
    account_id = values[0]
    name = name_entry.get()
    type = type_combo.get()
    balance = balance_entry.get()
    created_date = cal.get_date()

    c.execute("UPDATE accounts SET name=?, type=?, balance=?, created_date=? WHERE id=?",
              (name, type, balance, created_date, account_id))
    conn.commit()
    update_treeview()

# Function to delete account
def delete_account():
    selected_item = tree.focus()
    values = tree.item(selected_item, 'values')
    account_id = values[0]

    c.execute("DELETE FROM accounts WHERE id=?", (account_id,))
    conn.commit()
    update_treeview()

# Function to search account
def search_account():
    search_text = search_entry.get()
    c.execute("SELECT * FROM accounts WHERE name LIKE ?", ('%' + search_text + '%',))
    rows = c.fetchall()
    update_treeview(rows)



def delete_journal_entry():
    selected_item = journal_tree.focus()
    values = journal_tree.item(selected_item, 'values')
    if values:
        journal_entry_id = values[0]
        c.execute("DELETE FROM journal_entries WHERE id=?", (journal_entry_id,))
        conn.commit()
        update_journal_treeview()


# Function to update Treeview
def update_treeview(rows=None):
    tree.delete(*tree.get_children())

    if rows is None:
        c.execute("SELECT * FROM accounts")
        rows = c.fetchall()

    for row in rows:
        tree.insert('', 'end', values=row)


def generate_balance_sheet():
    # Fetch accounts and categorize into Asset, Liability, and Equity categories
    c.execute("SELECT * FROM accounts")
    accounts = c.fetchall()

    asset_accounts = [acc for acc in accounts if acc[2] == 'Asset']
    liability_accounts = [acc for acc in accounts if acc[2] == 'Liability']
    equity_accounts = [acc for acc in accounts if acc[2] == 'Equity']

    # Sort the accounts within each category by their ID
    asset_accounts.sort(key=lambda x: x[0])
    liability_accounts.sort(key=lambda x: x[0])
    equity_accounts.sort(key=lambda x: x[0])

    # Calculate totals for each category
    total_assets = sum(account[3] for account in asset_accounts)
    total_liabilities = sum(account[3] for account in liability_accounts)
    total_equity = sum(account[3] for account in equity_accounts)

    # Generate the balance sheet content
    balance_sheet_content = f"{'-' * 95}\n{'|':<3}{'ASSETS':^89}{'|':>4}\n{'-' * 95}\n"
    balance_sheet_content += f"| ID | {'Name':^40} |  Type  | {'Balance':^35} |\n{'-' * 95}\n"
    for account in asset_accounts:
        balance_sheet_content += f"| {account[0]:<2} | {account[1]:^40} | {'Asset':^6} | ${account[3]:>30,.2f} |\n"
    balance_sheet_content += f"{'-' * 95}\n| Total Assets{' ':>69} | ${total_assets:>,.2f}{' ':>25} |\n{'-' * 95}\n\n"

    balance_sheet_content += f"{'-' * 95}\n{'|':<3}{'LIABILITIES':^89}{'|':>4}\n{'-' * 95}\n"
    balance_sheet_content += f"| ID | {'Name':^40} |  Type  | {'Balance':^35} |\n{'-' * 95}\n"
    for account in liability_accounts:
        balance_sheet_content += f"| {account[0]:<2} | {account[1]:^40} | {'Liability':^6} | ${account[3]:>30,.2f} |\n"
    balance_sheet_content += f"{'-' * 95}\n| Total Liabilities{' ':>55} | ${total_liabilities:>,.2f}{' ':>39} |\n{'-' * 95}\n\n"

    balance_sheet_content += f"{'-' * 95}\n{'|':<3}{'EQUITY':^89}{'|':>4}\n{'-' * 95}\n"
    balance_sheet_content += f"| ID | {'Name':^40} |  Type  | {'Balance':^35} |\n{'-' * 95}\n"
    for account in equity_accounts:
        balance_sheet_content += f"| {account[0]:<2} | {account[1]:^40} | {'Equity':^6} | ${account[3]:>30,.2f} |\n"
    balance_sheet_content += f"{'-' * 95}\n| Total Equity{' ':>69} | ${total_equity:>,.2f}{' ':>25} |\n{'-' * 95}\n\n"

    balance_sheet_content += f"{'-' * 95}\n| Total Liabilities and Equity{' ':>35} | ${total_liabilities + total_equity:>,.2f}{' ':>59} |\n{'-' * 95}\n"

    # Display the balance sheet in the Balance Sheet tab
    balance_sheet_text.delete(1.0, tk.END)  # Clear previous content
    balance_sheet_text.insert(tk.END, balance_sheet_content)




def generate_cash_flow_statement():
    operating_activities = []
    investing_activities = []
    financing_activities = []

    # Retrieve transactions from the journal entries
    c.execute("SELECT * FROM journal_entries")
    transactions = c.fetchall()

    # Define criteria for operating, investing, and financing accounts based on account types
    operating_account_types = ['Income', 'Expense']  # Adjust based on your criteria
    investing_account_types = ['Asset']  # Adjust based on your criteria
    financing_account_types = ['Liability', 'Equity']  # Adjust based on your criteria

    for transaction in transactions:
        account_id = transaction[2]
        debit_amount = transaction[3]
        credit_amount = transaction[4]

        # Fetch account type from the 'accounts' table
        c.execute("SELECT type FROM accounts WHERE id=?", (account_id,))
        account_type_row = c.fetchone()
        if account_type_row:
            account_type = account_type_row[0]

            # Categorize transactions based on account type
            if account_type in operating_account_types:
                if debit_amount > 0:
                    operating_activities.append(debit_amount)
                elif credit_amount > 0:
                    operating_activities.append(-credit_amount)
            elif account_type in investing_account_types:
                if debit_amount > 0:
                    investing_activities.append(debit_amount)
                elif credit_amount > 0:
                    investing_activities.append(-credit_amount)
            elif account_type in financing_account_types:
                if debit_amount > 0:
                    financing_activities.append(debit_amount)
                elif credit_amount > 0:
                    financing_activities.append(-credit_amount)

    # Calculate totals for each category
    total_operating = sum(operating_activities)
    total_investing = sum(investing_activities)
    total_financing = sum(financing_activities)

    # Calculate net cash flow
    net_cash_flow = total_operating + total_investing + total_financing

    # Generate the cash flow statement content
    cash_flow_statement_content = f"OPERATING ACTIVITIES: ${total_operating:,.2f}\n"
    cash_flow_statement_content += f"INVESTING ACTIVITIES: ${total_investing:,.2f}\n"
    cash_flow_statement_content += f"FINANCING ACTIVITIES: ${total_financing:,.2f}\n\n"
    cash_flow_statement_content += f"NET CASH FLOW: ${net_cash_flow:,.2f}\n"

    # Display the cash flow statement in the Cash Flow Statement tab
    cash_flow_statement_text.delete(1.0, tk.END)  # Clear previous content
    cash_flow_statement_text.insert(tk.END, cash_flow_statement_content)


def generate_trial_balance():
    # Retrieve balances from the accounts table
    c.execute("SELECT name, balance FROM accounts")
    accounts_balance = c.fetchall()

    # Initialize variables for total debit and credit
    total_debit = 0
    total_credit = 0

    # Calculate total debits and credits separately
    for _, balance in accounts_balance:
        if balance > 0:
            total_debit += balance  # Consider positive balances as debits
        elif balance < 0:
            total_credit += abs(balance)  # Consider negative balances as credits

    # Generate the trial balance content
    trial_balance_content = f"TRIAL BALANCE\n"
    trial_balance_content += f"{'Account':<20}{'Balance':>15}\n"
    for account, balance in accounts_balance:
        trial_balance_content += f"{account:<20}${balance:>15,.2f}\n"

    # Display the totals
    trial_balance_content += f"\nTotal Debit: ${total_debit:,.2f}\n"
    trial_balance_content += f"Total Credit: ${total_credit:,.2f}\n"

    # Display the trial balance in the Trial Balance tab
    trial_balance_text.delete(1.0, tk.END)  # Clear previous content
    trial_balance_text.insert(tk.END, trial_balance_content)






def generate_income_statement():
    income_accounts = []
    expense_accounts = []

    # Categorize accounts into Income and Expense categories
    c.execute("SELECT * FROM accounts")
    accounts = c.fetchall()

    for account in accounts:
        if account[2] == 'Income':
            income_accounts.append(account)
        elif account[2] == 'Expense':
            expense_accounts.append(account)

    # Calculate totals for each category
    total_income = sum(account[3] for account in income_accounts)
    total_expense = sum(account[3] for account in expense_accounts)

    # Calculate net income
    net_income = total_income - total_expense

    # Generate the income statement content
    income_statement_content = f"INCOME\n"
    for account in income_accounts:
        income_statement_content += f"{account[1]}: ${account[3]:,.2f}\n"
    income_statement_content += f"Total Income: ${total_income:,.2f}\n\n"

    income_statement_content += f"EXPENSES\n"
    for account in expense_accounts:
        income_statement_content += f"{account[1]}: ${account[3]:,.2f}\n"
    income_statement_content += f"Total Expenses: ${total_expense:,.2f}\n\n"

    income_statement_content += f"NET INCOME: ${net_income:,.2f}\n"

    # Display the income statement in the Income Statement tab
    income_statement_text.delete(1.0, tk.END)  # Clear previous content
    income_statement_text.insert(tk.END, income_statement_content)







def on_tree_select(event):
    selected_item = tree.focus()
    values = tree.item(selected_item, 'values')

    if values:
        name_entry.delete(0, tk.END)
        name_entry.insert(0, values[1])
        type_combo.set(values[2])
        balance_entry.delete(0, tk.END)
        balance_entry.insert(0, values[3])
        cal.set_date(values[4])
        try:
            # Handling date format conversion
            date_str = values[4]
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            cal.set_date(date_obj.strftime("%m/%d/%Y"))
        except ValueError:
            # Display an error message
            messagebox.showerror("Error", "Invalid date format")



# Tab setup
# Create a custom style for the tabs
style = ttk.Style()

# Configure the tabs' appearance
style.configure('Custom.TNotebook.Tab', padding=[20, 8], font=('Arial', 12))
style.map('Custom.TNotebook.Tab', foreground=[('selected', 'black')], background=[('selected', '#DDDDDD')])

# Apply the style to the Notebook (tab_control)
tab_control = ttk.Notebook(root, style='Custom.TNotebook')


tab1 = ttk.Frame(tab_control)
tab_control.add(tab1, text='Accounts')



name_label = ctk.CTkLabel(tab1, text='Name:')
name_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
name_entry = ctk.CTkEntry(tab1)
name_entry.grid(row=0, column=1, padx=10, pady=5)

type_label = ctk.CTkLabel(tab1, text='Type:')
type_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')
account_types = ['Asset', 'Liability', 'Equity', 'Income', 'Expense']
type_combo = ctk.CTkComboBox(tab1, values=account_types)
type_combo.grid(row=1, column=1, padx=10, pady=5)

balance_label = ctk.CTkLabel(tab1, text='Balance:')
balance_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')
balance_entry = ctk.CTkEntry(tab1)
balance_entry.grid(row=2, column=1, padx=10, pady=5)

date_label = ctk.CTkLabel(tab1, text='Created Date:')
date_label.grid(row=3, column=0, padx=10, pady=5, sticky='w')
cal = DateEntry(tab1, width=12, background='darkblue', foreground='white', borderwidth=2)
cal.grid(row=3, column=1, padx=10, pady=5)

# Buttons
add_button = ctk.CTkButton(tab1, text='Add Account', command=add_account)
add_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

update_button = ctk.CTkButton(tab1, text='Update Account', command=update_account)
update_button.grid(row=5, column=0, columnspan=2, padx=10, pady=5)

delete_button = ctk.CTkButton(tab1, text='Delete Account', command=delete_account)
delete_button.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

# Search
search_label = ctk.CTkLabel(tab1, text='Search Account:')
search_label.grid(row=7, column=0, padx=10, pady=5, sticky='w')
search_entry = ctk.CTkEntry(tab1)
search_entry.grid(row=7, column=1, padx=10, pady=5)
search_button = ctk.CTkButton(tab1, text='Search', command=search_account)
search_button.grid(row=8, column=0, columnspan=2, padx=10, pady=5)

# Treeview
tree = ttk.Treeview(tab1, columns=('ID', 'Name', 'Type', 'Balance', 'Created Date'), show='headings')
tree.heading('ID', text='ID')
tree.heading('Name', text='Name')
tree.heading('Type', text='Type')
tree.heading('Balance', text='Balance')
tree.heading('Created Date', text='Created Date')
tree.grid(row=0, column=2, rowspan=9, padx=10, pady=10, sticky='nsew')

tree.bind("<<TreeviewSelect>>", on_tree_select)

update_treeview()

# Configure weight of rows and columns to make the UI responsive
tab1.columnconfigure(2, weight=1)
tab1.rowconfigure(8, weight=1)

tab_control.pack(expand=1, fill="both")


tab2 = ttk.Frame(tab_control)
tab_control.add(tab2, text='Journal')

# Journal Entry Fields
journal_label = ctk.CTkLabel(tab2, text='Date:')
journal_label.grid(row=0, column=0, padx=10, pady=5, sticky='w')
cal_journal = DateEntry(tab2, width=12, background='darkblue', foreground='white', borderwidth=2)
cal_journal.grid(row=0, column=1, padx=10, pady=5)

account_label = ctk.CTkLabel(tab2, text='Account:')
account_label.grid(row=1, column=0, padx=10, pady=5, sticky='w')

# Fetching accounts from the database
c.execute("SELECT id, name FROM accounts")
account_rows = c.fetchall()
account_options = {str(row[0]): row[1] for row in account_rows}
accounts_combo = ctk.CTkComboBox(tab2, values=list(account_options.values()))
accounts_combo.grid(row=1, column=1, padx=10, pady=5)

debit_label = ctk.CTkLabel(tab2, text='Debit:')
debit_label.grid(row=2, column=0, padx=10, pady=5, sticky='w')
debit_entry = ctk.CTkEntry(tab2)
debit_entry.grid(row=2, column=1, padx=10, pady=5)

credit_label = ctk.CTkLabel(tab2, text='Credit:')
credit_label.grid(row=3, column=0, padx=10, pady=5, sticky='w')
credit_entry = ctk.CTkEntry(tab2)
credit_entry.grid(row=3, column=1, padx=10, pady=5)

add_journal_button = ctk.CTkButton(tab2, text='Add Entry', command=add_journal_entry)
add_journal_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

delete_journal_button = ctk.CTkButton(tab2, text='Delete Entry', command=delete_journal_entry)
delete_journal_button.grid(row=5, column=0, columnspan=2, padx=10, pady=5)




# Journal Treeview
journal_tree = ttk.Treeview(tab2, columns=('ID', 'Date', 'Account', 'Debit', 'Credit'), show='headings')
journal_tree.heading('ID', text='ID')
journal_tree.heading('Date', text='Date')
journal_tree.heading('Account', text='Account')
journal_tree.heading('Debit', text='Debit')
journal_tree.heading('Credit', text='Credit')
journal_tree.grid(row=0, column=2, rowspan=5, padx=10, pady=10, sticky='nsew')

update_journal_treeview()

tab_control.pack(expand=1, fill="both")

# ... (previous code remains unchanged)

tab3 = ttk.Frame(tab_control)
tab_control.add(tab3, text='Ledger')
# Add entry widgets for search criteri
def generate_ledger():
    # Clear previous entries in the ledger Treeview
    ledger_tree.delete(*ledger_tree.get_children())

    # Fetch all ledger entries
    c.execute('''SELECT je.id, je.date, a.name, je.debit, je.credit
                 FROM journal_entries as je
                 INNER JOIN accounts as a ON je.account_id = a.id''')
    ledger_rows = c.fetchall()

    # Display the ledger entries in the ledger Treeview
    for row in ledger_rows:
        ledger_tree.insert('', 'end', values=row)

generate_ledger_button = ctk.CTkButton(tab3, text='Generate Ledger', command=generate_ledger)
generate_ledger_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)


ledger_tree = ttk.Treeview(tab3, columns=('ID', 'Date', 'Account', 'Debit', 'Credit', 'Balance'), show='headings')
ledger_tree.heading('ID', text='ID')
ledger_tree.heading('Date', text='Date')
ledger_tree.heading('Account', text='Account')
ledger_tree.heading('Debit', text='Debit')
ledger_tree.heading('Credit', text='Credit')
ledger_tree.heading('Balance', text='Balance')
ledger_tree.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

# ... (previous code remains unchanged)










# Configure column headings and widths
ledger_tree.heading('ID', text='ID')
ledger_tree.heading('Date', text='Date')
ledger_tree.heading('Account', text='Account')
ledger_tree.heading('Debit', text='Debit')
ledger_tree.heading('Credit', text='Credit')
ledger_tree.heading('Balance', text='Balance')
ledger_tree.column('Debit', anchor='center', width=100)
ledger_tree.column('Credit', anchor='center', width=100)
ledger_tree.column('Balance', anchor='center', width=120)



# Configure weight of rows and columns to make the UI responsive
tab3.columnconfigure(0, weight=1)
tab3.rowconfigure(0, weight=1)

tab_control.pack(expand=1, fill="both")


tab4 = ttk.Frame(tab_control)
tab_control.add(tab4, text='Balance Sheet')

# Balance Sheet Text Widget
balance_sheet_text = tk.Text(tab4, width=100, height=40, font=("Arial", 10))
balance_sheet_text.pack()

# Generate Balance Sheet Button
generate_balance_sheet_button = ctk.CTkButton(tab4, text='Generate Balance Sheet', command=generate_balance_sheet)
generate_balance_sheet_button.pack()

tab5 = ttk.Frame(tab_control)
tab_control.add(tab5, text='Income Statement')

# Income Statement Text Widget
income_statement_text = tk.Text(tab5, height=20, width=60)
income_statement_text.pack()

# Generate Income Statement Button
generate_income_statement_button = ctk.CTkButton(tab5, text='Generate Income Statement', command=generate_income_statement)
generate_income_statement_button.pack()


tab6 = ttk.Frame(tab_control)
tab_control.add(tab6, text='Cash Flow Statement')

# Cash Flow Statement Text Widget
cash_flow_statement_text = tk.Text(tab6, height=20, width=60)
cash_flow_statement_text.pack()

# Generate Cash Flow Statement Button
generate_cash_flow_statement_button = ctk.CTkButton(tab6, text='Generate Cash Flow Statement',
                                                 command=generate_cash_flow_statement)
generate_cash_flow_statement_button.pack()


tab7 = ttk.Frame(tab_control)
tab_control.add(tab7, text='Trial Balance')

# Trial Balance Text Widget
trial_balance_text = tk.Text(tab7, height=20, width=60)
trial_balance_text.pack()

# Generate Trial Balance Button
generate_trial_balance_button = ctk.CTkButton(tab7, text='Generate Trial Balance', command=generate_trial_balance)
generate_trial_balance_button.pack()



root.mainloop()

# Close the database connection on program exit
conn.close()
