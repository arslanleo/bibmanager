"""
Bibliography Manager

A Tkinter-based GUI application for managing bibliographic entries (articles, books, etc.).
Supports adding, editing, searching, browsing, and importing BibTeX entries.
All data is stored in JSON files for portability and ease of editing.

Main modules:
- File/database initialization and loading
- BibTeX field/type management
- Entry add/edit/search/browse/import GUIs
- Duplicate and required field checking
"""

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import json
import os
from difflib import SequenceMatcher
import re

# Initialize file names
BIB_FILE = 'bibliography_db.json'
SETTINGS_FILE = 'settings.json'
INPUT_FILE = 'input.txt'
BIBTEX_FIELDS_FILE = 'bibtexFields.json'

# Initialize BibTeX fields
bibtex_info = {}
BIB_ENTRY_TYPES = []
BIB_FIELDS = []

def init_files():
    """
    Initialize the main database and settings files if they do not exist.
    """
    if not os.path.exists(BIB_FILE):
        with open(BIB_FILE, 'w') as f:
            json.dump({}, f)
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({'field_order': BIB_FIELDS,
                       'match_options': ['contains'],
                       'fuzzy_sensitivity': 80}, f)

def load_bibtex_fields():
    """
    Load BibTeX entry types and fields from the bibtexFields.json file.
    Updates global variables for entry types and fields.
    """
    global bibtex_info, BIB_ENTRY_TYPES, BIB_FIELDS
    with open(BIBTEX_FIELDS_FILE, 'r') as f:
        bibtex_info = json.load(f)
        BIB_ENTRY_TYPES = list(bibtex_info['entry_types'].keys())
        BIB_FIELDS = list(bibtex_info['fields'].keys())
        settings = load_settings()
        field_order = settings.get('field_order', [])
        if field_order:
            BIB_FIELDS = [f for f in field_order if f in BIB_FIELDS]
            BIB_FIELDS += [f for f in BIB_FIELDS if f not in field_order]
            seen = set()
            BIB_FIELDS = [x for x in BIB_FIELDS if not (x in seen or seen.add(x))]

match_options_all = ['exact', 'contains', 'case-sensitive', 'regex', 'fuzzy']

def load_db():
    """
    Load the bibliography database from the JSON file.
    Returns:
        dict: The loaded database.
    """
    with open(BIB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    """
    Save the bibliography database to the JSON file.
    Args:
        data (dict): The database to save.
    """
    with open(BIB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_settings():
    """
    Load user settings from the settings JSON file.
    Returns:
        dict: The loaded settings.
    """
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(settings):
    """
    Save user settings to the settings JSON file.
    Args:
        settings (dict): The settings to save.
    """
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

def entry_form_gui(
    mode="add",
    key=None,
    entry_data=None,
    on_save=None,
    on_cancel=None,
    parent=None,
    title=None,
    show_key=True
):
    """
    Show a form for adding or editing a bibliographic entry.

    Args:
        mode (str): "add" or "edit"
        key (str): Key of entry (for edit)
        entry_data (dict): Entry fields (for edit/import)
        on_save (callable): Callback(new_key, new_entry_dict)
        on_cancel (callable): Callback()
        parent (tk.Tk or tk.Toplevel): Parent window
        title (str): Window title
        show_key (bool): Show the key field (True for add/edit, False for import review)
    """
    load_bibtex_fields()
    win = tk.Toplevel(parent if parent else root)
    win.title(title or ("Edit Entry" if mode == "edit" else "Add Entry"))

    fields = {}
    field_labels = {}
    help_labels = {}

    row = 0
    if show_key:
        tk.Label(win, text="Citation Key *").grid(row=row, column=0, sticky='e')
        key_entry = tk.Entry(win, width=50)
        if mode == "edit" and key:
            key_entry.insert(0, key)
        elif entry_data and "key" in entry_data:
            key_entry.insert(0, entry_data["key"])
        key_entry.grid(row=row, column=1)
        tk.Label(win, text="(Unique identifier for this entry)").grid(row=row, column=2, sticky='w')
        row += 1
    else:
        key_entry = None

    # Entry type dropdown with help text
    tk.Label(win, text="Entry Type *").grid(row=row, column=0, sticky='e')
    entry_type_var = tk.StringVar(value=(entry_data.get('entry_type', 'article') if entry_data else "article"))
    entry_type_cb = ttk.Combobox(win, textvariable=entry_type_var, values=BIB_ENTRY_TYPES, state="readonly", width=47)
    entry_type_cb.grid(row=row, column=1)
    entry_type_help = tk.Label(win, text=bibtex_info['entry_types'][entry_type_var.get()]['description'], wraplength=400, fg="gray")
    entry_type_help.grid(row=row, column=2, sticky='w')
    row += 1

    def update_fields(*args):
        """
        Update the form fields and help texts based on the selected entry type.
        """
        entry_type = entry_type_var.get()
        entry_type_help.config(text=bibtex_info['entry_types'][entry_type]['description'])
        required = set([f.replace(' or ', '/').split('/')[0] for f in bibtex_info['entry_types'][entry_type]['required']])
        optional = set([f.replace(' or ', '/').split('/')[0] for f in bibtex_info['entry_types'][entry_type]['optional']])
        for field in BIB_FIELDS:
            is_required = field in required
            is_optional = field in optional
            label = field_labels[field]
            help_label = help_labels[field]
            label.config(text=f"{field.capitalize()}{' *' if is_required else ''}")
            if is_required or is_optional:
                fields[field].config(state='normal')
            else:
                fields[field].delete(0, tk.END)
                fields[field].config(state='disabled')
            help_label.config(text=bibtex_info['fields'].get(field, ""), fg="gray")

    entry_type_var.trace_add('write', update_fields)

    for i, field in enumerate(BIB_FIELDS):
        label = tk.Label(win, text=field.capitalize())
        label.grid(row=row+i, column=0, sticky='e')
        ent = tk.Entry(win, width=50)
        if entry_data and field in entry_data:
            ent.insert(0, entry_data[field])
        ent.grid(row=row+i, column=1)
        help_label = tk.Label(win, text=bibtex_info['fields'].get(field, ""), wraplength=400, fg="gray")
        help_label.grid(row=row+i, column=2, sticky='w')
        fields[field] = ent
        field_labels[field] = label
        help_labels[field] = help_label

    update_fields()

    def save():
        """
        Validate and save the entry, calling the on_save callback if provided.
        """
        db = load_db()
        new_key = key_entry.get().strip() if key_entry else (key if key else "")
        entry_type = entry_type_var.get().strip()
        required_fields = bibtex_info['entry_types'][entry_type]['required']
        required_flat = []
        for rf in required_fields:
            if ' or ' in rf:
                required_flat.append(rf.split(' or ')[0])
            elif ' and/or ' in rf:
                required_flat.append(rf.split(' and/or ')[0])
            else:
                required_flat.append(rf)
        missing = []
        for rf in required_flat:
            rf = rf.strip()
            if rf == "key":
                continue
            if not fields[rf].get().strip():
                missing.append(rf)
        if show_key and not new_key:
            messagebox.showerror("Error", "Please enter a value for 'Key'.")
            return
        if not entry_type:
            messagebox.showerror("Error", "Please select an entry type.")
            return
        if mode == "add" and show_key and new_key in db:
            messagebox.showerror("Error", "Key already exists")
            return
        if missing:
            msg = f"The following required fields are empty: {', '.join(missing)}.\nDo you want to continue saving anyway?"
            if not messagebox.askyesno("Missing Required Fields", msg):
                return
        new_entry = {field: ent.get() for field, ent in fields.items() if ent.get() and ent['state'] == 'normal'}
        new_entry['entry_type'] = entry_type
        if on_save:
            on_save(new_key, new_entry)
        win.destroy()

    def cancel():
        """
        Cancel the form and call the on_cancel callback if provided.
        """
        if on_cancel:
            on_cancel()
        win.destroy()

    btn_row = row + len(BIB_FIELDS)
    tk.Button(win, text="Save Entry" if mode == "add" else "Save Changes", command=save).grid(row=btn_row, column=0)
    tk.Button(win, text="Cancel", command=cancel).grid(row=btn_row, column=1)

    win.grab_set()
    win.focus_set()
    win.wait_window()

def add_entry_gui():
    """
    Open the add entry form and save the new entry to the database.
    """
    def on_save(new_key, new_entry):
        db = load_db()
        db[new_key] = new_entry
        save_db(db)
        messagebox.showinfo("Success", "Entry added successfully")
    entry_form_gui(mode="add", on_save=on_save, title="Add Entry")

def edit_entry_gui(key):
    """
    Open the edit entry form for the given key and save changes to the database.
    Args:
        key (str): The key of the entry to edit.
    """
    db = load_db()
    if key not in db:
        messagebox.showerror("Error", "Key not found")
        return
    entry = db[key]
    def on_save(new_key, new_entry):
        db2 = load_db()
        if new_key != key and new_key in db2:
            messagebox.showerror("Error", "Key already exists.")
            return
        if new_key != key:
            del db2[key]
        db2[new_key] = new_entry
        save_db(db2)
        messagebox.showinfo("Updated", "Entry updated successfully.")
    entry_form_gui(mode="edit", key=key, entry_data=entry, on_save=on_save, title=f"Edit Entry: {key}")

def import_entries():
    """
    Import BibTeX entries from input.txt, review each entry, and add to the database.
    Checks for duplicate keys and duplicate title/author combinations.
    """
    if not os.path.exists(INPUT_FILE):
        messagebox.showerror("Error", "input.txt file not found.")
        return
    with open(INPUT_FILE, 'r') as f:
        lines = [line.rstrip() for line in f]

    parsed_entries = []
    entry = {}
    key = None
    entry_type = None
    inside_entry = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('@'):
            inside_entry = True
            if entry and key:
                entry['entry_type'] = entry_type
                parsed_entries.append((key, entry.copy()))
            entry = {}
            try:
                entry_type, rest = line[1:].split('{', 1)
                key = rest.split(',', 1)[0].strip()
            except Exception:
                entry_type = "article"
                key = None
        elif inside_entry and '=' in line:
            try:
                field, value = line.split('=', 1)
                field = field.strip().lower()
                value = value.strip().strip(',').strip('{}').strip()
                entry[field] = value
            except Exception:
                continue
        elif inside_entry and line.startswith('}'):
            if entry and key:
                entry['entry_type'] = entry_type
                parsed_entries.append((key, entry.copy()))
            entry = {}
            key = None
            entry_type = None
            inside_entry = False

    if entry and key:
        entry['entry_type'] = entry_type
        parsed_entries.append((key, entry.copy()))

    if not parsed_entries:
        messagebox.showinfo("Import", "No entries found in input.txt.")
        return

    messagebox.showinfo("Import", f"Parsed {len(parsed_entries)} entries from input.txt. You will now review each entry before saving.")

    db = load_db()
    idx = [0]

    def show_entry_form():
        """
        Show the entry form for each imported entry, allowing review and editing.
        """
        if idx[0] >= len(parsed_entries):
            save_db(db)
            messagebox.showinfo("Import", "All entries processed and saved.")
            return

        key, entry = parsed_entries[idx[0]]

        def on_save(new_key, new_entry):
            # Duplicate key check
            if new_key in db:
                res = messagebox.askyesno("Duplicate Key", f"An entry with key '{new_key}' already exists. Do you want to modify this entry and save as new?")
                if not res:
                    idx[0] += 1
                    show_entry_form()
                    return
            # Duplicate title/author check
            new_title = new_entry.get('title', '').strip().lower()
            new_author = new_entry.get('author', '').strip().lower()
            for k, e in db.items():
                if k == new_key:
                    continue
                if e.get('title', '').strip().lower() == new_title and e.get('author', '').strip().lower() == new_author and new_title and new_author:
                    res = messagebox.askyesno("Duplicate Entry", f"An entry with the same title and author already exists (key: {k}). Do you want to modify this entry and save as new?")
                    if not res:
                        idx[0] += 1
                        show_entry_form()
                        return
            db[new_key] = new_entry
            idx[0] += 1
            show_entry_form()

        def on_cancel():
            idx[0] += 1
            show_entry_form()

        entry_form_gui(
            mode="add",
            key=key,
            entry_data=entry,
            on_save=on_save,
            on_cancel=on_cancel,
            title=f"Review Imported Entry {idx[0]+1} of {len(parsed_entries)}"
        )

    show_entry_form()

def search_entries_gui():
    """
    Open the search window to search for entries by field and query.
    Supports exact, contains, case-sensitive, regex, and fuzzy search.
    """
    settings = load_settings()
    search_win = tk.Toplevel(root)
    search_win.title("Search Entries")
    search_win.geometry("1100x700")

    tk.Label(search_win, text="Search Field:").grid(row=0, column=0, sticky="w")
    field_cb = ttk.Combobox(search_win, values=BIB_FIELDS)
    field_cb.grid(row=0, column=1, sticky="ew", columnspan=3)

    tk.Label(search_win, text="Query:").grid(row=1, column=0, sticky="w")
    query_ent = tk.Entry(search_win, width=80)
    query_ent.grid(row=1, column=1, sticky="ew", columnspan=3)

    match_vars = {
        'exact': tk.BooleanVar(),
        'contains': tk.BooleanVar(),
        'case-sensitive': tk.BooleanVar(),
        'regex': tk.BooleanVar(),
        'fuzzy': tk.BooleanVar()
    }

    def on_exact_checked():
        if match_vars['exact'].get():
            match_vars['contains'].set(False)

    def on_contains_checked():
        if match_vars['contains'].get():
            match_vars['exact'].set(False)

    match_vars['exact'].set('exact' in settings.get('match_options', []))
    match_vars['contains'].set('contains' in settings.get('match_options', []))
    match_vars['case-sensitive'].set('case-sensitive' in settings.get('match_options', []))
    match_vars['regex'].set('regex' in settings.get('match_options', []))
    match_vars['fuzzy'].set('fuzzy' in settings.get('match_options', []))

    tk.Checkbutton(search_win, text='exact', variable=match_vars['exact'], command=on_exact_checked).grid(row=2, column=0, sticky="w")
    tk.Checkbutton(search_win, text='contains', variable=match_vars['contains'], command=on_contains_checked).grid(row=2, column=1, sticky="w")
    tk.Checkbutton(search_win, text='case-sensitive', variable=match_vars['case-sensitive']).grid(row=2, column=2, sticky="w")
    tk.Checkbutton(search_win, text='regex', variable=match_vars['regex']).grid(row=2, column=3, sticky="w")
    tk.Checkbutton(search_win, text='fuzzy', variable=match_vars['fuzzy']).grid(row=2, column=4, sticky="w")

    tk.Label(search_win, text="Fuzzy Sensitivity (%):").grid(row=3, column=0, sticky='e')
    fuzzy_slider = tk.Scale(search_win, from_=0, to=100, orient='horizontal')
    fuzzy_slider.set(settings.get('fuzzy_sensitivity', 80))
    fuzzy_slider.grid(row=3, column=1, sticky="ew", columnspan=3)

    tk.Button(search_win, text="Search", command=lambda: search()).grid(row=4, column=0, pady=5, sticky="ew")
    tk.Button(search_win, text="Edit Entry", command=lambda: edit_prompt()).grid(row=4, column=1, pady=5, sticky="ew")

    result_box = tk.Text(search_win, height=30, width=140, wrap="none")
    result_box.grid(row=5, column=0, columnspan=5, sticky="nsew")

    x_scroll = tk.Scrollbar(search_win, orient='horizontal', command=result_box.xview)
    x_scroll.grid(row=6, column=0, columnspan=5, sticky='ew')
    y_scroll = tk.Scrollbar(search_win, orient='vertical', command=result_box.yview)
    y_scroll.grid(row=5, column=5, sticky='ns')
    result_box.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

    search_win.grid_rowconfigure(5, weight=1)
    for col in range(5):
        search_win.grid_columnconfigure(col, weight=1)

    results = []

    def search(event=None):
        """
        Perform the search and display results in the result box.
        """
        db = load_db()
        field = field_cb.get()
        query = query_ent.get()
        selected_matches = [k for k, v in match_vars.items() if v.get()]
        fuzzy_sensitivity = fuzzy_slider.get() / 100.0

        settings['match_options'] = selected_matches
        settings['fuzzy_sensitivity'] = int(fuzzy_slider.get())
        save_settings(settings)

        result_box.delete(1.0, tk.END)
        results.clear()

        for key, entry in db.items():
            value = entry.get(field, '')
            matched = False
            preview_match = False

            if 'case-sensitive' in selected_matches:
                if 'exact' in selected_matches and value == query:
                    matched = True
                elif 'contains' in selected_matches and query in value:
                    matched = True
            else:
                if 'exact' in selected_matches and value.lower() == query.lower():
                    matched = True
                elif 'contains' in selected_matches and query.lower() in value.lower():
                    matched = True

            if 'regex' in selected_matches:
                try:
                    if re.search(query, value):
                        matched = True
                except re.error:
                    pass

            if 'fuzzy' in selected_matches:
                similarity = SequenceMatcher(None, value.lower(), query.lower()).ratio()
                if similarity >= fuzzy_sensitivity:
                    matched = True
                    preview_match = True

            if matched:
                results.append((key, entry, value if preview_match else ''))

        if not results:
            result_box.insert(tk.END, "No matching entries found.\n")
            return

        for i, (k, entry, preview) in enumerate(results):
            entry_type = entry.get('entry_type', 'article')
            bibtex_lines = []
            bibtex_lines.append(f"@{entry_type}{{{k},")
            for f in settings['field_order']:
                if f in entry:
                    bibtex_lines.append(f"\t{f}\t\t = {{{entry[f]}}},")
            bibtex_lines[-1] = bibtex_lines[-1].rstrip(',')
            bibtex_lines.append("}")
            bibtex_entry = "\n".join(bibtex_lines)
            result_box.insert(tk.END, f"Result {i+1}:\n{bibtex_entry}\n")
            if preview:
                result_box.insert(tk.END, f"Preview Match: {preview}\n")
            result_box.insert(tk.END, "\n")

    def edit_prompt():
        """
        Prompt the user to select a result to edit, then open the edit form.
        """
        if not results:
            messagebox.showerror("Error", "No results to edit.")
            return
        if len(results) > 1:
            cmd = simpledialog.askstring("Edit Entry", "Enter the result number to edit:")
            if cmd and cmd.isdigit():
                try:
                    idx = int(cmd) - 1
                    if 0 <= idx < len(results):
                        key = results[idx][0]
                        edit_entry_gui(key)
                    else:
                        messagebox.showerror("Error", "Invalid entry number.")
                except ValueError:
                    messagebox.showerror("Error", "Invalid input.")
            else:
                messagebox.showerror("Error", "Invalid input.")
        else:
            key = results[0][0]
            edit_entry_gui(key)

    query_ent.bind('<Return>', search)

def browse_entries_gui():
    """
    Open a window to browse all entries in a table.
    Double-click an entry to edit it.
    """
    db = load_db()
    browse_win = tk.Toplevel(root)
    browse_win.title("Browse Bibliography Entries")
    browse_win.geometry("1200x600")

    columns = ("#", "Authors", "Title", "Year", "Source")
    tree = ttk.Treeview(browse_win, columns=columns, show="headings", height=25)
    for col in columns:
        tree.heading(col, text=col)
        if col == "#":
            tree.column(col, width=50, anchor="center")
        else:
            tree.column(col, width=250, anchor="w")

    for idx, (key, entry) in enumerate(db.items(), 1):
        authors = entry.get("author", "")
        title = entry.get("title", "")
        year = entry.get("year", "")
        source = (
            entry.get("journal") or
            entry.get("booktitle") or
            entry.get("conference") or
            entry.get("publisher") or
            entry.get("organization") or
            ""
        )
        tree.insert("", "end", iid=key, values=(idx, authors, title, year, source))

    tree.pack(fill="both", expand=True)

    vsb = ttk.Scrollbar(browse_win, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    def on_double_click(event):
        item = tree.identify_row(event.y)
        if item:
            edit_entry_gui(item)

    tree.bind("<Double-1>", on_double_click)

def main():
    """
    Main function to initialize files, load database, and start the GUI.
    """
    init_files()
    global db, root
    db = load_db()
    root = tk.Tk()
    root.title("Bibliography Manager")

    menu = tk.Menu(root)
    root.config(menu=menu)

    file_menu = tk.Menu(menu)
    menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Add Entry", command=add_entry_gui)
    file_menu.add_command(label="Search Entries", command=search_entries_gui)
    file_menu.add_command(label="Browse", command=browse_entries_gui)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)

    adv_menu = tk.Menu(menu)
    menu.add_cascade(label="Advanced Features", menu=adv_menu)
    adv_menu.add_command(label="Import from input.txt", command=import_entries)

    welcome_label = tk.Label(root, text=f"Welcome to Bibliography Manager!\nTotal Entries: {len(db)}", font=('Arial', 14))
    welcome_label.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
