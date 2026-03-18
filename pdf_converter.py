import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import fitz  # PyMuPDF
import os
import re
import numpy as np
from PIL import Image, ImageOps, ImageEnhance

class TkDnDApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

class PDFConverterApp(TkDnDApp):
    def __init__(self):
        super().__init__()

        self.title("Texture Processor & PDF Converter")
        self.geometry("1000x650") 
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.minsize(900, 600)

        self.selected_paths = []

        # ==================== MAIN LAYOUT ====================
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==================== LEFT SIDEBAR (SETTINGS) ====================
        self.sidebar_frame = ctk.CTkFrame(self, width=320, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.pack_propagate(False) # Keep sidebar width fixed

        # App Title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Texture\nProcessor", 
                                       font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"), justify="left")
        self.logo_label.pack(pady=(30, 20), padx=20, anchor="w")

        # --- Section 1: Output Geometry ---
        self.lbl_geo = ctk.CTkLabel(self.sidebar_frame, text="OUTPUT GEOMETRY", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray50")
        self.lbl_geo.pack(anchor="w", padx=20, pady=(10, 0))

        self.square_var = ctk.BooleanVar(value=False)
        self.chk_square = ctk.CTkCheckBox(self.sidebar_frame, text="Force 1:1 Square Canvas", variable=self.square_var)
        self.chk_square.pack(anchor="w", padx=20, pady=10)

        self.res_var = ctk.StringVar(value="Match Original")
        self.res_menu = ctk.CTkOptionMenu(self.sidebar_frame, variable=self.res_var, values=["Match Original", "1024x1024", "2048x2048", "4096x4096"], width=280)
        self.res_menu.pack(padx=20, pady=(0, 15))

        # --- Section 2: Color & Alpha ---
        self.lbl_color = ctk.CTkLabel(self.sidebar_frame, text="COLOR & ALPHA", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray50")
        self.lbl_color.pack(anchor="w", padx=20, pady=(10, 0))

        self.remove_bg_var = ctk.BooleanVar(value=False)
        self.chk_bg = ctk.CTkCheckBox(self.sidebar_frame, text="Force Remove White BG", variable=self.remove_bg_var)
        self.chk_bg.pack(anchor="w", padx=20, pady=(10, 5))

        self.invert_var = ctk.BooleanVar(value=False)
        self.chk_invert = ctk.CTkCheckBox(self.sidebar_frame, text="Invert Colors (Bump/Roughness)", variable=self.invert_var)
        self.chk_invert.pack(anchor="w", padx=20, pady=5)

        self.sat_label = ctk.CTkLabel(self.sidebar_frame, text="Saturation: 1.0", font=ctk.CTkFont(size=12))
        self.sat_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.sat_slider = ctk.CTkSlider(self.sidebar_frame, from_=0, to=3, number_of_steps=30, command=self.update_sat_label)
        self.sat_slider.set(1.0)
        self.sat_slider.pack(fill="x", padx=20, pady=(0, 15))

        # --- Section 3: PDF Engine ---
        self.lbl_pdf = ctk.CTkLabel(self.sidebar_frame, text="PDF RENDER ENGINE", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray50")
        self.lbl_pdf.pack(anchor="w", padx=20, pady=(10, 0))

        self.zoom_label = ctk.CTkLabel(self.sidebar_frame, text="Render Zoom (Quality): 4.0", font=ctk.CTkFont(size=12))
        self.zoom_label.pack(anchor="w", padx=20, pady=(10, 0))
        
        self.zoom_slider = ctk.CTkSlider(self.sidebar_frame, from_=1, to=10, number_of_steps=18, command=self.update_zoom_label)
        self.zoom_slider.set(4.0)
        self.zoom_slider.pack(fill="x", padx=20, pady=(0, 20))

        # ==================== RIGHT WORKSPACE ====================
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1) # File list expands

        # --- Big Drop Zone ---
        self.drop_frame = ctk.CTkFrame(self.main_frame, height=200, corner_radius=15, fg_color=("gray80", "gray15"), border_width=2, border_color="gray30")
        self.drop_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.drop_frame.pack_propagate(False)

        self.drop_icon = ctk.CTkLabel(self.drop_frame, text="📥", font=ctk.CTkFont(size=40))
        self.drop_icon.pack(pady=(40, 0))

        self.drop_label = ctk.CTkLabel(self.drop_frame, text="Drag & Drop PDFs or Images here", font=ctk.CTkFont(size=16, weight="bold"))
        self.drop_label.pack(pady=(5, 5))

        self.select_btn = ctk.CTkButton(self.drop_frame, text="Or Browse Files", fg_color="transparent", border_width=1, text_color=("gray10", "gray90"), hover_color=("gray70", "gray25"), command=self.select_files)
        self.select_btn.pack(pady=5)

        # Register entire main area for Drag & Drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)
        self.main_frame.drop_target_register(DND_FILES)
        self.main_frame.dnd_bind('<<Drop>>', self.handle_drop)

        # --- Queue Header ---
        self.queue_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.queue_header.grid(row=1, column=0, sticky="ew")
        
        self.queue_label = ctk.CTkLabel(self.queue_header, text="Processing Queue", font=ctk.CTkFont(size=16, weight="bold"))
        self.queue_label.pack(side="left")

        self.clear_btn = ctk.CTkButton(self.queue_header, text="Clear Queue", width=100, fg_color="transparent", text_color="#ff5555", hover_color="#442222", command=self.clear_queue)
        self.clear_btn.pack(side="right")

        # --- File List ---
        self.file_list_frame = ctk.CTkScrollableFrame(self.main_frame, corner_radius=10, fg_color=("gray85", "gray10"))
        self.file_list_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 20))

        # --- Execution Area ---
        self.exec_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.exec_frame.grid(row=3, column=0, sticky="ew")

        self.progress = ctk.CTkProgressBar(self.exec_frame, height=12)
        self.progress.set(0)
        self.progress.pack(side="left", fill="x", expand=True, padx=(0, 20))

        self.process_btn = ctk.CTkButton(self.exec_frame, text="PROCESS FILES", state="disabled", font=ctk.CTkFont(weight="bold"), fg_color="#2b8a3e", hover_color="#206a2e", height=40, command=self.process_files)
        self.process_btn.pack(side="right")

    # ==================== LOGIC FUNCTIONS ====================
    def update_sat_label(self, value):
        self.sat_label.configure(text=f"Saturation: {value:.1f}")

    def update_zoom_label(self, value):
        self.zoom_label.configure(text=f"Render Zoom (Quality): {value:.1f}")

    def clear_queue(self):
        self.selected_paths.clear()
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
        self.process_btn.configure(state="disabled")

    def handle_drop(self, event):
        paths = re.findall(r'\{.*?\}|\S+', event.data)
        valid_exts = ('.pdf', '.png', '.jpg', '.jpeg')
        clean_paths = [path.strip('{}') for path in paths if path.strip('{}').lower().endswith(valid_exts)]
        self.add_files(clean_paths)

    def select_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Supported Files", "*.pdf *.png *.jpg *.jpeg")])
        if file_paths:
            self.add_files(file_paths)

    def add_files(self, files):
        for f in files:
            if f not in self.selected_paths:
                self.selected_paths.append(f)
                
                # Create a nice looking row for each file
                file_row = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
                file_row.pack(fill="x", padx=5, pady=4)
                
                icon = "📄" if f.lower().endswith(".pdf") else "🖼️"
                lbl = ctk.CTkLabel(file_row, text=f"{icon}  {os.path.basename(f)}", anchor="w", font=ctk.CTkFont(size=13))
                lbl.pack(side="left", fill="x", expand=True)
        
        if self.selected_paths:
            self.process_btn.configure(state="normal")

    def process_image(self, img):
        if self.sat_slider.get() != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(self.sat_slider.get())

        if self.invert_var.get():
            r, g, b, a = img.split()
            rgb_img = Image.merge("RGB", (r, g, b))
            inverted_img = ImageOps.invert(rgb_img)
            r2, g2, b2 = inverted_img.split()
            img = Image.merge("RGBA", (r2, g2, b2, a))

        if self.remove_bg_var.get():
            img_array = np.array(img)
            r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
            white_mask = (r > 230) & (g > 230) & (b > 230)
            img_array[white_mask, 3] = 0
            img = Image.fromarray(img_array)

        if self.square_var.get():
            max_dim = max(img.width, img.height)
            square_img = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
            paste_x = (max_dim - img.width) // 2
            paste_y = (max_dim - img.height) // 2
            square_img.paste(img, (paste_x, paste_y))
            img = square_img

        res_choice = self.res_var.get()
        if res_choice != "Match Original":
            target_size = int(res_choice.split("x")[0])
            if self.square_var.get():
                img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            else:
                img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

        return img

    def process_files(self):
        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if not output_folder:
            return

        self.process_btn.configure(state="disabled", text="PROCESSING...")
        self.update_idletasks()

        try:
            total_files = len(self.selected_paths)
            zoom_level = self.zoom_slider.get()

            for file_index, file_path in enumerate(self.selected_paths):
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                ext = os.path.splitext(file_path)[1].lower()

                if ext == '.pdf':
                    doc = fitz.open(file_path)
                    for i, page in enumerate(doc):
                        mat = fitz.Matrix(zoom_level, zoom_level)
                        pix = page.get_pixmap(matrix=mat, alpha=True) 
                        img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
                        final_img = self.process_image(img)
                        final_img.save(f"{output_folder}/{base_name}_page_{i+1}.png", "PNG")
                    doc.close()
                
                elif ext in ['.png', '.jpg', '.jpeg']:
                    img = Image.open(file_path).convert("RGBA")
                    final_img = self.process_image(img)
                    final_img.save(f"{output_folder}/{base_name}_processed.png", "PNG")

                self.progress.set((file_index + 1) / total_files)
                self.update_idletasks()

            messagebox.showinfo("Success", f"Successfully processed {total_files} file(s)!")
            self.clear_queue()
            self.progress.set(0)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process: {str(e)}")
        finally:
            self.process_btn.configure(text="PROCESS FILES")
            if self.selected_paths:
                self.process_btn.configure(state="normal")

if __name__ == "__main__":
    app = PDFConverterApp()
    app.mainloop()