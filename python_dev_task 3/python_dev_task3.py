import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyttsx3
import PyPDF2
import threading
import time
import os

audio_output_path = "temp_audio.wav"


def select_pdf():
    filepath = filedialog.askopenfilename(
        title="Select PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )
    pdf_path_var.set(filepath)


def update_progress(value):
    progress_var.set(value)
    root.update_idletasks()


def convert_pdf_to_audio():
    pdf_file = pdf_path_var.get()

    if not pdf_file:
        messagebox.showerror("Error", "Please select a PDF file first!")
        return

    speed = int(speed_var.get())   # reading speed

    try:
        with open(pdf_file, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)

            extracted_text = ""
            total_pages = len(pdf_reader.pages)

            for i, page in enumerate(pdf_reader.pages):
                extracted_text += page.extract_text()
                update_progress(int((i + 1) / total_pages * 50))
                time.sleep(0.02)

        if extracted_text.strip() == "":
            messagebox.showerror("Error", "No readable text found!")
            return

        update_progress(60)

        # Convert text to speech using pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", speed)  # set speed
        engine.save_to_file(extracted_text, audio_output_path)
        engine.runAndWait()

        update_progress(100)

        play_button.config(state="normal")
        save_button.config(state="normal")

        messagebox.showinfo("Success", "Audio generated successfully!")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        update_progress(0)


def play_audio():
    def _play():
        engine = pyttsx3.init()
        engine.setProperty("rate", int(speed_var.get()))
        engine.play(audio_output_path)

    threading.Thread(target=_play, daemon=True).start()


def save_audio():
    save_path = filedialog.asksaveasfilename(
        title="Save Audio",
        defaultextension=".wav",
        filetypes=[("Audio Files", "*.wav")]
    )

    if save_path:
        os.replace(audio_output_path, save_path)
        messagebox.showinfo("Saved", "Audio saved successfully!")


# -------- GUI ----------

root = tk.Tk()
root.title("PDF to Audio Converter (Offline)")
root.geometry("480x420")

pdf_path_var = tk.StringVar()
progress_var = tk.IntVar()
speed_var = tk.IntVar(value=150)  # default rate

tk.Label(root, text="Select PDF File:", font=("Arial", 12)).pack(pady=10)
tk.Entry(root, textvariable=pdf_path_var, width=43).pack()
tk.Button(root, text="Browse", command=select_pdf).pack(pady=5)

tk.Button(root, text="Convert to Audio", bg="#4CAF50", fg="white",
          command=convert_pdf_to_audio).pack(pady=10)

# Speed control
tk.Label(root, text="Reading Speed (50 - 200):", font=("Arial", 12)).pack()
speed_slider = tk.Scale(root, from_=50, to=200,
                        orient="horizontal",
                        variable=speed_var,
                        length=250)
speed_slider.pack(pady=10)

# Progress bar
tk.Label(root, text="Progress:", font=("Arial", 12)).pack()
progress_bar = ttk.Progressbar(root, maximum=100,
                               variable=progress_var,
                               length=300)
progress_bar.pack(pady=10)

play_button = tk.Button(root, text="Play Audio",
                        state="disabled",
                        command=lambda: os.system(f'start {audio_output_path}'))
play_button.pack(pady=10)

save_button = tk.Button(root, text="Save Audio",
                        state="disabled",
                        command=save_audio)
save_button.pack(pady=5)

root.mainloop()
