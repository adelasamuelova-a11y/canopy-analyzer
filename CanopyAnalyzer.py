import os
import glob
import csv
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk


def imread_unicode(path):
    """Safely read image with UTF-8 / Czech characters in path on Windows."""
    try:
        with open(path, "rb") as f:
            bytes_data = bytearray(f.read())
        numpy_array = np.asarray(bytes_data, dtype=np.uint8)
        return cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Chyba při čtení {path}: {e}")
        return None


def imwrite_unicode(path, img):
    """Safely write image with UTF-8 / Czech characters in path on Windows."""
    try:
        ext = os.path.splitext(path)[1]
        if not ext:
            ext = ".png"
        is_success, buffer = cv2.imencode(ext, img)
        if is_success:
            with open(path, "wb") as f:
                f.write(buffer)
            return True
        return False
    except Exception as e:
        print(f"Chyba při zápisu {path}: {e}")
        return False


class CanopyAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Canopy Analyzer | Hodnocení zápoje korun a otevřenosti oblohy (Fisheye)")
        self.root.geometry("1280x860")
        self.root.minsize(1050, 720)

        # UI Styling
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.bg_color = "#f4f6f9"
        self.card_bg = "#ffffff"
        self.primary_color = "#1976d2"
        self.accent_green = "#2e7d32"
        self.accent_blue = "#0288d1"
        self.root.configure(bg=self.bg_color)

        # Image state & Queue
        self.image_queue = []          # List of file paths
        self.current_index = -1
        self.img_path = None
        self.orig_bgr = None
        self.h = 0
        self.w = 0

        # Circle variables
        self.cx_var = tk.IntVar(value=0)
        self.cy_var = tk.IntVar(value=0)
        self.r_var = tk.IntVar(value=0)

        # Threshold variable
        self.thresh_var = tk.IntVar(value=128)

        # View mode
        self.view_mode = tk.StringVar(value="split")  # 'orig', 'binary', 'split'

        # Stats strings
        self.stat_closure = tk.StringVar(value="-- %")
        self.stat_openness = tk.StringVar(value="-- %")
        self.stat_thresh = tk.StringVar(value="--")
        self.stat_fileinfo = tk.StringVar(value="Žádná fotografie nenačtena")
        self.stat_counter = tk.StringVar(value="0 / 0")

        self._build_ui()

    def _build_ui(self):
        # 1. Header
        header = tk.Frame(self.root, bg="#263238", height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        lbl_title = tk.Label(
            header,
            text="🌲 Canopy Analyzer v2.0 | Vyhodnocení zápoje korun a otevřenosti oblohy",
            font=("Segoe UI", 13, "bold"),
            fg="#eceff1",
            bg="#263238",
            padx=15,
            pady=10
        )
        lbl_title.pack(side=tk.LEFT)

        # 2. Main horizontal layout
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # --- LEFT SIDEBAR (Controls & Stats) ---
        sidebar = tk.Frame(main_frame, bg=self.card_bg, width=380, padx=14, pady=12, relief=tk.SOLID, bd=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)

        # Action Buttons: Load Single / Multiple / Folder
        btn_frame = tk.Frame(sidebar, bg=self.card_bg)
        btn_frame.pack(fill=tk.X, pady=(0, 6))

        btn_load_files = tk.Button(
            btn_frame,
            text="📂 Vložit fotografie (jednu i více)",
            command=self.open_files_dialog,
            bg=self.primary_color,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=6,
            cursor="hand2"
        )
        btn_load_files.pack(fill=tk.X, pady=(0, 4))

        btn_load_dir = tk.Button(
            btn_frame,
            text="📁 Načíst celou složku s fotkami",
            command=self.open_folder_dialog,
            bg="#455a64",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=5,
            cursor="hand2"
        )
        btn_load_dir.pack(fill=tk.X, pady=(0, 6))

        # Photo navigation bar (Previous / Next)
        nav_box = tk.Frame(sidebar, bg="#eceff1", padx=6, pady=6, relief=tk.GROOVE, bd=1)
        nav_box.pack(fill=tk.X, pady=(0, 8))

        btn_prev = tk.Button(nav_box, text="◀ Předchozí", command=self.prev_photo, font=("Segoe UI", 8, "bold"), width=10, cursor="hand2")
        btn_prev.pack(side=tk.LEFT)

        lbl_cnt = tk.Label(nav_box, textvariable=self.stat_counter, font=("Segoe UI", 9, "bold"), bg="#eceff1", fg="#37474f")
        lbl_cnt.pack(side=tk.LEFT, expand=True)

        btn_next = tk.Button(nav_box, text="Další ▶", command=self.next_photo, font=("Segoe UI", 8, "bold"), width=10, cursor="hand2")
        btn_next.pack(side=tk.RIGHT)

        lbl_info = tk.Label(sidebar, textvariable=self.stat_fileinfo, font=("Segoe UI", 8, "italic"), fg="#546e7a", bg=self.card_bg, wraplength=350, justify=tk.LEFT)
        lbl_info.pack(fill=tk.X, pady=(0, 8))

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

        # --- RESULTS CARDS ---
        stats_frame = tk.LabelFrame(sidebar, text=" 📊 Výsledky zápoje & otevřenosti ", font=("Segoe UI", 9, "bold"), bg=self.card_bg, padx=10, pady=8)
        stats_frame.pack(fill=tk.X, pady=(0, 8))

        # Card 1: Zápoj korun (Canopy Closure / Cover)
        c1 = tk.Frame(stats_frame, bg="#e8f5e9", relief=tk.SOLID, bd=1, padx=8, pady=6)
        c1.pack(fill=tk.X, pady=3)
        tk.Label(c1, text="🌲 ZÁPOJ KORUN (Canopy Cover / Closure):", font=("Segoe UI", 8, "bold"), fg=self.accent_green, bg="#e8f5e9").pack(anchor=tk.W)
        tk.Label(c1, textvariable=self.stat_closure, font=("Segoe UI", 16, "bold"), fg=self.accent_green, bg="#e8f5e9").pack(anchor=tk.W)

        # Card 2: Otevřenost oblohy (Canopy Openness)
        c2 = tk.Frame(stats_frame, bg="#e1f5fe", relief=tk.SOLID, bd=1, padx=8, pady=6)
        c2.pack(fill=tk.X, pady=3)
        tk.Label(c2, text="☁️ OTEVŘENOST OBLOHY (Canopy Openness):", font=("Segoe UI", 8, "bold"), fg=self.accent_blue, bg="#e1f5fe").pack(anchor=tk.W)
        tk.Label(c2, textvariable=self.stat_openness, font=("Segoe UI", 16, "bold"), fg=self.accent_blue, bg="#e1f5fe").pack(anchor=tk.W)

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

        # --- THRESHOLD CONTROLS ---
        thresh_frame = tk.LabelFrame(sidebar, text=" ⚙️ Prahování (Binarizace na č/b) ", font=("Segoe UI", 9, "bold"), bg=self.card_bg, padx=10, pady=6)
        thresh_frame.pack(fill=tk.X, pady=(0, 8))

        row_th_head = tk.Frame(thresh_frame, bg=self.card_bg)
        row_th_head.pack(fill=tk.X)
        tk.Label(row_th_head, text="Práh (0-255):", font=("Segoe UI", 8), bg=self.card_bg).pack(side=tk.LEFT)
        tk.Label(row_th_head, textvariable=self.stat_thresh, font=("Segoe UI", 8, "bold"), bg=self.card_bg).pack(side=tk.RIGHT)

        self.scale_thresh = ttk.Scale(thresh_frame, from_=0, to=255, variable=self.thresh_var, command=self.on_thresh_change)
        self.scale_thresh.pack(fill=tk.X, pady=3)

        btn_auto_otsu = tk.Button(
            thresh_frame,
            text="⚡ Nastavit optimální práh (Otsu)",
            command=self.apply_auto_otsu,
            bg="#eceff1",
            fg="#263238",
            font=("Segoe UI", 8),
            relief=tk.GROOVE,
            cursor="hand2"
        )
        btn_auto_otsu.pack(fill=tk.X, pady=(2, 0))

        # --- CIRCLE CONTROLS ---
        circle_frame = tk.LabelFrame(sidebar, text=" ⭕ Vymezení kruhu objektivu ", font=("Segoe UI", 9, "bold"), bg=self.card_bg, padx=10, pady=6)
        circle_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(circle_frame, text="Poloměr kruhu (Radius):", font=("Segoe UI", 8), bg=self.card_bg).pack(anchor=tk.W)
        self.scale_r = ttk.Scale(circle_frame, from_=10, to=1500, variable=self.r_var, command=self.on_circle_change)
        self.scale_r.pack(fill=tk.X, pady=(0, 2))

        row_centers = tk.Frame(circle_frame, bg=self.card_bg)
        row_centers.pack(fill=tk.X)
        col_cx = tk.Frame(row_centers, bg=self.card_bg)
        col_cx.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        tk.Label(col_cx, text="Střed X:", font=("Segoe UI", 8), bg=self.card_bg).pack(anchor=tk.W)
        self.scale_cx = ttk.Scale(col_cx, from_=0, to=1000, variable=self.cx_var, command=self.on_circle_change)
        self.scale_cx.pack(fill=tk.X)

        col_cy = tk.Frame(row_centers, bg=self.card_bg)
        col_cy.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        tk.Label(col_cy, text="Střed Y:", font=("Segoe UI", 8), bg=self.card_bg).pack(anchor=tk.W)
        self.scale_cy = ttk.Scale(col_cy, from_=0, to=1000, variable=self.cy_var, command=self.on_circle_change)
        self.scale_cy.pack(fill=tk.X)

        # --- BATCH EXPORT BUTTON ---
        btn_batch_export = tk.Button(
            sidebar,
            text="📊 Spočítat vše v seznamu a exportovat do CSV",
            command=self.batch_export_all,
            bg="#2e7d32",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            pady=6,
            cursor="hand2"
        )
        btn_batch_export.pack(fill=tk.X, pady=(4, 0))

        # --- RIGHT AREA: View Panel & Canvas ---
        view_panel = tk.Frame(main_frame, bg=self.card_bg, relief=tk.SOLID, bd=1)
        view_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Mode toolbar
        mode_toolbar = tk.Frame(view_panel, bg="#eceff1", height=38, padx=10, pady=5)
        mode_toolbar.pack(fill=tk.X, side=tk.TOP)
        tk.Label(mode_toolbar, text="Zobrazení:", font=("Segoe UI", 9, "bold"), bg="#eceff1").pack(side=tk.LEFT, padx=(0, 10))

        for text, val in [("Vedle sebe (Původní / Černobílá)", "split"), ("Pouze černobílá", "binary"), ("Pouze původní + kruh", "orig")]:
            rb = ttk.Radiobutton(mode_toolbar, text=text, value=val, variable=self.view_mode, command=self.update_display)
            rb.pack(side=tk.LEFT, padx=6)

        btn_save_current = tk.Button(
            mode_toolbar,
            text="💾 Uložit aktuální černobílý snímek",
            command=self.save_current_binary,
            bg="white",
            fg="#1976d2",
            font=("Segoe UI", 8),
            relief=tk.SOLID,
            bd=1,
            cursor="hand2"
        )
        btn_save_current.pack(side=tk.RIGHT, padx=5)

        # Canvas
        self.canvas = tk.Canvas(view_panel, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas.bind("<Configure>", lambda e: self.update_display())

    def open_files_dialog(self):
        """Select one or multiple photos."""
        paths = filedialog.askopenfilenames(
            title="Vyberte jednu nebo více fotografií",
            filetypes=[("Podporované obrázky (*.jpg, *.png, *.bmp, *.tif)", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"), ("Všechny soubory", "*.*")]
        )
        if not paths:
            return

        self.image_queue = list(paths)
        self.current_index = 0
        self.load_image_at_index(0)

    def open_folder_dialog(self):
        """Open an entire folder and populate the queue."""
        folder = filedialog.askdirectory(title="Vyberte složku s hemisférickými fotografiemi")
        if not folder:
            return

        exts = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"]
        found = []
        for item in sorted(os.listdir(folder)):
            p = os.path.join(folder, item)
            if os.path.isfile(p):
                _, ext = os.path.splitext(item)
                if ext.lower() in exts:
                    found.append(p)

        if not found:
            messagebox.showwarning("Prázdná složka", f"Ve složce:\n{folder}\nnebyly nalezeny žádné obrázky.")
            return

        self.image_queue = found
        self.current_index = 0
        self.load_image_at_index(0)

    def prev_photo(self):
        if not self.image_queue:
            return
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image_at_index(self.current_index)

    def next_photo(self):
        if not self.image_queue:
            return
        if self.current_index < len(self.image_queue) - 1:
            self.current_index += 1
            self.load_image_at_index(self.current_index)

    def load_image_at_index(self, index):
        if index < 0 or index >= len(self.image_queue):
            return

        path = self.image_queue[index]
        img = imread_unicode(path)
        if img is None:
            messagebox.showerror("Chyba", f"Nepodařilo se načíst soubor:\n{path}")
            return

        self.img_path = path
        self.orig_bgr = img
        self.h, self.w = self.orig_bgr.shape[:2]

        fname = os.path.basename(path)
        self.stat_counter.set(f"{index + 1} / {len(self.image_queue)}")
        self.stat_fileinfo.set(f"{fname}\nRozlišení: {self.w}x{self.h} px")

        # Estimate center and radius
        cx = self.w // 2
        cy = self.h // 2
        
        # Keep radius if previously set, or auto detect
        curr_r = self.r_var.get()
        if curr_r > 20 and curr_r < min(self.w, self.h):
            r = curr_r
        else:
            r = self._auto_detect_fisheye_radius(self.orig_bgr, cx, cy)

        self.scale_cx.configure(from_=0, to=self.w)
        self.scale_cy.configure(from_=0, to=self.h)
        self.scale_r.configure(from_=10, to=min(self.w, self.h))

        self.cx_var.set(cx)
        self.cy_var.set(cy)
        self.r_var.set(r)

        self.apply_auto_otsu()

    def _auto_detect_fisheye_radius(self, img_bgr, cx, cy):
        """Detect the radius where the circular image meets the black lens barrel."""
        if img_bgr is None:
            return 240
        h, w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        max_r = min(cx, cy, w - cx, h - cy)
        if max_r <= 20:
            return 100
        
        best_r = int(max_r * 0.70)
        for r in range(int(max_r * 0.95), int(max_r * 0.4), -5):
            angles = np.linspace(0, 2*np.pi, 120, endpoint=False)
            xs = np.clip((cx + r * np.cos(angles)).astype(int), 0, w - 1)
            ys = np.clip((cy + r * np.sin(angles)).astype(int), 0, h - 1)
            mean_val = np.mean(gray[ys, xs])
            if mean_val > 45:
                best_r = r
                break
        return best_r

    def apply_auto_otsu(self):
        if self.orig_bgr is None:
            return
        cx, cy, r = self.cx_var.get(), self.cy_var.get(), self.r_var.get()
        if r <= 0:
            return

        mask = np.zeros((self.h, self.w), dtype=np.uint8)
        cv2.circle(mask, (cx, cy), r, 255, -1)

        blue = self.orig_bgr[:, :, 0]
        inside = blue[mask == 255]

        if len(inside) > 0:
            otsu_val, _ = cv2.threshold(inside, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            self.thresh_var.set(int(otsu_val))
            self.stat_thresh.set(f"{int(otsu_val)} (Auto-Otsu)")
        self.recalculate_and_draw()

    def on_thresh_change(self, event=None):
        self.stat_thresh.set(f"{self.thresh_var.get()} (Manuální)")
        self.recalculate_and_draw()

    def on_circle_change(self, event=None):
        self.recalculate_and_draw()

    def recalculate_and_draw(self):
        if self.orig_bgr is None:
            return

        cx = self.cx_var.get()
        cy = self.cy_var.get()
        r = self.r_var.get()
        thresh = self.thresh_var.get()

        mask = np.zeros((self.h, self.w), dtype=np.uint8)
        cv2.circle(mask, (cx, cy), r, 255, -1)

        blue = self.orig_bgr[:, :, 0]
        _, binary = cv2.threshold(blue, thresh, 255, cv2.THRESH_BINARY)
        binary_masked = cv2.bitwise_and(binary, binary, mask=mask)

        total_px = np.count_nonzero(mask)
        if total_px > 0:
            sky_px = np.count_nonzero(binary_masked)  # Bílá = obloha (bez zápoje)
            canopy_px = total_px - sky_px              # Černá = koruny (zápoj)

            openness = (sky_px / total_px) * 100.0
            closure = (canopy_px / total_px) * 100.0

            self.stat_closure.set(f"{closure:.1f} %")
            self.stat_openness.set(f"{openness:.1f} %")
        else:
            self.stat_closure.set("-- %")
            self.stat_openness.set("-- %")

        self.binary_cached = binary_masked
        self.mask_cached = mask
        self.update_display()

    def update_display(self):
        if self.orig_bgr is None:
            return

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:
            return

        mode = self.view_mode.get()
        cx, cy, r = self.cx_var.get(), self.cy_var.get(), self.r_var.get()

        orig_disp = self.orig_bgr.copy()
        cv2.circle(orig_disp, (cx, cy), r, (0, 255, 0), 2)
        cv2.circle(orig_disp, (cx, cy), 4, (0, 0, 255), -1)

        bin_disp = cv2.cvtColor(self.binary_cached, cv2.COLOR_GRAY2BGR)
        bin_disp[self.mask_cached == 0] = [35, 35, 35]

        if mode == "orig":
            final_bgr = orig_disp
        elif mode == "binary":
            final_bgr = bin_disp
        else:  # 'split'
            final_bgr = np.hstack([orig_disp, bin_disp])

        img_h, img_w = final_bgr.shape[:2]
        scale = min((canvas_w - 20) / img_w, (canvas_h - 20) / img_h)
        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))

        resized = cv2.resize(final_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        self.tk_img = ImageTk.PhotoImage(pil_img)

        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, anchor=tk.CENTER, image=self.tk_img)

    def save_current_binary(self):
        if self.orig_bgr is None or not hasattr(self, "binary_cached"):
            messagebox.showwarning("Upozornění", "Nejprve otevřete fotografii.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Uložit černobílý snímek",
            defaultextension=".png",
            filetypes=[("PNG obrázek", "*.png"), ("JPEG obrázek", "*.jpg"), ("BMP rastr", "*.bmp")]
        )
        if out_path:
            ok = imwrite_unicode(out_path, self.binary_cached)
            if ok:
                messagebox.showinfo("Uloženo", f"Černobílý snímek byl úspěšně uložen do:\n{out_path}")
            else:
                messagebox.showerror("Chyba", "Nepodařilo se uložit soubor.")

    def batch_export_all(self):
        """Batch evaluate all images currently in the queue, save CSV and binary masks."""
        if not self.image_queue:
            messagebox.showwarning("Prázdný seznam", "Nejprve vložte fotografie nebo načtěte složku.")
            return

        out_dir = filedialog.askdirectory(title="Vyberte cílovou složku pro uložení CSV tabulky a černobílých masek")
        if not out_dir:
            return

        csv_path = os.path.join(out_dir, "vysledky_zapoj_batch.csv")
        results = []

        progress_win = tk.Toplevel(self.root)
        progress_win.title("Zpracovávám fotografie...")
        progress_win.geometry("460x150")
        progress_win.transient(self.root)
        progress_win.grab_set()

        lbl_status = tk.Label(progress_win, text=f"Zpracovávám 0 z {len(self.image_queue)}...", font=("Segoe UI", 9))
        lbl_status.pack(pady=10)
        pbar = ttk.Progressbar(progress_win, maximum=len(self.image_queue), mode="determinate")
        pbar.pack(fill=tk.X, padx=20, pady=5)
        progress_win.update()

        for i, file_path in enumerate(self.image_queue, 1):
            fname = os.path.basename(file_path)
            lbl_status.config(text=f"Zpracovávám ({i}/{len(self.image_queue)}):\n{fname}")
            pbar.config(value=i)
            progress_win.update()

            img = imread_unicode(file_path)
            if img is None:
                continue

            h, w = img.shape[:2]
            cx, cy = w // 2, h // 2
            
            curr_r = self.r_var.get()
            if curr_r > 20 and curr_r < min(w, h):
                r = curr_r
            else:
                r = self._auto_detect_fisheye_radius(img, cx, cy)

            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.circle(mask, (cx, cy), r, 255, -1)

            blue = img[:, :, 0]
            inside = blue[mask == 255]
            if len(inside) == 0:
                continue

            otsu_val, _ = cv2.threshold(inside, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            _, binary = cv2.threshold(blue, otsu_val, 255, cv2.THRESH_BINARY)
            binary_masked = cv2.bitwise_and(binary, binary, mask=mask)

            tot = np.count_nonzero(mask)
            sky = np.count_nonzero(binary_masked)
            canopy = tot - sky
            open_pct = (sky / tot) * 100.0
            close_pct = (canopy / tot) * 100.0

            results.append({
                "Soubor": fname,
                "Zapoj_korun_%": f"{close_pct:.2f}".replace(".", ","),
                "Otevrenost_oblohy_%": f"{open_pct:.2f}".replace(".", ","),
                "Prah_Otsu": int(otsu_val),
                "Stred_X": cx,
                "Stred_Y": cy,
                "Polomer_R": r
            })

            base_name = os.path.splitext(fname)[0]
            out_img_name = f"bw_{base_name}.png"
            imwrite_unicode(os.path.join(out_dir, out_img_name), binary_masked)

        # Write CSV with BOM for Excel compatibility
        with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["Soubor", "Zapoj_korun_%", "Otevrenost_oblohy_%", "Prah_Otsu", "Stred_X", "Stred_Y", "Polomer_R"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerows(results)

        progress_win.destroy()
        messagebox.showinfo(
            "Hotovo!",
            f"Úspěšně zpracováno {len(results)} fotografií!\n\n"
            f"📊 Tabulka CSV pro Excel:\n{csv_path}\n\n"
            f"🖼️ Černobílé masky jsou ve složce:\n{out_dir}"
        )


def main():
    root = tk.Tk()
    app = CanopyAnalyzerApp(root)
    
    # Pre-load sample if exists
    sample_path = r"C:\Users\Ada Samuelova\.gemini\antigravity\brain\86d575ee-2bb0-436b-94e5-cecdcc3ef1de\.user_uploaded\media_1793879169726_aa4aae20.jpg"
    if os.path.exists(sample_path):
        app.image_queue = [sample_path]
        app.current_index = 0
        app.load_image_at_index(0)
        
    root.mainloop()


if __name__ == "__main__":
    main()
