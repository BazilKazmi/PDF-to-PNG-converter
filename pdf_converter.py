import customtkinter as ctk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import os

class PDFConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PDF to PNG Converter")
        self.geometry("500x350")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # --- UI Elements ---
        self.label = ctk.CTkLabel(self, text="PDF to PNG Converter", font=("Arial", 20, "bold"))
        self.label.pack(pady=20)

        self.select_btn = ctk.CTkButton(self, text="Select PDF File", command=self.select_file)
        self.select_btn.pack(pady=10)

        self.file_label = ctk.CTkLabel(self, text="No file selected", text_color="gray")
        self.file_label.pack(pady=5)

        self.convert_btn = ctk.CTkButton(self, text="Convert to PNG", state="disabled", 
                                          fg_color="green", hover_color="darkgreen", command=self.convert)
        self.convert_btn.pack(pady=20)

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.set(0)
        self.progress.pack(pady=10)

        self.selected_path = ""

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.selected_path = file_path
            self.file_label.configure(text=os.path.basename(file_path), text_color="white")
            self.convert_btn.configure(state="normal")

    def convert(self):
        output_folder = filedialog.askdirectory(title="Select Output Folder")
        if not output_folder:
            return

        try:
            doc = fitz.open(self.selected_path)
            total_pages = len(doc)
            
            for i, page in enumerate(doc):
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # High Quality
                pix.save(f"{output_folder}/page_{i+1}.png")
                self.progress.set((i + 1) / total_pages)
                self.update_idletasks()

            doc.close()
            messagebox.showinfo("Success", f"Converted {total_pages} pages successfully!")
            self.progress.set(0)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert: {str(e)}")

if __name__ == "__main__":
    app = PDFConverterApp()
    app.mainloop()