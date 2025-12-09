import customtkinter as ctk
from tkinter import messagebox
import pyodbc
import socket
import platform
import geocoder
from datetime import datetime

# === SQL Server Connection ===
conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=HAMZA-LAPTOP;'  # Change to your actual server #HAMZA-LAPTOP\\SQLEXPRESS
    'DATABASE=Fraud;'              # Change to your actual database
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

session = {
    "user_id": None,
    "user_name": "",
    "email": "",
    "phone": "",
    "balance": 0.0,
    "is_admin": False
}

def Ddetails():
    os = f"{platform.system()} {platform.release()}"
    hostname = socket.gethostname()
    return f"{hostname} ({os})"

def ipaddress():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "Unknown"

def Dlocation():
    try:
        g = geocoder.ip('me')
        return g.city #or "Unknown"
    except:
        return "Unknown"

def Addlogs(action):
    cursor.execute("INSERT INTO Logs (user_id, action) VALUES (?, ?)", session["user_id"], action)
    conn.commit()

def Uregister():
    name = entry_name.get()
    email = entry_email.get()
    phone = entry_phone.get()
    password = entry_password.get()

    if not all([name, email, phone, password]):
        messagebox.showerror("Error", "All fields are required!")
        return

    try:
        cursor.execute("INSERT INTO Users (name, email, phone_number, password, balance) VALUES (?, ?, ?, ?, ?)",
                       name, email, phone, password, 1000.0)
        conn.commit()
        messagebox.showinfo("Success", "Registered with PKR 1000")
        for field in [entry_name, entry_email, entry_phone, entry_password]:
            field.delete(0, 'end')
    except Exception as e:
        messagebox.showerror("Error", str(e))

def Ulogin():
    email = login_email.get()
    password = login_password.get()
    cursor.execute("SELECT user_id, name, phone_number, balance FROM Users WHERE email = ? AND password = ?", email, password)
    user = cursor.fetchone()
    if user:
        session["user_id"], session["user_name"], session["phone"], session["balance"] = user
        session["email"] = email
        session["is_admin"] = (email == "admin@example.com" and session["phone"] == "0000")
        Addlogs("Logged in")
        device_type = platform.system()
        os_name = f'{platform.system()} {platform.release()}'
        ip = ipaddress()
        location = Dlocation()
        now = datetime.now()

        cursor.execute("""
            INSERT INTO Device_Usage (user_id, device_type, os_name, ip_address, location, last_used_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, session["user_id"], device_type, os_name, ip, location, now)
        conn.commit()
        app.destroy()
        dashboard()

    else:
        messagebox.showerror("Login Failed", "Invalid credentials")

def logout():
    Addlogs("Logged out")
    dashboard.destroy()
    main()

def Tamount():
    rphone = transfer_phone.get()
    try:
        amount = float(transfer_amount.get())
        if amount <= 0:
            messagebox.showerror("Error", "Amount must be greater than zero.")
            return
    except ValueError:
        messagebox.showerror("Error", "Invalid amount.")
        return

    currency = "PKR"
    location = Dlocation() if location_mode.get() == "auto" else manual_location.get()
    device = Ddetails()
    ip = ipaddress()

    if rphone == session["phone"]:
        messagebox.showerror("Invalid", "Cannot send to yourself.")
        return

    cursor.execute("SELECT user_id, balance FROM Users WHERE phone_number = ?", rphone)
    receiver = cursor.fetchone()

    if not receiver:
        messagebox.showerror("Error", "Recipient not found.")
        return

    receiver_id, _ = receiver

    if session["balance"] < amount:
        messagebox.showerror("Insufficient Funds", "Not enough balance.")
        return

    cursor.execute("UPDATE Users SET balance = balance - ? WHERE user_id = ?", amount, session["user_id"])
    cursor.execute("UPDATE Users SET balance = balance + ? WHERE user_id = ?", amount, receiver_id)
    cursor.execute("""
        INSERT INTO Transactions (sender_id, receiver_id, amount, currency, location, device_info, ip_address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, session["user_id"], receiver_id, amount, currency, location, device, ip)
    conn.commit()

    cursor.execute("SELECT balance FROM Users WHERE user_id = ?", session["user_id"])
    session["balance"] = cursor.fetchone()[0]
    balance_label.configure(text=f"Balance: PKR {session['balance']:.2f}")

    Addlogs(f"Sent PKR {amount:.2f} to {rphone}")
    cursor.execute("INSERT INTO Logs (user_id, action) VALUES (?, ?)", receiver_id, f"Received PKR {amount:.2f} from {session['phone']}")
    conn.commit()

    Dfrauds(amount, location)

    for field in [transfer_phone, transfer_amount, manual_location]:
        field.delete(0, 'end')

    refresh()
    messagebox.showinfo("Success", f"Transferred PKR {amount:.2f} to {rphone}")

def Dfrauds(amount, location):
    if amount >= 1000000:
        reason = "Large transaction"
        cursor.execute("INSERT INTO Fraud_Alerts (transaction_id, user_id, fraud_score, reason) VALUES ((SELECT MAX(transaction_id) FROM Transactions), ?, ?, ?)",
                       session["user_id"], 90, reason)
        conn.commit()
        Addlogs(f"Fraud alert triggered: {reason}")

    cursor.execute("""
        SELECT COUNT(DISTINCT location) FROM Transactions
        WHERE sender_id = ? AND timestamp >= DATEADD(MINUTE, -5, GETDATE())
    """, session["user_id"])
    if cursor.fetchone()[0] > 1:
        reason = "Multiple locations in short time"
        cursor.execute("INSERT INTO Fraud_Alerts (transaction_id, user_id, fraud_score, reason) VALUES ((SELECT MAX(transaction_id) FROM Transactions), ?, ?, ?)",
                       session["user_id"], 85, reason)
        conn.commit()
        Addlogs(f"Fraud alert triggered: {reason}")

    cursor.execute("""
        SELECT COUNT(*) FROM Transactions
        WHERE sender_id = ? AND timestamp >= DATEADD(MINUTE, -5, GETDATE())
    """, session["user_id"])
    if cursor.fetchone()[0] >= 5:
        reason = "High transaction frequency (5+ in 5 mins)"
        cursor.execute("INSERT INTO Fraud_Alerts (transaction_id, user_id, fraud_score, reason) VALUES ((SELECT MAX(transaction_id) FROM Transactions), ?, ?, ?)",
                       session["user_id"], 80, reason)
        conn.commit()
        Addlogs(f"Fraud alert triggered: {reason}")

# def Mlocation():
#     if location_mode.get() == "auto":
#         manual_location.pack_forget()
#     else:
#         manual_location.pack(pady=5)

def refresh():
    cursor.execute("SELECT balance FROM Users WHERE user_id = ?", session["user_id"])
    session["balance"] = cursor.fetchone()[0]
    balance_label.configure(text=f"Balance: PKR {session['balance']:.2f}")

    log_box.configure(state="normal")
    log_box.delete("0.0", "end")

    if session["is_admin"]:
        cursor.execute("SELECT U.user_id,U.name, L.action, L.timestamp FROM Logs L JOIN Users U ON L.user_id = U.user_id ORDER BY L.timestamp DESC")
    else:
        cursor.execute("SELECT action, timestamp FROM Logs WHERE user_id = ? ORDER BY timestamp DESC", session["user_id"])

    logs = cursor.fetchall()
    for row in logs:
        if session["is_admin"]:
            log_box.insert("end", f"{row[3]} | {row[1]}({row[0]}) → {row[2]}\n\n")
        else:
            log_box.insert("end", f"{row[1]} - {row[0]}\n\n")
    log_box.configure(state="disabled")

    fraud_box.configure(state="normal")
    fraud_box.delete("0.0", "end")
    if session["is_admin"]:
        cursor.execute("SELECT U.user_id,U.name, F.reason, F.created_at FROM Fraud_Alerts F JOIN Users U ON F.user_id = U.user_id ORDER BY F.created_at DESC")
    else:
        cursor.execute("SELECT reason, created_at FROM Fraud_Alerts WHERE user_id = ? ORDER BY created_at DESC", session["user_id"])
    for row in cursor.fetchall():
        if session["is_admin"]:
            fraud_box.insert("end", f"{row[3]} | {row[1]}({row[0]}) → {row[2]}\n\n")
        else:
            fraud_box.insert("end", f"{row[1]} - {row[0]}\n\n")
    fraud_box.configure(state="disabled")

def dashboard():
    global dashboard, transfer_phone, transfer_amount, balance_label, log_box, fraud_box, manual_location, location_mode

    dashboard = ctk.CTk()
    dashboard.geometry("800x600")
    dashboard.title("Dashboard")

    ctk.CTkLabel(dashboard, text=f"Welcome, {session['user_name']}", font=("Arial", 20)).pack(pady=10)
    balance_label = ctk.CTkLabel(dashboard, text=f"Balance: PKR {session['balance']:.2f}", font=("Arial", 16))
    balance_label.pack(pady=5)

    transfer_frame = ctk.CTkFrame(dashboard)
    transfer_frame.pack(pady=10)

    transfer_phone = ctk.CTkEntry(transfer_frame, placeholder_text="Recipient Phone"); transfer_phone.pack(pady=5)
    transfer_amount = ctk.CTkEntry(transfer_frame, placeholder_text="Amount"); transfer_amount.pack(pady=5)
    manual_location = ctk.CTkEntry(transfer_frame, placeholder_text="Manual Location (optional)"); manual_location.pack(pady=5)

    location_mode = ctk.StringVar(value="auto")
    manual_location.pack_forget()
    # ctk.CTkRadioButton(transfer_frame, text="Auto", variable=location_mode, value="auto", command=Mlocation).pack()
    # ctk.CTkRadioButton(transfer_frame, text="Manual", variable=location_mode, value="manual", command=Mlocation).pack()
    # Mlocation()

    ctk.CTkButton(dashboard, text="Send", command=Tamount).pack(pady=10)
    ctk.CTkButton(dashboard, text="Logout", fg_color="red", command=logout).pack()

    container = ctk.CTkFrame(dashboard)
    container.pack(pady=10, fill="both", expand=True)

    log_frame = ctk.CTkFrame(container)
    log_frame.pack(side="left", padx=10, pady=10, fill="y", expand=True)
    ctk.CTkLabel(log_frame, text="Notifications & Logs", font=("Arial", 14)).pack()
    log_box = ctk.CTkTextbox(log_frame, width=450, height=300)
    log_box.pack()
    log_box.configure(state="disabled")

    fraud_frame = ctk.CTkFrame(container)
    fraud_frame.pack(side="right", padx=10, pady=10, fill="y", expand=True)
    ctk.CTkLabel(fraud_frame, text="Fraud Alerts", font=("Arial", 14)).pack()
    fraud_box = ctk.CTkTextbox(fraud_frame, width=450, height=300)
    fraud_box.pack()
    fraud_box.configure(state="disabled")

    refresh()
    dashboard.mainloop()

def main():
    global app, entry_name, entry_email, entry_phone, entry_password, login_email, login_password
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    app.geometry("400x500")
    app.title("Fraud Banking System")

    frame = ctk.CTkFrame(app)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    ctk.CTkLabel(frame, text="Register", font=("Arial", 18)).pack(pady=5)
    entry_name = ctk.CTkEntry(frame, placeholder_text="Name"); entry_name.pack()
    entry_email = ctk.CTkEntry(frame, placeholder_text="Email"); entry_email.pack()
    entry_phone = ctk.CTkEntry(frame, placeholder_text="Phone"); entry_phone.pack()
    entry_password = ctk.CTkEntry(frame, placeholder_text="Password", show="*"); entry_password.pack()
    ctk.CTkButton(frame, text="Register", command=Uregister).pack(pady=5)

    ctk.CTkLabel(frame, text="Login", font=("Arial", 18)).pack(pady=5)
    login_email = ctk.CTkEntry(frame, placeholder_text="Email"); login_email.pack()
    login_password = ctk.CTkEntry(frame, placeholder_text="Password", show="*"); login_password.pack()
    ctk.CTkButton(frame, text="Login", command=Ulogin).pack(pady=5)

    app.mainloop()

main()