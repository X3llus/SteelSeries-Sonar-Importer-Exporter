# import required libraries
from sqlite3 import connect
import csv
from uuid import uuid4
from tkinter import ttk, filedialog, Toplevel, Label, Button, Tk, StringVar, Entry
import os

def connect_to_db(database_file):
    # connect to the db file used by sonar
    conn = connect(database_file)
    return conn

def query_configs(conn, name, vad):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configs WHERE name = ? AND vad = ?", (name, vad))
    return cursor.fetchall()

def export_to_csv(rows, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['id', 'name', 'vad', 'data', 'schema_version', 'created_at', 'updated_at'])
        for row in rows:
            csv_writer.writerow(row)

def get_names_by_vad(conn, vad):
    # get the names of the configs for the given vad
    query = f"SELECT name FROM configs WHERE vad={vad}"
    cursor = conn.cursor()
    cursor.execute(query)
    names = [row[0] for row in cursor.fetchall()]
    return names

def check_name_vad_exists(conn, name, vad):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configs WHERE name = ? AND vad = ?", (name, vad))
    result = cursor.fetchone()
    return result is not None


def main():
    def set_database_file():
        # set the database file to be used by sonar
        nonlocal conn
        new_database_file = filedialog.askopenfilename(filetypes=[("Database Files", "*.db")])
        if new_database_file:
            conn = connect_to_db(new_database_file)
    
    def delete_entries_with_schema_version_3(conn):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM configs WHERE schema_version = ?", (3,))
        conn.commit()

    database_file = r"C:\ProgramData\SteelSeries\GG\apps\sonar\db\database.db"
    conn = connect_to_db(database_file)
    delete_entries_with_schema_version_3(conn)

    vad_mapping = {"Game": 1, "Chat": 2, "Mic": 3, "Media": 4, "Aux": 5}

    def show_popup(message):
        popup = Toplevel(root)
        popup.title("Success")
        label = Label(popup, text=message)
        label.pack(padx=10, pady=10)
        ok_button = Button(popup, text="OK", command=popup.destroy)
        ok_button.pack(pady=(0, 10))

    def update_names_dropdown(*args):
        selected_vad_text = vad_var.get()
        selected_vad = vad_mapping[selected_vad_text]
        names = get_names_by_vad(conn, selected_vad)
        name_var.set('')
        name_combobox['values'] = names

    def import_data_to_db(conn, input_file):
        with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip the header row

            cursor = conn.cursor()
            for row in csv_reader:
                name = row[1]
                vad = int(row[2])
                csv_schema_version = int(row[4])

                existing_rows = query_configs(conn, name, vad)
                if existing_rows:
                    existing_schema_version = existing_rows[0][4]
                    if existing_schema_version != csv_schema_version:
                        show_popup("Schema version mismatch. Import unsuccessful.")
                        return False

                id = str(uuid4())
                data = row[3]
                created_at = row[5]
                updated_at = row[6]

                cursor.execute(
                    "INSERT INTO configs (id, name, vad, data, schema_version, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (id, name, vad, data, csv_schema_version, created_at, updated_at),
                )
            conn.commit()
            return True

    def export_button_click():
        selected_name = name_var.get()
        selected_vad_text = vad_var.get()
        selected_vad = vad_mapping[selected_vad_text]

        rows = query_configs(conn, selected_name, selected_vad)
        if not rows:
            show_popup("No matching records found.")
            return

        schema_version = str(rows[0][4])  # Get schema_version from the first row
        filename = f"{selected_name}.{schema_version}.csv"

        # Let the user choose the folder to save the file
        selected_folder = filedialog.askdirectory()
        if not selected_folder:
            return

        output_file = os.path.join(selected_folder, filename)
        export_to_csv(rows, output_file)
        show_popup(f"Export successful! File saved as {output_file}")

    def import_button_click():
        input_file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not input_file:
            return

        with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            header = next(csv_reader)
            row = next(csv_reader)

        original_name = row[1]
        original_vad = int(row[2])

        if import_data_to_db(conn, input_file):
            show_popup("Import successful!")

    root = Tk()
    root.title("Sonar Config Exporter/Importer")
    root.resizable(False, False)

    change_db_button = Button(root, text="Change Database File", command=set_database_file)
    change_db_button.grid(row=0, column=2, padx=(10, 10), pady=(10, 5))

    vad_label = Label(root, text="Profile Type:")
    vad_label.grid(row=1, column=0, padx=(10, 5), pady=(5, 10))

    vad_var = StringVar(root)
    vad_combobox = ttk.Combobox(root, textvariable=vad_var, values=("Game", "Chat", "Mic", "Media", "Aux"))
    vad_combobox.grid(row=1, column=1, padx=(5, 10), pady=(5, 10))
    vad_combobox.bind("<<ComboboxSelected>>", update_names_dropdown)

    name_label = Label(root, text="Name:")
    name_label.grid(row=2, column=0, padx=(10, 5), pady=(5, 10))

    name_var = StringVar(root)
    name_combobox = ttk.Combobox(root, textvariable=name_var)
    name_combobox.grid(row=2, column=1, padx=(5, 10), pady=(5, 10))

    export_button = Button(root, text="Export to CSV", command=export_button_click)
    export_button.grid(row=3, column=0, padx=(10, 5), pady=(5, 10))

    import_button = Button(root, text="Import from CSV", command=import_button_click)
    import_button.grid(row=3, column=1, padx=(5, 10), pady=(5, 10))

    root.mainloop()

if __name__ == "__main__":
    main()
