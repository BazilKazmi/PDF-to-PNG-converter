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
        self.geometry("650x720") # Made slightly taller for the new slider
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.selected_paths = []

        # --- Title ---
        self.label = ctk.CTkLabel(self, text="Texture Processor & PDF Converter", font=("Arial", 20, "bold"))
        self.label.pack(pady=15)

        # --- Settings Panel ---
        self.settings_frame = ctk.CTkFrame(self, corner_radius=10)
        self.settings_frame.pack(pady=5, padx=20, fill="x")
        
        self.settings_label = ctk.CTkLabel(self.settings_frame, text="Processing & Render Settings", font=("Arial", 14, "bold"))
        self.settings_label.pack(pady=5)

        # 1. Image Toggles
        self.remove_bg_var = ctk.BooleanVar(value=False)
        self.invert_var = ctk.BooleanVar(value=False)

        self.chk_bg = ctk.CTkCheckBox(self.settings_frame, text="Force Remove White BG (Use only if PDF lacks native alpha)", variable=self.remove_bg_var)
        self.chk_bg.pack(anchor="w", padx=20, pady=5)

        self.chk_invert = ctk.CTkCheckBox(self.settings_frame, text="Invert Colors (Great for Roughness/Bump Maps)", variable=self.invert_var)
        self.chk_invert.pack(anchor="w", padx=20, pady=5)

        # 2. Saturation Slider
        self.sat_label = ctk.CTkLabel(self.settings_frame, text="Saturation: 1.0 (Normal)")
        self.sat_label.pack(anchor="w", padx=20, pady=(5, 0))
        
        self.sat_slider = ctk.CTkSlider(self.settings_frame, from_=0, to=3, number_of_steps=30, command=self.update_sat_label)
        self.sat_slider.set(1.0)
        self.sat_slider.pack(fill="x", padx=20, pady=(0, 5))

        # 3. Quality / Zoom Slider (NEW)
        self.zoom_label = ctk.CTkLabel(self.settings_frame, text="PDF Render Quality (Zoom): 4.0")
        self.zoom_label.pack(anchor="w", padx=20, pady=(5, 0))
        
        # Ranges from 1 to 10. Step counts allow for smooth half-steps.
        self.zoom_slider = ctk.CTkSlider(self.settings_frame, from_=1, to=10, number_of_steps=18, command=self.update_zoom_label)
        self.zoom_slider.set(4.0)
        self.zoom_slider.pack(fill="x", padx=20, pady=(0, 15))

        # --- Drop Zone Frame ---
        self.drop_frame = ctk.CTkFrame(self, height=100, corner_radius=15)
        self.drop_frame.pack(pady=10, padx=20, fill="x")
        self.drop_frame.pack_propagate(False)

        self.drop_label = ctk.CTkLabel(self.drop_frame, text="Drag & Drop PDFs or Images here\nor", text_color="gray")
        self.drop_label.pack(pady=(15, 5))

        self.select_btn = ctk.CTkButton(self.drop_frame, text="Browse Files", command=self.select_files)
        self.select_btn.pack(pady=5)

        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.handle_drop)

        # --- File List & Execution ---
        self.file_list_frame = ctk.CTkScrollableFrame(self, height=80)
        self.file_list_frame.pack(pady=5, padx=20, fill="both", expand=True)

        self.process_btn = ctk.CTkButton(self, text="Process Files", state="disabled", 
                                          fg_color="green", hover_color="darkgreen", command=self.process_files)
        self.process_btn.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(pady=10, padx=20, fill="x")

    def update_sat_label(self, value):
        self.sat_label.configure(text=f"Saturation: {value:.1f} (0=Grayscale)")

    def update_zoom_label(self, value):
        self.zoom_label.configure(text=f"PDF Render Quality (Zoom): {value:.1f}")

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
                lbl = ctk.CTkLabel(self.file_list_frame, text=os.path.basename(f), anchor="w")
                lbl.pack(fill="x", padx=5, pady=2)
        
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
            # Slightly more aggressive threshold to help eat away white fringing on standard images
            white_mask = (r > 230) & (g > 230) & (b > 230)
            img_array[white_mask, 3] = 0
            img = Image.fromarray(img_array)

        return img

    def process_files(self):
        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if not output_folder:
            return

        try:
            total_files = len(self.selected_paths)
            zoom_level = self.zoom_slider.get() # Get the current slider value

            for file_index, file_path in enumerate(self.selected_paths):
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                ext = os.path.splitext(file_path)[1].lower()

                if ext == '.pdf':
                    doc = fitz.open(file_path)
                    for i, page in enumerate(doc):
                        # Apply the dynamic zoom level and strictly enforce Alpha channel
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
            
            self.progress.set(0)
            self.selected_paths.clear()
            for widget in self.file_list_frame.winfo_children():
                widget.destroy()
            self.process_btn.configure(state="disabled")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process: {str(e)}")

if __name__ == "__main__":
    app = PDFConverterApp()
    app.mainloop()