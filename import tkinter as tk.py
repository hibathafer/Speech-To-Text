import tkinter as tk
from tkinter import filedialog, messagebox

# =====================
# Main Window
# =====================
root = tk.Tk()
root.title("Speech to Text - Graduation Project")
root.geometry("1000x700")
root.resizable(False, False)

# =====================
# Top Bar
# =====================
top_bar = tk.Frame(root, bg="#2c3e50", height=50)
top_bar.pack(fill="x")
top_bar.pack_propagate(False)  # يخلي ارتفاع الشريط ثابت

title_label = tk.Label(
    top_bar,
    text="Speech to Text Converter",
    bg="#2c3e50",
    fg="white",
    font=("Segoe UI", 14, "bold")
)
title_label.pack(side="left", padx=20)

# =====================
# Main Content
# =====================
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Status Label
status_label = tk.Label(main_frame, text="Status: Idle", font=("Segoe UI", 11), fg="gray")
status_label.pack(anchor="w")

# Timer Label
timer_label = tk.Label(main_frame, text="00:00", font=("Segoe UI", 12, "bold"))
timer_label.pack(anchor="center", pady=10)

# Microphone Button
mic_button = tk.Button(main_frame, text="🎙️ Start Recording", font=("Segoe UI", 14), width=20, height=2, bg="#3498db", fg="white", relief="flat")
mic_button.pack(pady=15)

# =====================
# Text Area + Scrollbar
# =====================
text_frame = tk.Frame(main_frame)
text_frame.pack(fill="both", expand=True)

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side="right", fill="y")

text_area = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Segoe UI", 11))
text_area.pack(side="top", fill="both", expand=True)

scrollbar.config(command=text_area.yview)

# =====================
# Buttons Frame
# =====================
buttons_frame = tk.Frame(main_frame)
buttons_frame.pack(fill="x", pady=15)

# =====================
# Button Functions
# =====================
def copy_text():
    root.clipboard_clear()
    root.clipboard_append(text_area.get("1.0", tk.END))
    messagebox.showinfo("Copy", "Text copied to clipboard!")

def clear_text():
    text_area.delete("1.0", tk.END)

def save_text():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_area.get("1.0", tk.END))
        messagebox.showinfo("Save", f"File saved at:\n{file_path}")

def exit_app():
    root.quit()

# Exit Button
exit_button = tk.Button(buttons_frame, text="الخروج", font=("Segoe UI", 12), width=15, bg="#e74c3c", fg="white", relief="flat", command=exit_app)
exit_button.pack(pady=15)

# Run App
# =====================
root.mainloop()