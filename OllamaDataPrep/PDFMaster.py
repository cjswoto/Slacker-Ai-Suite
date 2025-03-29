import os
import fitz  # PyMuPDF
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk

#######################################
# Original Extraction Logic
#######################################
def extract_images(pdf_document, output_dir, name_predicate, pages, save_pages_as_images):
    """
    Extract either embedded images or full-page snapshots from specified pages.
    If save_pages_as_images=True, saves the entire page as an image.
    Otherwise extracts each embedded image individually.
    """
    image_count = 0
    for page_number in pages:
        page = pdf_document.load_page(page_number)
        if save_pages_as_images:
            # Save the entire page as an image
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            image_path = os.path.join(output_dir, f"{name_predicate}_page_{page_number + 1}.png")
            img.save(image_path)
            print(f"Page image saved to: {image_path}")
        else:
            # Extract images from the page
            image_list = page.get_images(full=True)
            if not image_list:
                continue
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_path = os.path.join(output_dir, f"{name_predicate}_{image_count}.{image_ext}")
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                print(f"Image extracted and saved to: {image_path}")
                image_count += 1

def preview_pdf(pdf_path, page_number=0):
    """
    Return a PIL Image of the specified page_number from pdf_path,
    along with the total number of pages.
    """
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(page_number)
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img, len(pdf_document)

def parse_page_input(pages_str, total_pages):
    """
    Parse the user input for pages to parse,
    supporting 'ALL' and ranges like '2-5' or comma-delimited pages.
    """
    if pages_str.upper() == "ALL":
        return list(range(total_pages))

    pages = []
    parts = pages_str.split(',')
    for part in parts:
        if '-' in part:
            start, end = part.split('-')
            pages.extend(range(int(start) - 1, int(end)))
        else:
            pages.append(int(part) - 1)
    return pages

##########################################
# TtkBootstrap GUI with OllamaFace look
##########################################

CONFIG_FILE = "last_paths.cfg"

class PDFMasterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Image Extractor - OllamaFace UI")
        # Increase default size for comfortable spacing
        self.root.geometry("1024x800")

        # Make sure to configure style
        self.style = tb.Style(theme="superhero")
        # Larger base font for the entire app
        self.style.configure('.', font=('Segoe UI', 11))

        # Title Label (top)
        self.title_label = tb.Label(
            self.root,
            text="PDF Image Extractor",
            bootstyle=INFO,
            font=("Segoe UI", 18, "bold")
        )
        self.title_label.pack(pady=10)

        ########################################################
        # SCROLLABLE MAIN FRAME
        # We'll create a Canvas + a Scrollbar, then place a Frame inside.
        ########################################################
        self.scroll_canvas = tk.Canvas(
            self.root,
            background="#2b2b2b"
        )
        self.scroll_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.scrollbar = tb.Scrollbar(
            self.root,
            orient=VERTICAL,
            bootstyle=SECONDARY,
            command=self.scroll_canvas.yview
        )
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.scrollable_frame = tb.Frame(self.scroll_canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.scroll_canvas.configure(
                scrollregion=self.scroll_canvas.bbox("all")
            )
        )

        self.canvas_window = self.scroll_canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        # We'll keep all content inside self.scrollable_frame.
        ########################################################

        # We proceed to build content in self.scrollable_frame
        self.main_frame = tb.Frame(self.scrollable_frame, padding=20)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Load last used directories if present
        self.last_pdf = ""
        self.last_out = os.getcwd()
        self.load_config()

        self.init_file_frame()
        self.init_preview_section()
        self.init_settings_frame()
        self.init_extraction_options()
        self.init_buttons()
        self.init_images_display()

    def load_config(self):
        """
        Load the last used PDF path and output directory from CONFIG_FILE,
        so we can pre-populate those fields.
        """
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 2:
                        self.last_pdf = lines[0].strip()
                        self.last_out = lines[1].strip()
            except:
                pass

    def save_config(self, pdf_path, out_path):
        """
        Save the last used PDF path and output directory to CONFIG_FILE.
        """
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(pdf_path + "\n")
                f.write(out_path + "\n")
        except:
            pass

    def init_file_frame(self):
        """
        A labeled frame for PDF selection and output directory.
        """
        self.file_frame = tb.Labelframe(self.main_frame, text="PDF & Output", padding=15)
        self.file_frame.pack(fill=X, padx=10, pady=10)

        # PDF file row
        pdf_row = tb.Frame(self.file_frame)
        pdf_row.pack(fill=X, pady=5)

        tb.Label(pdf_row, text="PDF File:", font=("Segoe UI", 12)).pack(side=LEFT)
        self.pdf_entry = tb.Entry(pdf_row, width=50)
        self.pdf_entry.pack(side=LEFT, padx=5, fill=X, expand=True)
        # If we loaded a last pdf path from config, set it
        if self.last_pdf:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, self.last_pdf)

        tb.Button(pdf_row, text="Browse...", bootstyle=INFO, command=self.browse_pdf).pack(side=LEFT, padx=5)

        # Output directory row
        out_row = tb.Frame(self.file_frame)
        out_row.pack(fill=X, pady=5)

        tb.Label(out_row, text="Output Directory:", font=("Segoe UI", 12)).pack(side=LEFT)
        self.output_entry = tb.Entry(out_row, width=50)
        # If we loaded a last out path from config, set it, else default to current
        self.output_entry.insert(0, self.last_out or os.getcwd())
        self.output_entry.pack(side=LEFT, padx=5, fill=X, expand=True)
        tb.Button(out_row, text="Browse...", bootstyle=INFO, command=self.browse_output_dir).pack(side=LEFT, padx=5)

    def init_preview_section(self):
        """
        A labeled frame for PDF preview with page navigation.
        """
        self.preview_frame = tb.Labelframe(self.main_frame, text="PDF Preview", padding=15)
        self.preview_frame.pack(fill=X, padx=10, pady=10)

        # Label for preview
        self.pdf_preview = tb.Label(self.preview_frame)
        self.pdf_preview.pack(pady=5)

        # Navigation
        self.nav_frame = tb.Frame(self.preview_frame)
        self.nav_frame.pack(pady=5)

        tb.Button(self.nav_frame, text="Previous Page", bootstyle=PRIMARY, command=self.previous_page).pack(side=LEFT, padx=5)
        self.current_page_label = tb.Label(self.nav_frame, text="Page 1/1", font=("Segoe UI", 10))
        self.current_page_label.current_page = 0
        self.current_page_label.total_pages = 1
        self.current_page_label.pack(side=LEFT, padx=5)
        tb.Button(self.nav_frame, text="Next Page", bootstyle=PRIMARY, command=self.next_page).pack(side=LEFT, padx=5)

    def init_settings_frame(self):
        """
        A labeled frame for advanced extraction settings:
        name predicate, pages to parse, skip pattern, starting page.
        """
        self.settings_frame = tb.Labelframe(self.main_frame, text="Extraction Settings", padding=15)
        self.settings_frame.pack(fill=X, padx=10, pady=10)

        # Name predicate
        np_row = tb.Frame(self.settings_frame)
        np_row.pack(fill=X, pady=3)
        tb.Label(np_row, text="Name Predicate:", width=15).pack(side=LEFT)
        self.name_predicate_entry = tb.Entry(np_row, width=30)
        self.name_predicate_entry.insert(0, "extracted_image")
        self.name_predicate_entry.pack(side=LEFT, padx=5, fill=X, expand=True)

        # Pages to parse
        pages_row = tb.Frame(self.settings_frame)
        pages_row.pack(fill=X, pady=3)
        tb.Label(pages_row, text="Pages to Parse:", width=15).pack(side=LEFT)
        self.pages_entry = tb.Entry(pages_row, width=30)
        self.pages_entry.insert(0, "ALL")
        self.pages_entry.pack(side=LEFT, padx=5, fill=X, expand=True)

        # Skip pattern
        skip_row = tb.Frame(self.settings_frame)
        skip_row.pack(fill=X, pady=3)
        tb.Label(skip_row, text="Skip Pattern:", width=15).pack(side=LEFT)
        self.skip_pattern_entry = tb.Entry(skip_row, width=30)
        self.skip_pattern_entry.insert(0, "1")
        self.skip_pattern_entry.pack(side=LEFT, padx=5, fill=X, expand=True)

        # Starting page
        start_row = tb.Frame(self.settings_frame)
        start_row.pack(fill=X, pady=3)
        tb.Label(start_row, text="Starting Page:", width=15).pack(side=LEFT)
        self.start_page_entry = tb.Entry(start_row, width=30)
        self.start_page_entry.insert(0, "1")
        self.start_page_entry.pack(side=LEFT, padx=5, fill=X, expand=True)

    def init_extraction_options(self):
        """
        A labeled frame for choosing between extracting images
        or saving pages as images.
        """
        self.options_frame = tb.Labelframe(self.main_frame, text="Extraction Type", padding=10)
        self.options_frame.pack(fill=X, padx=10, pady=10)

        self.save_option_var = tk.StringVar(value="images")
        row = tb.Frame(self.options_frame)
        row.pack()

        rb1 = tb.Radiobutton(row, text="Extract Images", variable=self.save_option_var,
                             value="images", bootstyle=PRIMARY)
        rb1.pack(side=LEFT, padx=20)
        rb2 = tb.Radiobutton(row, text="Save Pages as Images", variable=self.save_option_var,
                             value="pages", bootstyle=INFO)
        rb2.pack(side=LEFT, padx=20)

    def init_buttons(self):
        """
        A frame at the bottom for the Start Extraction button.
        """
        self.button_frame = tb.Frame(self.main_frame, padding=10)
        self.button_frame.pack(fill=X, padx=10, pady=5)

        tb.Button(self.button_frame, text="🚀 Start Extraction",
                  bootstyle=SUCCESS, command=self.start_extraction).pack()

    def init_images_display(self):
        """
        The bottom frame to display extracted images in a scrollable area.
        """
        self.image_display_frame = tb.Labelframe(self.main_frame, text="Extracted Images", padding=15)
        self.image_display_frame.pack(fill=BOTH, padx=10, pady=10, expand=True)

    #####################################
    # Feature: Display Extracted Images
    #####################################

    def display_extracted_images(self, output_dir):
        """
        Display the extracted images from output_dir in a scrollable
        horizontal area in image_display_frame.
        """
        for widget in self.image_display_frame.winfo_children():
            widget.destroy()

        images = [f for f in os.listdir(output_dir) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
        if images:
            canvas = tk.Canvas(self.image_display_frame, background="#2b2b2b")  # Themed color
            scrollbar = ttk.Scrollbar(self.image_display_frame, orient="horizontal", command=canvas.xview)
            scrollable_frame = tb.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(
                    scrollregion=canvas.bbox("all")
                )
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(xscrollcommand=scrollbar.set)

            for image_file in images:
                image_path = os.path.join(output_dir, image_file)
                img = Image.open(image_path)
                img.thumbnail((100, 100))
                img_tk = ImageTk.PhotoImage(img)
                label = tb.Label(scrollable_frame, image=img_tk, bootstyle=SECONDARY)
                label.image = img_tk
                label.pack(side=tk.LEFT, padx=5, pady=5)

            canvas.pack(side=tk.TOP, fill="both", expand=True)
            scrollbar.pack(side=tk.BOTTOM, fill="x")
        else:
            ttk.Label(self.image_display_frame, text="No images found in the output directory.").pack()

    ##################################
    # Page Preview Navigation Logic
    ##################################

    def update_preview(self, page_number):
        """
        Update the PDF preview to show the given page_number.
        """
        pdf_path = self.pdf_entry.get().strip()
        if pdf_path and os.path.exists(pdf_path):
            img, total_pages = preview_pdf(pdf_path, page_number)
            img.thumbnail((400, 400))
            img_tk = ImageTk.PhotoImage(img)
            self.pdf_preview.config(image=img_tk)
            self.pdf_preview.image = img_tk
            self.current_page_label.config(text=f"Page {page_number + 1}/{total_pages}")
            self.current_page_label.current_page = page_number
            self.current_page_label.total_pages = total_pages

    def next_page(self):
        """
        Move to the next page in the preview,
        if not already on the final page.
        """
        if self.current_page_label.current_page < self.current_page_label.total_pages - 1:
            self.update_preview(self.current_page_label.current_page + 1)

    def previous_page(self):
        """
        Move to the previous page in the preview,
        if not already on the first page.
        """
        if self.current_page_label.current_page > 0:
            self.update_preview(self.current_page_label.current_page - 1)

    ##################################
    # Main Extraction Function
    ##################################

    def start_extraction(self):
        """
        Start extracting either embedded images or full-page images,
        based on the user settings. Then show the results in the UI.
        """
        pdf_path = self.pdf_entry.get().strip()
        output_dir = self.output_entry.get().strip()
        name_predicate = self.name_predicate_entry.get().strip()
        pages_to_parse = self.pages_entry.get().strip()
        save_option = self.save_option_var.get()
        skip_pattern = self.skip_pattern_entry.get().strip()
        start_page = self.start_page_entry.get().strip()

        if not os.path.exists(pdf_path):
            messagebox.showerror("Error", f"The file {pdf_path} does not exist.")
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)

        # Parse the pages to extract
        if pages_to_parse:
            pages = parse_page_input(pages_to_parse, total_pages)
        else:
            pages = list(range(total_pages))

        # Starting page logic
        if start_page.isdigit():
            start = int(start_page) - 1
            pages = [p for p in pages if p >= start]

        # Skip pattern logic
        if skip_pattern.isdigit():
            skip = int(skip_pattern)
            pages = pages[::skip]

        # Ensure we don't go out of bounds
        pages = [p for p in pages if 0 <= p < total_pages]

        # Distinguish between full-page vs. embedded image extraction
        save_pages_as_images = (save_option == "pages")

        # Extract images accordingly
        extract_images(pdf_document, output_dir, name_predicate, pages, save_pages_as_images)

        # Save the updated pdf path + output dir to config
        self.save_config(pdf_path, output_dir)

        # Refresh UI with newly extracted images
        self.display_extracted_images(output_dir)
        messagebox.showinfo("Success", "Image extraction completed.")

    ##################################
    # File Browsing
    ##################################

    def browse_pdf(self):
        """
        Let user select a PDF, update pdf_entry, show preview from first page.
        Also store to config.
        """
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if pdf_path:
            self.pdf_entry.delete(0, tk.END)
            self.pdf_entry.insert(0, pdf_path)
            self.update_preview(0)
            # Save to config with current output as well
            self.save_config(pdf_path, self.output_entry.get().strip())

    def browse_output_dir(self):
        """
        Let user select an output directory,
        update output_entry, display images if any,
        also store to config.
        """
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, dir_path)
            self.display_extracted_images(dir_path)
            # Save to config with current pdf path
            self.save_config(self.pdf_entry.get().strip(), dir_path)

    def save_config(self, pdf_path, out_path):
        """
        Save last used PDF path and output directory
        so we can auto-populate them next time.
        """
        config_file = "last_paths.cfg"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(pdf_path + "\n")
                f.write(out_path + "\n")
        except:
            pass

    def load_config(self):
        """
        Load the last used PDF path and output directory from config.
        """
        config_file = "last_paths.cfg"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.read().splitlines()
                    if len(lines) >= 2:
                        self.last_pdf = lines[0].strip()
                        self.last_out = lines[1].strip()
            except:
                pass

######################################
# Launch the Application
######################################

if __name__ == "__main__":
    root = tb.Window(themename="superhero")
    app = PDFMasterGUI(root)
    root.mainloop()
