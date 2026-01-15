import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import speech_recognition as sr
import threading
import time
import os
import configparser
import logging

# Setup logging and config
logging.basicConfig(filename='speech_to_text.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
config = configparser.ConfigParser()
config_file = 'settings.ini'
if not os.path.exists(config_file):
    config['Settings'] = {'dialect': 'ar-SA'}
    with open(config_file, 'w') as f: config.write(f)
else:
    config.read(config_file)

# Main Window
root = tk.Tk()
root.title("Speech to Text - Graduation Project")
root.geometry("1000x700")
root.resizable(True, True)

# Top Bar
top_bar = tk.Frame(root, bg="#2c3e50", height=50)
top_bar.pack(fill="x")
top_bar.pack_propagate(False)
title_label = tk.Label(top_bar, text="Speech to Text Converter", bg="#2c3e50", fg="white", font=("Segoe UI", 14, "bold"))
title_label.pack(side="left", padx=20)

# Main Content
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

# Global Variables
recording = False
paused = False
recognizer = sr.Recognizer()
timer_running = False
start_time = 0
paused_time = 0
timer_thread = None

ARABIC_DIALECTS = {
    "العربية الفصحى (ar-SA)": "ar-SA",
    "السعودية (ar-SA)": "ar-SA",
    "المصرية (ar-EG)": "ar-EG",
    "الإمارات (ar-AE)": "ar-AE",
    "الجزائر (ar-DZ)": "ar-DZ",
    "المغرب (ar-MA)": "ar-MA",
    "الأردن/الشام (ar-JO)": "ar-JO",
    "لبنان/الشام (ar-LB)": "ar-LB",
    "تونس (ar-TN)": "ar-TN",
    "الكويت (ar-KW)": "ar-KW",
    "العراقية (ar-IQ)": "ar-IQ",
    "عام (ar)": "ar",
}
selected_dialect = config['Settings'].get('dialect', 'ar-SA')
sentence_count = 0

# تحويل الأحرف الخاصة للهجات
def convert_special_characters(text):
    """تحويل الأصوات الخاصة إلى أحرف عربية"""
    text = text.replace('ch', 'چ').replace('Ch', 'چ').replace('CH', 'چ')
    text = text.replace('v', 'ڤ').replace('V', 'ڤ').replace('ف ع', 'ڤ')
    return text

def format_text_output(text):
    """تنسيق النص وعرضه"""
    global sentence_count
    sentence_count += 1
    current_time = time.strftime("%H:%M:%S")
    return f"\n【 جملة #{sentence_count} 】 [{current_time}]\n{text}\n" + ("=" * 60)

# =====================
# Status Label
# =====================
status_label = tk.Label(main_frame, text="Status: Idle", font=("Segoe UI", 11), fg="gray")
status_label.pack(anchor="w")

# Timer Label
timer_label = tk.Label(main_frame, text="00:00", font=("Segoe UI", 12, "bold"))
timer_label.pack(anchor="center", pady=10)

# Dialect Selection Frame
dialect_frame = tk.Frame(main_frame)
dialect_frame.pack(fill="x", pady=10)

dialect_label = tk.Label(dialect_frame, text="اختر اللهجة:", font=("Segoe UI", 10))
dialect_label.pack(side="left", padx=5)

dialect_combo = ttk.Combobox(dialect_frame, values=list(ARABIC_DIALECTS.keys()), 
                              state="readonly", font=("Segoe UI", 10), width=30)
dialect_combo.set([k for k, v in ARABIC_DIALECTS.items() if v == selected_dialect][0])
dialect_combo.pack(side="left", padx=5)

def on_dialect_change(event=None):
    global selected_dialect
    selected_dialect = ARABIC_DIALECTS[dialect_combo.get()]
    config['Settings']['dialect'] = selected_dialect
    with open(config_file, 'w') as f:
        config.write(f)
    logging.info(f"Dialect changed to: {selected_dialect}")

dialect_combo.bind("<<ComboboxSelected>>", on_dialect_change)

# =====================
# Text Area + Scrollbar (moved early for function access)
# =====================
text_frame = tk.Frame(main_frame, bg="#ffffff", relief="sunken", bd=2)

scrollbar = tk.Scrollbar(text_frame)

text_area = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Segoe UI", 12), bg="#f9f9f9", fg="#333333", insertbackground="#333333")

scrollbar.config(command=text_area.yview)

def update_timer():
    """تحديث العداد"""
    global timer_running, start_time, paused_time, paused
    while timer_running:
        if not paused:
            elapsed_time = time.time() - start_time - paused_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            try:
                timer_label.config(text=time_str)
                root.update_idletasks()
            except: pass
        time.sleep(0.1)

def pause_recording():
    """إيقاف مؤقت"""
    global paused, start_time, paused_time
    if recording and not paused:
        paused = True
        paused_time = time.time() - start_time
        status_label.config(text="Status: Paused", fg="#9b59b6")
        pause_button.config(state="disabled")
        resume_button.config(state="normal")

def resume_recording():
    """استئناف"""
    global paused, start_time, paused_time
    if recording and paused:
        paused = False
        start_time = time.time() - paused_time
        status_label.config(text="Status: Recording...", fg="red")
        pause_button.config(state="normal")
        resume_button.config(state="disabled")

def record_audio():
    global recording, timer_running, start_time, timer_thread, paused, paused_time
    if not recording:
        recording = True
        paused = False
        paused_time = 0
        timer_running = True
        start_time = time.time()
        mic_button.config(text="⏹️ Stop Recording", bg="#e74c3c")
        pause_button.config(state="normal")
        resume_button.config(state="disabled")
        status_label.config(text="Status: Recording...", fg="red")
        timer_thread = threading.Thread(target=update_timer, daemon=True)
        timer_thread.start()
        thread = threading.Thread(target=capture_audio, daemon=True)
        thread.start()
    else:
        recording = False
        paused = False
        timer_running = False
        mic_button.config(text="🎙️ Start Recording", bg="#3498db")
        pause_button.config(state="disabled")
        resume_button.config(state="disabled")
        status_label.config(text="Status: Processing...", fg="orange")

def capture_audio():
    global recording
    try:
        with sr.Microphone() as source:
            status_label.config(text="Status: Adjusting for noise...", fg="orange")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            status_label.config(text="Status: Listening...", fg="blue")
            audio_data = recognizer.listen(source, timeout=60, phrase_time_limit=10)
        status_label.config(text="Status: Converting...", fg="purple")
        text = recognizer.recognize_google(audio_data, language=selected_dialect)
        text = convert_special_characters(text)
        formatted_text = format_text_output(text)
        text_area.insert(tk.END, formatted_text)
        text_area.see(tk.END)
        status_label.config(text="Status: Done", fg="green")
        root.clipboard_clear()
        root.clipboard_append(text)
        logging.info("Speech recognized and converted successfully")
    except sr.UnknownValueError:
        messagebox.showwarning("Warning", "لم يتمكن النظام من فهم الصوت. حاول مرة أخرى.")
        status_label.config(text="Status: Idle", fg="gray")
        logging.warning("Unknown value error during speech recognition")
    except sr.RequestError:
        messagebox.showerror("Error", "خطأ في الاتصال. تأكد من الإنترنت.")
        status_label.config(text="Status: Error", fg="red")
        logging.error("Request error during speech recognition")
    except Exception as e:
        messagebox.showerror("Error", f"خطأ: {str(e)}")
        status_label.config(text="Status: Error", fg="red")
        logging.error(f"Unexpected error during speech recognition: {str(e)}")
    finally:
        recording = False
        paused = False
        timer_running = False
        mic_button.config(text="🎙️ Start Recording", bg="#3498db")
        pause_button.config(state="disabled")
        resume_button.config(state="disabled")
        timer_label.config(text="00:00")

def clear_text():
    global sentence_count
    text_area.delete("1.0", tk.END)
    sentence_count = 0  # إعادة تعيين عداد الجمل

def load_audio_file():
    file_path = filedialog.askopenfilename(
        title="اختر ملف صوتي",
        filetypes=[("Audio files", "*.wav *.flac *.mp3"), ("All files", "*.*")]
    )
    if file_path:
        status_label.config(text="Status: Loading file...", fg="blue")
        thread = threading.Thread(target=convert_audio_file, args=(file_path,), daemon=True)
        thread.start()

def convert_audio_file(file_path):
    try:
        status_label.config(text="Status: Converting file...", fg="purple")
        with sr.AudioFile(file_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language=selected_dialect)
        text = convert_special_characters(text)
        formatted_text = format_text_output(text)
        text_area.insert(tk.END, formatted_text)
        text_area.see(tk.END)
        status_label.config(text="Status: Done", fg="green")
        logging.info(f"Converted audio file: {file_path}")
    except sr.UnknownValueError:
        messagebox.showwarning("Warning", "لم يتمكن النظام من فهم الصوت في الملف.")
        status_label.config(text="Status: Idle", fg="gray")
        logging.warning(f"Unknown value in file: {file_path}")
    except sr.RequestError:
        messagebox.showerror("Error", "خطأ في الاتصال. تأكد من الإنترنت.")
        status_label.config(text="Status: Error", fg="red")
        logging.error(f"Request error for file: {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"خطأ: {str(e)}")
        status_label.config(text="Status: Error", fg="red")
        logging.error(f"Error converting file {file_path}: {str(e)}")

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

def copy_to_clipboard():
    """نسخ كل النص للحافظة"""
    text = text_area.get("1.0", tk.END)
    if text.strip():
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("نسخ", "تم نسخ النص إلى الحافظة! ✅")
    else:
        messagebox.showwarning("تحذير", "لا يوجد نص للنسخ!")

def share_text():
    """مشاركة النص عبر وسائل التواصل"""
    text = text_area.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("تحذير", "لا يوجد نص للمشاركة!")
        return
    
    # إنشاء نسخة لنسخ النص للمشاركة
    root.clipboard_clear()
    root.clipboard_append(text)
    messagebox.showinfo("مشاركة", 
        "تم نسخ النص! \n\n"
        "يمكنك الآن لصقه في:\n"
        "📱 WhatsApp\n"
        "📘 Facebook\n"
        "🐦 Twitter\n"
        "📧 البريد الإلكتروني\n"
        "وغيرها...")

# Microphone Button
mic_button = tk.Button(main_frame, text="🎙️ Start Recording", font=("Segoe UI", 14, "bold"), width=25, height=2, bg="#3498db", fg="white", relief="raised", bd=3)
mic_button.pack(pady=15)

# Control Buttons Frame
control_frame = tk.Frame(main_frame, bg="#f0f0f0", relief="groove", bd=2)
control_frame.pack(fill="x", pady=10)

pause_button = tk.Button(control_frame, text="⏸️ Pause", font=("Segoe UI", 12, "bold"), width=15, height=2, bg="#f39c12", fg="white", relief="raised", bd=2, state="disabled")
pause_button.pack(side="left", padx=10, pady=5, expand=True)

resume_button = tk.Button(control_frame, text="▶️ Resume", font=("Segoe UI", 12, "bold"), width=15, height=2, bg="#27ae60", fg="white", relief="raised", bd=2, state="disabled")
resume_button.pack(side="left", padx=10, pady=5, expand=True)

# Action Buttons Frame
action_buttons_frame = tk.Frame(main_frame, bg="#f0f0f0", relief="groove", bd=2)
action_buttons_frame.pack(fill="x", pady=10)

load_button = tk.Button(action_buttons_frame, text="📁 تحميل ملف صوتي", font=("Segoe UI", 11, "bold"), width=18, height=2, bg="#9b59b6", fg="white", relief="raised", bd=2, command=load_audio_file)
load_button.pack(side="left", padx=5, pady=5, expand=True)

save_button = tk.Button(action_buttons_frame, text="💾 حفظ الملف", font=("Segoe UI", 11, "bold"), width=15, height=2, bg="#27ae60", fg="white", relief="raised", bd=2, command=save_text)
save_button.pack(side="left", padx=5, pady=5, expand=True)

copy_button = tk.Button(action_buttons_frame, text="📋 نسخ", font=("Segoe UI", 11, "bold"), width=12, height=2, bg="#3498db", fg="white", relief="raised", bd=2, command=copy_to_clipboard)
copy_button.pack(side="left", padx=5, pady=5, expand=True)

share_button = tk.Button(action_buttons_frame, text="📤 مشاركة", font=("Segoe UI", 11, "bold"), width=15, height=2, bg="#1abc9c", fg="white", relief="raised", bd=2, command=share_text)
share_button.pack(side="left", padx=5, pady=5, expand=True)

clear_button = tk.Button(action_buttons_frame, text="🗑️ مسح النص", font=("Segoe UI", 11, "bold"), width=15, height=2, bg="#e67e22", fg="white", relief="raised", bd=2, command=clear_text)
clear_button.pack(side="left", padx=5, pady=5, expand=True)

exit_button = tk.Button(action_buttons_frame, text="❌ الخروج", font=("Segoe UI", 11, "bold"), width=12, height=2, bg="#e74c3c", fg="white", relief="raised", bd=2, command=exit_app)
exit_button.pack(side="left", padx=5, pady=5, expand=True)

# Text Area + Scrollbar
text_frame.pack(fill="both", expand=True, pady=10)
scrollbar.pack(side="right", fill="y")
text_area.pack(side="top", fill="both", expand=True)

# Connect buttons
mic_button.config(command=record_audio)
pause_button.config(command=pause_recording)
resume_button.config(command=resume_recording)

# Run App
root.mainloop()