import tkinter as tk
from tkinter import messagebox
import psycopg2
import subprocess
import os,sys
from config import host, user, password, db_name, port

# Підключення до БД
try:
    connection = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name
    )
except Exception as e:
    print("[ERROR] Підключення:", e)
    connection = None

def launch_program(user_id, name, is_admin):
    def open_admin_panel():
        choice_win.destroy()
        root.destroy()
        subprocess.Popen(
            [sys.executable, os.path.abspath("Program.py"), str(user_id), name],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def open_sales_panel():
        choice_win.destroy()
        root.destroy()
        subprocess.Popen(
            [sys.executable, os.path.abspath("Sales.py"), str(user_id), name],
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    if is_admin:
        choice_win = tk.Toplevel(root)
        choice_win.title("Вибір режиму")
        choice_win.geometry("300x150")

        tk.Label(choice_win, text=f"Вітаємо, {name}!", font=("Arial", 12)).pack(pady=10)
        tk.Button(choice_win, text="Панель керування", command=open_admin_panel).pack(pady=5, fill="x", padx=20)
        tk.Button(choice_win, text="Панель касира", command=open_sales_panel).pack(pady=5, fill="x", padx=20)
    else:
        root.destroy()
        subprocess.Popen(
            [sys.executable, os.path.abspath("Sales.py"), str(user_id), name],
            creationflags=subprocess.CREATE_NO_WINDOW
        )


def login():
    name = entry_user.get().strip()
    pwd = entry_pass.get().strip()

    if not name or not pwd:
        messagebox.showwarning("Увага", "Уведіть ім’я та пароль!")
        return

    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT id_user, name_user, password_user, status_user FROM users WHERE name_user = %s',
            (name,))
        user_data = cursor.fetchone()

    if not user_data or user_data[2] != pwd:
        messagebox.showerror("Помилка", "Невірне ім’я або пароль!")
        return

    user_id, username, _, role = user_data
    launch_program(user_id, username, is_admin=(role == 1))

# Вікно входу
root = tk.Tk()
root.title("Вхід у систему")
root.geometry("300x220")

tk.Label(root, text="Ім’я користувача").pack(pady=5)
entry_user = tk.Entry(root)
entry_user.pack(pady=5)

tk.Label(root, text="Пароль").pack(pady=5)
entry_pass = tk.Entry(root, show='*')
entry_pass.pack(pady=5)

tk.Button(root, text="Увійти", command=login).pack(pady=15)

root.mainloop()
