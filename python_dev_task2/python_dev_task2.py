import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
from pathlib import Path
import threading

class ImageConverterResizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Converter & Resizer")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables
        self.images = []
        self.output_folder = tk.StringVar(value=os.getcwd())
        self.quality = tk.IntVar(value=85)
        self.resize_width = tk.IntVar(value=800)
        self.resize_height = tk.IntVar(value=600)
        self.keep_aspect = tk.BooleanVar(value=True)
        self.format_var = tk.StringVar(value="Same as original")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Image Converter & Resizer", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Upload Section
        upload_frame = ttk.LabelFrame(main_frame, text="Upload Images", padding="10")
        upload_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        upload_frame.columnconfigure(1, weight=1)
        
        ttk.Button(upload_frame, text="Select Images", 
                  command=self.select_images).grid(row=0, column=0, padx=(0, 10))
        
        self.upload_status = ttk.Label(upload_frame, text="No images selected")
        self.upload_status.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Selected files list
        self.files_listbox = tk.Listbox(upload_frame, height=4)
        self.files_listbox.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Clear selection button
        ttk.Button(upload_frame, text="Clear Selection", 
                  command=self.clear_selection).grid(row=2, column=0, pady=(10, 0))
        
        # Processing Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Processing Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # Format conversion
        ttk.Label(options_frame, text="Convert to:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var,
                                   values=["Same as original", "JPEG", "PNG", "WEBP", "BMP"])
        format_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        format_combo.set("Same as original")
        
        # Quality/Compression
        ttk.Label(options_frame, text="Quality (JPEG):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        quality_scale = ttk.Scale(options_frame, from_=1, to=100, variable=self.quality,
                                 orient=tk.HORIZONTAL)
        quality_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.quality_label = ttk.Label(options_frame, text="85%")
        self.quality_label.grid(row=1, column=2)
        
        # Resize options
        ttk.Label(options_frame, text="Resize to:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10))
        
        resize_frame = ttk.Frame(options_frame)
        resize_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Entry(resize_frame, textvariable=self.resize_width, width=6).grid(row=0, column=0)
        ttk.Label(resize_frame, text="x").grid(row=0, column=1, padx=5)
        ttk.Entry(resize_frame, textvariable=self.resize_height, width=6).grid(row=0, column=2)
        ttk.Checkbutton(resize_frame, text="Keep aspect ratio", 
                       variable=self.keep_aspect).grid(row=0, column=3, padx=(20, 0))
        
        # Output location
        ttk.Label(options_frame, text="Output folder:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(options_frame, textvariable=self.output_folder).grid(row=3, column=1, sticky=(tk.W, tk.E))
        ttk.Button(options_frame, text="Browse", 
                  command=self.select_output_folder).grid(row=3, column=2, padx=(10, 0))
        
        # Bind events
        quality_scale.configure(command=self.update_quality_label)
        self.resize_width.trace('w', self.update_aspect_ratio)
        self.resize_height.trace('w', self.update_aspect_ratio)
        
        # Preview Section
        preview_frame = ttk.LabelFrame(main_frame, text="Image Preview", padding="10")
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        self.preview_label = ttk.Label(preview_frame, text="Select an image to preview", 
                                      background="white", anchor=tk.CENTER)
        self.preview_label.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bind listbox selection event
        self.files_listbox.bind('<<ListboxSelect>>', self.show_preview)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Process Images", 
                  command=self.process_images, style="Accent.TButton").grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="Clear All", 
                  command=self.clear_all).grid(row=0, column=1, padx=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Ready")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=(5, 0))
        
    def update_quality_label(self, value):
        self.quality_label.config(text=f"{int(float(value))}%")
        
    def update_aspect_ratio(self, *args):
        if self.keep_aspect.get() and hasattr(self, 'current_image'):
            try:
                if self.resize_width.get() != self.original_width:
                    new_height = int((self.resize_width.get() / self.original_width) * self.original_height)
                    self.resize_height.set(new_height)
                elif self.resize_height.get() != self.original_height:
                    new_width = int((self.resize_height.get() / self.original_height) * self.original_width)
                    self.resize_width.set(new_width)
            except (AttributeError, ValueError):
                pass
        
    def select_images(self):
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("All files", "*.*")
            ]
        )
        
        if files:
            self.images = list(files)
            self.files_listbox.delete(0, tk.END)
            for file in self.images:
                self.files_listbox.insert(tk.END, os.path.basename(file))
            self.upload_status.config(text=f"{len(self.images)} image(s) selected")
            
    def clear_selection(self):
        self.images = []
        self.files_listbox.delete(0, tk.END)
        self.upload_status.config(text="No images selected")
        self.preview_label.config(image='', text="Select an image to preview")
        
    def clear_all(self):
        self.clear_selection()
        self.progress['value'] = 0
        self.status_label.config(text="Ready")
        
    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            
    def show_preview(self, event):
        selection = self.files_listbox.curselection()
        if not selection:
            return
            
        file_path = self.images[selection[0]]
        try:
            image = Image.open(file_path)
            self.original_width, self.original_height = image.size
            
            # Resize for preview while maintaining aspect ratio
            preview_size = (300, 200)
            image.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # Keep a reference
            
            # Update resize fields with original dimensions
            self.resize_width.set(self.original_width)
            self.resize_height.set(self.original_height)
            self.current_image = image
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image: {str(e)}")
            
    def process_images(self):
        if not self.images:
            messagebox.showwarning("Warning", "Please select at least one image to process.")
            return
            
        # Run processing in a separate thread to keep UI responsive
        thread = threading.Thread(target=self._process_images_thread)
        thread.daemon = True
        thread.start()
        
    def _process_images_thread(self):
        try:
            total_images = len(self.images)
            processed = 0
            
            # Create output folder if it doesn't exist
            output_path = Path(self.output_folder.get())
            output_path.mkdir(exist_ok=True)
            
            for i, image_path in enumerate(self.images):
                try:
                    self.status_label.config(text=f"Processing {i+1}/{total_images}: {os.path.basename(image_path)}")
                    
                    # Update progress
                    self.progress['value'] = (i / total_images) * 100
                    self.root.update_idletasks()
                    
                    # Process image
                    self.process_single_image(image_path, output_path)
                    processed += 1
                    
                except Exception as e:
                    print(f"Error processing {image_path}: {str(e)}")
                    continue
                    
            # Final update
            self.progress['value'] = 100
            self.status_label.config(text=f"Completed! {processed}/{total_images} images processed successfully.")
            
            messagebox.showinfo("Success", 
                              f"Processing completed!\n{processed}/{total_images} images processed successfully.")
                              
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed: {str(e)}")
            self.status_label.config(text="Processing failed")
            
    def process_single_image(self, image_path, output_path):
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize image
            if self.resize_width.get() != img.width or self.resize_height.get() != img.height:
                if self.keep_aspect.get():
                    img = self.resize_with_aspect(img, self.resize_width.get(), self.resize_height.get())
                else:
                    img = img.resize((self.resize_width.get(), self.resize_height.get()), Image.Resampling.LANCZOS)
            
            # Determine output format
            if self.format_var.get() == "Same as original":
                output_format = img.format or 'JPEG'
            else:
                output_format = self.format_var.get()
            
            # Prepare output filename
            original_name = Path(image_path).stem
            extension = self.get_extension(output_format)
            output_file = output_path / f"{original_name}_processed{extension}"
            
            # Save with appropriate options
            save_kwargs = {}
            if output_format.upper() == 'JPEG':
                save_kwargs['quality'] = self.quality.get()
                save_kwargs['optimize'] = True
            elif output_format.upper() == 'PNG':
                save_kwargs['optimize'] = True
            elif output_format.upper() == 'WEBP':
                save_kwargs['quality'] = self.quality.get()
            
            img.save(output_file, format=output_format, **save_kwargs)
    
    def resize_with_aspect(self, image, target_width, target_height):
        """Resize image while maintaining aspect ratio"""
        original_width, original_height = image.size
        ratio = min(target_width / original_width, target_height / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def get_extension(self, format_name):
        """Get file extension for given format"""
        extensions = {
            'JPEG': '.jpg',
            'JPG': '.jpg',
            'PNG': '.png',
            'WEBP': '.webp',
            'BMP': '.bmp',
            'GIF': '.gif',
            'TIFF': '.tiff'
        }
        return extensions.get(format_name.upper(), '.jpg')

def main():
    root = tk.Tk()
    app = ImageConverterResizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
