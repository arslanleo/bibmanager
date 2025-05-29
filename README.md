# Bibliography Manager

## Overview

**Bibliography Manager** is a graphical user interface (GUI) application for managing bibliographic references, such as journal articles, books, conference papers, and more. It is designed to help researchers, students, and academics organize, search, edit, and import their bibliography entries in a user-friendly way.

The application is built using Python and Tkinter, and stores all data in JSON files for easy portability and editing.

There's still a lot of features that can be added to this, and I will keep adding stuff.

---

## Features

### 1. Add New Entry
- **Menu:** File → Add Entry
- Opens a form to add a new bibliographic entry.
- Entry type (e.g., article, book, inproceedings, etc.) is selected from a dropdown.
- Required fields for the selected entry type are marked with an asterisk (*).
- Field descriptions and help texts are shown for each field.
- The program checks for missing required fields and prompts the user before saving.
- Prevents duplicate keys and warns about duplicate title/author combinations.

### 2. Edit Existing Entry
- **How:** Double-click an entry in the Browse table, or use the Search/Edit feature.
- Opens the same form as Add Entry, pre-filled with the entry's data.
- Allows editing all fields, including changing the entry type.
- Checks for duplicate keys and missing required fields.

### 3. Browse All Entries
- **Menu:** File → Browse
- Displays all entries in a table with columns: Serial Number (#), Authors, Title, Year, and Source (Journal/Conference/Publisher/Booktitle).
- Double-click any row to open the edit form for that entry.

### 4. Search Entries
- **Menu:** File → Search Entries
- Search for entries by any field using various match options:
  - Exact, Contains, Case-sensitive, Regex, Fuzzy (with adjustable sensitivity).
- Results are shown in BibTeX format.
- Edit any result directly from the search window.

### 5. Import Entries from BibTeX File
- **Menu:** Advanced Features → Import from input.txt
- Reads BibTeX-formatted entries from `input.txt`.
- Parses all entries and presents each one in the entry form for review and editing.
- Checks for duplicate keys and duplicate title/author combinations before saving.
- User can choose to save or discard each imported entry.

---

## File Structure and Required Files

### 1. `main.py`
- The main application script containing all GUI logic, data handling, and user interaction.

### 2. `bibliography_db.json`
- The main database file where all bibliography entries are stored in JSON format.
- Automatically created if it does not exist.

### 3. `settings.json`
- Stores user settings such as field order, search match options, and fuzzy search sensitivity.
- Automatically created if it does not exist.

### 4. `input.txt`
- Used for importing entries.
- Should contain BibTeX-formatted entries (e.g., exported from Google Scholar, Zotero, etc.).
- Each entry is parsed and reviewed before being added to the database.

### 5. `bibtexFields.json`
- Contains metadata about all supported BibTeX entry types and fields.
- For each entry type, lists required and optional fields and provides a description.
- For each field, provides a description/help text.
- Used to dynamically generate forms and help texts in the GUI.

---

## How to Use

1. **Start the application** by running `main.py`.
2. **Add entries** using the File → Add Entry menu.
3. **Browse or search** your bibliography using the File → Browse or File → Search Entries menus.
4. **Edit entries** by double-clicking them in the Browse table or from search results.
5. **Import entries** by placing a BibTeX file in `input.txt` and using Advanced Features → Import from input.txt.
6. **All data is saved automatically** in `bibliography_db.json`.

---

## Notes

- The application is cross-platform and works on Windows, macOS, and Linux (requires Python and Tkinter).
- All data is stored locally; there is no cloud sync or online dependency.
- The BibTeX field and entry type definitions can be customized by editing `bibtexFields.json`.

---

## License

This project is open source and free to use.

---
