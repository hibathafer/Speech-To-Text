import tkinter as tk
from tkinter import filedialog, messagebox
import speech_recognition as sr
import threading
import time

# =====================
# Main Window
# =====================
root = tk.Tk()
root.title("Speech to Text - Graduation Project")
root.geometry("1000x700")
root.resizable(True, True)

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

# =====================
# Global Variables
# =====================
recording = False
recognizer = sr.Recognizer()
timer_running = False
start_time = 0
timer_thread = None

# =====================
# Microphone Button
# =====================
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

# Additional buttons frame for save, clear, exit
action_buttons_frame = tk.Frame(main_frame)
action_buttons_frame.pack(fill="x", pady=10)

# =====================
# Button Functions
# =====================
def update_timer():
    """تحديث العداد بشكل مستمر"""
    global timer_running, start_time
    
    while timer_running:
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        try:
            timer_label.config(text=time_str)
            root.update_idletasks()
        except:
            pass
        
        time.sleep(0.1)

def record_audio():
    global recording, timer_running, start_time, timer_thread
    
    if not recording:
        # Start Recording
        recording = True
        timer_running = True
        start_time = time.time()
        
        mic_button.config(text="⏹️ Stop Recording", bg="#e74c3c")
        status_label.config(text="Status: Recording...", fg="red")
        
        # بدء عداد الوقت في thread منفصل
        timer_thread = threading.Thread(target=update_timer, daemon=True)
        timer_thread.start()
        
        # Run recording in a separate thread
        thread = threading.Thread(target=capture_audio, daemon=True)
        thread.start()
    else:
        # Stop Recording
        recording = False
        timer_running = False
        mic_button.config(text="🎙️ Start Recording", bg="#3498db")
        status_label.config(text="Status: Processing...", fg="orange")

def capture_audio():
    global recording
    try:
        with sr.Microphone() as source:
            status_label.config(text="Status: Listening...", fg="blue")
            audio_data = recognizer.listen(source, timeout=30)
            
        status_label.config(text="Status: Converting...", fg="purple")
        
        # Try to convert speech to text using Google API
        try:
            text = recognizer.recognize_google(audio_data, language="ar-SA")
            text_area.insert(tk.END, text + "\n")
            status_label.config(text="Status: Done", fg="green")
            
            # Copy to clipboard
            root.clipboard_clear()
            root.clipboard_append(text)
            
        except sr.UnknownValueError:
            messagebox.showwarning("Warning", "لم يتمكن النظام من فهم الصوت. حاول مرة أخرى.")
            status_label.config(text="Status: Idle", fg="gray")
        except sr.RequestError:
            messagebox.showerror("Error", "خطأ في الاتصال. تأكد من الإنترنت.")
            status_label.config(text="Status: Error", fg="red")
    except Exception as e:
        messagebox.showerror("Error", f"خطأ: {str(e)}")
        status_label.config(text="Status: Error", fg="red")
    finally:
        recording = False
        timer_running = False
        mic_button.config(text="🎙️ Start Recording", bg="#3498db")
        timer_label.config(text="00:00")

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
save_button = tk.Button(action_buttons_frame, text="💾 حفظ الملف", font=("Segoe UI", 11), width=12, bg="#27ae60", fg="white", relief="flat", command=save_text)
save_button.pack(side="left", padx=5)

clear_button = tk.Button(action_buttons_frame, text="🗑️ مسح النص", font=("Segoe UI", 11), width=12, bg="#f39c12", fg="white", relief="flat", command=clear_text)
clear_button.pack(side="left", padx=5)

exit_button = tk.Button(action_buttons_frame, text="الخروج", font=("Segoe UI", 11), width=12, bg="#e74c3c", fg="white", relief="flat", command=exit_app)
exit_button.pack(side="left", padx=5)

# Connect Microphone Button
mic_button.config(command=record_audio)

# Run App
# =====================
root.mainloop()