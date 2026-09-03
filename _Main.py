import os, tempfile, threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from _thaiID_blacklist_check import load_blacklist, main_polling, normalize
    from decoder import decrypt_file
    from encoder import encrypt_file
    from generatekey import generate_keys
except ImportError as e:
    print(f"Error importing backend files: {e}")

# ==========================================
# COLOR PALETTE & STYLES (Navy Blue Theme)
# ==========================================
COLOR_BG_DARK = "#0B192C"       # Deep Navy Background
COLOR_BG_CARD = "#1E3E62"       # Lighter Navy Accent
COLOR_FG_WHITE = "#FFFFFF"      # Crisp Text
COLOR_FG_LIGHT = "#E0E0E0"      # Off-white Text
COLOR_BTN_MAIN = "#00adb5"      # Cyan Accent Button
COLOR_BTN_HOVER = "#008c93"

# Status Background Colors for Card Reader
COLOR_STATUS_GRAY = "#6c757d"    # Reader Disconnected
COLOR_STATUS_BLUE = "#0275d8"    # Reader Connected / Waiting
COLOR_STATUS_RED = "#d9534f"     # Blacklist
COLOR_STATUS_YELLOW = "#f0ad4e"  # Watchlist
COLOR_STATUS_GREEN = "#5cb85c"   # Whitelist / Clear / Decryption Success


class ThaiIDBlacklistApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Thai ID Blacklist Checker")
        self.geometry("900x700")
        self.configure(bg=COLOR_BG_DARK)

        # Application State
        self.temp_excel_file = None
        self.id_records = {}
        self.name_records = {}
        self.polling_thread = None
        self.stop_polling_event = threading.Event()

        # Build Main Frame Container
        self.container = tk.Frame(self, bg=COLOR_BG_DARK)
        self.container.pack(fill="both", expand=True)

        # Show initial view
        self.show_main_menu()

    def clear_container(self):
        """Removes all widgets from container before switching views."""
        for widget in self.container.winfo_children():
            widget.destroy()

    # ==========================================
    # VIEW 1: MAIN MENU
    # ==========================================
    def show_main_menu(self):
        self.clear_container()

        # Top-left container for "Encrypt File" button
        top_bar = tk.Frame(self.container, bg=COLOR_BG_DARK)
        top_bar.pack(anchor="nw", padx=15, pady=15, fill="x")

        btn_encrypt_page = tk.Button(
            top_bar,
            text="Encrypt File",
            font=("Helvetica", 10, "bold"),
            bg=COLOR_BTN_MAIN,
            fg="white",
            activebackground=COLOR_BTN_HOVER,
            activeforeground="white",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.show_encrypt_page
        )
        btn_encrypt_page.pack(side="left")

        # Center layout container
        center_frame = tk.Frame(self.container, bg=COLOR_BG_DARK)
        center_frame.pack(expand=True)

        lbl_title = tk.Label(
            center_frame,
            text="Thai National ID Blacklist System",
            font=("Helvetica", 20, "bold"),
            bg=COLOR_BG_DARK,
            fg=COLOR_FG_WHITE
        )
        lbl_title.pack(pady=(0, 30))

        btn_upload = tk.Button(
            center_frame,
            text="Upload .enc File",
            font=("Helvetica", 14, "bold"),
            bg=COLOR_BG_CARD,
            fg=COLOR_FG_WHITE,
            activebackground="#2B5278",
            activeforeground="white",
            bd=2,
            relief="groove",
            padx=40,
            pady=20,
            cursor="hand2",
            command=self.handle_upload_enc
        )
        btn_upload.pack()

    # ==========================================
    # VIEW 2: ENCRYPT PAGE
    # ==========================================
    def show_encrypt_page(self):
        self.clear_container()

        # Header Frame
        header_frame = tk.Frame(self.container, bg=COLOR_BG_DARK)
        header_frame.pack(fill="x", padx=20, pady=15)

        btn_back = tk.Button(
            header_frame,
            text="<- Back to Main Menu",
            font=("Helvetica", 10, "bold"),
            bg=COLOR_BG_CARD,
            fg=COLOR_FG_WHITE,
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.show_main_menu
        )
        btn_back.pack(side="left")

        lbl_title = tk.Label(
            header_frame,
            text="Encryption & Key Management Tool",
            font=("Helvetica", 16, "bold"),
            bg=COLOR_BG_DARK,
            fg=COLOR_FG_WHITE
        )
        lbl_title.pack(side="right")

        # Content Card Frame
        card_frame = tk.Frame(self.container, bg=COLOR_BG_CARD, padx=30, pady=30)
        card_frame.pack(pady=40, padx=50, fill="both")

        # Section 1: Generate Key
        lbl_sec1 = tk.Label(card_frame, text="1. Key Generation", font=("Helvetica", 12, "bold"), bg=COLOR_BG_CARD, fg=COLOR_FG_WHITE)
        lbl_sec1.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(card_frame, text="Key Pair Name:", font=("Helvetica", 10), bg=COLOR_BG_CARD, fg=COLOR_FG_LIGHT).grid(row=1, column=0, sticky="w")
        entry_key_name = tk.Entry(card_frame, font=("Helvetica", 11), width=25)
        entry_key_name.grid(row=1, column=1, sticky="w", padx=10)

        btn_gen_key = tk.Button(
            card_frame, text="Generate Key Pair", font=("Helvetica", 10, "bold"), bg=COLOR_BTN_MAIN, fg="white", bd=0, padx=10, pady=4, cursor="hand2",
            command=lambda: self.handle_generate_keys(entry_key_name.get())
        )
        btn_gen_key.grid(row=1, column=2, padx=10)

        # Divider
        ttk.Separator(card_frame, orient="horizontal").grid(row=2, column=0, columnspan=3, sticky="ew", pady=20)

        # Section 2: Encrypt File
        lbl_sec2 = tk.Label(card_frame, text="2. Encrypt Blacklist File", font=("Helvetica", 12, "bold"), bg=COLOR_BG_CARD, fg=COLOR_FG_WHITE)
        lbl_sec2.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 10))

        selected_file_var = tk.StringVar(value="No file selected...")
        
        btn_select_file = tk.Button(
            card_frame, text="Select File (.xlsx)", font=("Helvetica", 10), bg=COLOR_BG_DARK, fg=COLOR_FG_WHITE, bd=1, padx=10, pady=4, cursor="hand2",
            command=lambda: self.handle_select_file(selected_file_var)
        )
        btn_select_file.grid(row=4, column=0, sticky="w")

        lbl_file_path = tk.Label(card_frame, textvariable=selected_file_var, font=("Helvetica", 10, "italic"), bg=COLOR_BG_CARD, fg=COLOR_FG_LIGHT)
        lbl_file_path.grid(row=4, column=1, columnspan=2, sticky="w", padx=10)

        btn_run_encrypt = tk.Button(
            card_frame, text="Encrypt File Now", font=("Helvetica", 11, "bold"), bg=COLOR_BTN_MAIN, fg="white", bd=0, padx=20, pady=8, cursor="hand2",
            command=lambda: self.handle_encrypt_process(selected_file_var.get())
        )
        btn_run_encrypt.grid(row=5, column=0, columnspan=3, pady=(25, 0))

    # ==========================================
    # VIEW 3: MAIN WORKING PAGE (CARD MONITOR + SEARCH)
    # ==========================================
    def show_working_page(self):
        self.clear_container()

        # Header Frame with Exit Button & Search Bar
        header = tk.Frame(self.container, bg=COLOR_BG_DARK, padx=15, pady=10)
        header.pack(fill="x")

        btn_exit = tk.Button(
            header,
            text="Exit to Main Menu",
            font=("Helvetica", 10, "bold"),
            bg=COLOR_BG_CARD,
            fg=COLOR_FG_WHITE,
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.cleanup_and_exit
        )
        btn_exit.pack(side="left")

        # Search Bar Frame (Right side of header)
        search_frame = tk.Frame(header, bg=COLOR_BG_DARK)
        search_frame.pack(side="right")

        tk.Label(
            search_frame,
            text="Search:",
            font=("Helvetica", 10, "bold"),
            bg=COLOR_BG_DARK,
            fg=COLOR_FG_WHITE
        ).pack(side="left", padx=(0, 5))

        self.search_entry = tk.Entry(search_frame, font=("Helvetica", 10), width=22)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda event: self.handle_manual_search())

        btn_search = tk.Button(
            search_frame,
            text="Lookup",
            font=("Helvetica", 9, "bold"),
            bg=COLOR_BTN_MAIN,
            fg="white",
            bd=0,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.handle_manual_search
        )
        btn_search.pack(side="left", padx=(0, 5))

        btn_clear_search = tk.Button(
            search_frame,
            text="Clear",
            font=("Helvetica", 9),
            bg=COLOR_BG_CARD,
            fg=COLOR_FG_WHITE,
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.clear_manual_search
        )
        btn_clear_search.pack(side="left")

        # Main Status Banner (Grey, Yellow, Red, Green dynamically)
        self.status_banner = tk.Label(
            self.container,
            text="INITIALIZING CARD READER...",
            font=("Helvetica", 16, "bold"),
            bg=COLOR_STATUS_GRAY,
            fg=COLOR_FG_WHITE,
            pady=15
        )
        self.status_banner.pack(fill="x", padx=20, pady=10)

        # Two Column Display Layout
        details_container = tk.Frame(self.container, bg=COLOR_BG_DARK, padx=20, pady=10)
        details_container.pack(fill="both", expand=True)

        # Left Column: Card Details
        card_info_group = tk.LabelFrame(
            details_container, text=" Thai ID Card Information ", font=("Helvetica", 11, "bold"), bg=COLOR_BG_DARK, fg=COLOR_FG_WHITE, padx=15, pady=15
        )
        card_info_group.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.card_labels = {}
        card_fields = [
            ("CID", "CID:"),
            ("TH Fullname", "Thai Name:"),
            ("EN Fullname", "English Name:"),
            ("Date of Birth", "Date of Birth:"),
            ("Gender", "Gender:"),
            ("Card Issuer", "Issuer:"),
            ("Issue Date", "Issue Date:"),
            ("Expire Date", "Expire Date:"),
            ("Address", "Address:")
        ]

        for idx, (key, title) in enumerate(card_fields):
            tk.Label(card_info_group, text=title, font=("Helvetica", 10, "bold"), bg=COLOR_BG_DARK, fg=COLOR_FG_LIGHT).grid(row=idx, column=0, sticky="nw", pady=2)
            val_lbl = tk.Label(card_info_group, text="-", font=("Helvetica", 10), bg=COLOR_BG_DARK, fg=COLOR_FG_WHITE, anchor="w", justify="left", wraplength=220)
            val_lbl.grid(row=idx, column=1, sticky="nw", padx=10, pady=2)
            self.card_labels[key] = val_lbl

        # Right Column: Blacklist / Allegation Details
        bl_info_group = tk.LabelFrame(
            details_container, text=" Verification Results ", font=("Helvetica", 11, "bold"), bg=COLOR_BG_DARK, fg=COLOR_FG_WHITE, padx=15, pady=15
        )
        bl_info_group.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.bl_labels = {}
        bl_fields = [
            ("reason", "Match Reason:"),
            ("status", "Status:"),
            ("area", "Area:"),
            ("caught_area", "Caught Area:"),
            ("occurance_date", "Occurrence Date:"),
            ("company_name", "Company Name:"),
            ("department", "Department:"),
            ("card_number", "Card No.:"),
            ("position", "Position:"),
            ("affiliation", "Affiliation:"),
            ("allegation", "Allegation:"),
            ("start_date", "Start Date:"),
            ("due_date", "Due Date:"),
            ("document", "Document:"),
            ("detail", "Detail:")
        ]

        for idx, (key, title) in enumerate(bl_fields):
            tk.Label(bl_info_group, text=title, font=("Helvetica", 10, "bold"), bg=COLOR_BG_DARK, fg=COLOR_FG_LIGHT).grid(row=idx, column=0, sticky="nw", pady=4)
            val_lbl = tk.Label(bl_info_group, text="-", font=("Helvetica", 10), bg=COLOR_BG_DARK, fg=COLOR_FG_WHITE, anchor="w", justify="left", wraplength=220)
            val_lbl.grid(row=idx, column=1, sticky="nw", padx=10, pady=4)
            self.bl_labels[key] = val_lbl

        # Start Card Listener Thread
        self.start_card_polling()

    # ==========================================
    # LOGIC: SEARCH BAR HANDLER
    # ==========================================
    def handle_manual_search(self):
        query = self.search_entry.get().strip()
        if not query:
            return

        self.clear_display_info()
        record = None
        match_reason = ""
        
        # Clean non-digit characters without regex
        clean_query_id = "".join(char for char in query if char.isdigit())

        # 1. Match by ID Card (digits-only comparison)
        if clean_query_id and clean_query_id in self.id_records:
            record = self.id_records[clean_query_id]
            match_reason = f"Manual Lookup by ID → {clean_query_id}"
        else:
            # 2. Match by Name
            normalized_query = normalize(query)
            if normalized_query in self.name_records:
                record = self.name_records[normalized_query]
                match_reason = f"Manual Lookup by Name → {query}"

        if record:
            # Display ID or Name on the Card Info Panel
            self.card_labels["CID"].config(text=record.get("id") or "-")
            self.card_labels["TH Fullname"].config(text=record.get("name") or "-")

            # Display Verification Results
            self.bl_labels["reason"].config(text=match_reason)

            for key in self.bl_labels:
                if key != "reason":
                    self.bl_labels[key].config(
                        text=record.get(key, "-") or "-"
                    )

            # Dynamic Banner Status Color
            status_str = str(record.get("status", "")).strip().lower()
            if "watch" in status_str or "warning" in status_str:
                self.status_banner.config(
                    bg=COLOR_STATUS_YELLOW,
                    fg="black",
                    text=f"MANUAL MATCH: {record.get('status', 'WATCHLIST').upper()}"
                )
            else:
                self.status_banner.config(
                    bg=COLOR_STATUS_RED,
                    fg="white",
                    text=f"MANUAL MATCH: {record.get('status', 'BLACKLIST').upper()}"
                )
        else:
            # Display as WHITELIST (Green) when no record is found
            self.status_banner.config(
                bg=COLOR_STATUS_GREEN,
                fg=COLOR_FG_WHITE,
                text=f"WHITELIST — NO RECORD FOUND FOR: '{query}'"
            )
            self.bl_labels["reason"].config(text=f"Manual Search: '{query}'")
            self.bl_labels["status"].config(text="CLEAR / WHITELIST")

    def clear_manual_search(self):
        self.search_entry.delete(0, tk.END)
        self.clear_display_info()
        self.status_banner.config(
            bg=COLOR_STATUS_BLUE,
            fg=COLOR_FG_WHITE,
            text="READER DETECTED — WAITING FOR CARD..."
        )

    # ==========================================
    # LOGIC: ENCRYPTION & DECRYPTION HANDLERS
    # ==========================================
    def handle_generate_keys(self, key_name):
        if not key_name.strip():
            messagebox.showwarning("Input Error", "Please enter a valid key pair name.")
            return
        try:
            generate_keys(key_name)
            messagebox.showinfo("Success", f"Keys for '{key_name}' generated successfully!")
        except Exception as e:
            messagebox.showerror("Key Generation Error", str(e))

    def handle_select_file(self, target_var):
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if path:
            target_var.set(path)

    def handle_encrypt_process(self, input_path):
        if not os.path.exists(input_path):
            messagebox.showwarning(
                "Warning",
                "Please select a valid .xlsx file first."
            )
            return

        default_filename = os.path.splitext(os.path.basename(input_path))[0] + ".enc"

        out_path = filedialog.asksaveasfilename(
            title="Save Encrypted File",
            initialfile=default_filename,
            defaultextension=".enc",
            filetypes=[("Encrypted File", "*.enc")]
        )

        if not out_path:
            return

        try:
            encrypt_file(input_path, out_path)

            messagebox.showinfo(
                "Success",
                f"Encrypted file saved to:\n{out_path}"
            )

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror(
                "Encryption Failed",
                error_details
            )

    def handle_upload_enc(self):
        enc_file_path = filedialog.askopenfilename(
            title="Select Encrypted File",
            filetypes=[("Encrypted Files", "*.enc")]
        )
        if not enc_file_path:
            return

        # Attempt Decryption using backend rules
        try:
            # Create a secure temporary file to receive decrypted contents
            temp_fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
            os.close(temp_fd)

            decrypt_file(enc_file_path, temp_path)

            # Load Blacklist directly into memory
            self.id_records, self.name_records = load_blacklist(temp_path)
            self.temp_excel_file = temp_path

            # Navigate to Working Monitor Screen
            self.show_working_page()

        except Exception as e:
            messagebox.showerror("Decryption / Load Failed", f"Could not load .enc file:\n{str(e)}")

    # ==========================================
    # LOGIC: SMART CARD POLLING & UI UPDATE
    # ==========================================
    def start_card_polling(self):
        self.stop_polling_event.clear()
        self.polling_thread = threading.Thread(
            target=main_polling,
            args=(self.id_records, self.name_records, self.card_callback, self.stop_polling_event),
            daemon=True
        )
        self.polling_thread.start()

    def card_callback(self, event_type, data):
        """Thread-safe UI updates dispatched to the Tkinter thread."""
        self.after(0, self.update_working_ui, event_type, data)

    def update_working_ui(self, event_type, data):
        # Ignore card reader background events if user is currently searching manually
        if hasattr(self, 'search_entry') and self.search_entry.get().strip():
            return

        if event_type == "NO_READER":
            self.status_banner.config(bg=COLOR_STATUS_GRAY, text="NO READER DETECTED")
            self.clear_display_info()

        elif event_type in ["WAITING_CARD", "NO_CARD"]:
            self.status_banner.config(bg=COLOR_STATUS_BLUE, text="READER DETECTED — WAITING FOR CARD...")
            self.clear_display_info()

        elif event_type == "CARD_READ":
            card_data = data.get("card_data", {})
            is_match = data.get("is_match", False)
            result = data.get("result", {})

            # Populate Card Details
            for key, lbl in self.card_labels.items():
                lbl.config(text=card_data.get(key, "-"))

            # Populate Blacklist Details
            for key, lbl in self.bl_labels.items():
                lbl.config(text=result.get(key, "-") if is_match else "-")

            # Determine UI Theme/Color Status based on backend return logic
            if is_match:
                status_str = str(result.get("status", "")).strip().lower()
                if "watch" in status_str or "warning" in status_str:
                    # Watchlist -> Yellow background
                    self.status_banner.config(
                        bg=COLOR_STATUS_YELLOW,
                        fg="black",
                        text=f"MATCH DETECTED: {result.get('status', 'WATCHLIST').upper()}"
                    )
                else:
                    # Default match / Blacklist -> Red background
                    self.status_banner.config(
                        bg=COLOR_STATUS_RED,
                        fg="white",
                        text=f"WARNING: {result.get('status', 'BLACKLIST').upper()}"
                    )
            else:
                # Clear status -> Green background
                self.status_banner.config(
                    bg=COLOR_STATUS_GREEN,
                    fg="white",
                    text="CLEAR — NO MATCH FOUND"
                )

    def clear_display_info(self):
        """Resets all dynamic label fields in the UI."""
        for lbl in self.card_labels.values():
            lbl.config(text="-")
        for lbl in self.bl_labels.values():
            lbl.config(text="-")

    def cleanup_and_exit(self):
        """Stops thread safely and cleans temporary decrypted files."""
        self.stop_polling_event.set()
        if self.temp_excel_file and os.path.exists(self.temp_excel_file):
            try:
                os.remove(self.temp_excel_file)
            except OSError:
                pass
        self.show_main_menu()

    def destroy(self):
        """Ensure thread teardown on window exit."""
        self.stop_polling_event.set()
        if self.temp_excel_file and os.path.exists(self.temp_excel_file):
            try:
                os.remove(self.temp_excel_file)
            except OSError:
                pass
        super().destroy()


if __name__ == "__main__":
    app = ThaiIDBlacklistApp()
    app.mainloop()