import sqlite3
import pandas as pd
import uuid
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

def connect_to_db(database_file):
    conn = sqlite3.connect(database_file)
    return conn

def query_configs(conn, name, vad):
    query = f"SELECT * FROM configs WHERE name='{name}' AND vad={vad}"
    df = pd.read_sql_query(query, conn)
    return df

def export_to_csv(df, output_file):
    df.to_csv(output_file, index=False)

def import_from_csv(conn, input_file, new_id=True):
    df = pd.read_csv(input_file)
    if new_id:
        df['id'] = str(uuid.uuid4())
    df.to_sql("configs", conn, if_exists="append", index=False)

def get_names_by_vad(conn, vad):
    query = f"SELECT name FROM configs WHERE vad={vad}"
    cursor = conn.cursor()
    cursor.execute(query)
    names = [row[0] for row in cursor.fetchall()]
    return names

def main():
    def set_database_file():
        nonlocal conn
        new_database_file = filedialog.askopenfilename(filetypes=[("Database Files", "*.db")])
        if new_database_file:
            conn = connect_to_db(new_database_file)

    database_file = r"C:\ProgramData\SteelSeries\GG\apps\sonar\db\database.db"
    conn = connect_to_db(database_file)

    vad_mapping = {"Game": 1, "Chat": 2, "Mic": 3, "Media": 4, "Aux": 5}

    def show_popup(message):
        popup = tk.Toplevel(root)
        popup.title("Success")
        label = tk.Label(popup, text=message)
        label.pack(padx=10, pady=10)
        ok_button = tk.Button(popup, text="OK", command=popup.destroy)
        ok_button.pack(pady=(0, 10))

    def update_names_dropdown(*args):
        selected_vad_text = vad_var.get()
        selected_vad = vad_mapping[selected_vad_text]
        names = get_names_by_vad(conn, selected_vad)
        name_var.set('')
        name_combobox['values'] = names

    def export_button_click():
        selected_name = name_var.get()
        selected_vad_text = vad_var.get()
        selected_vad = vad_mapping[selected_vad_text]
        output_file = filedialog.asksaveasfilename(defaultextension=".csv")
        if not output_file:
            return
        df = query_configs(conn, selected_name, selected_vad)
        export_to_csv(df, output_file)
        show_popup("Export successful!")

    def import_button_click():
        input_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not input_file:
            return
        import_from_csv(conn, input_file)
        show_popup("Import successful!")

    root = tk.Tk()
    root.title("Sonar Config Exporter/Importer")
    root.resizable(False, False)

    change_db_button = tk.Button(root, text="Change Database File", command=set_database_file)
    change_db_button.grid(row=0, column=2, padx=(10, 10), pady=(10, 5))

    vad_label = tk.Label(root, text="VAD:")
    vad_label.grid(row=1, column=0, padx=(10, 5), pady=(5, 10))

    vad_var = tk.StringVar(root)
    vad_combobox = ttk.Combobox(root, textvariable=vad_var, values=("Game", "Chat", "Mic", "Media", "Aux"))
    vad_combobox.grid(row=1, column=1, padx=(5, 10), pady=(5, 10))
    vad_combobox.bind("<<ComboboxSelected>>", update_names_dropdown)

    name_label = tk.Label(root, text="Name:")
    name_label.grid(row=2, column=0, padx=(10, 5), pady=(5, 10))

    name_var = tk.StringVar(root)
    name_combobox = ttk.Combobox(root, textvariable=name_var)
    name_combobox.grid(row=2, column=1, padx=(5, 10), pady=(5, 10))

    export_button = tk.Button(root, text="Export to CSV", command=export_button_click)
    export_button.grid(row=3, column=0, padx=(10, 5), pady=(5, 10))

    import_button = tk.Button(root, text="Import from CSV", command=import_button_click)
    import_button.grid(row=3, column=1, padx=(5, 10), pady=(5, 10))

    root.mainloop()



if __name__ == "__main__":
    main()
