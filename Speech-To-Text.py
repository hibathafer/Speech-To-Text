import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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

# =====================
# Global Variables & Dialects (يجب تعريفها قبل الاستخدام)
# =====================
recording = False
paused = False
recognizer = sr.Recognizer()
timer_running = False
start_time = 0
paused_time = 0
timer_thread = None

# Arabic dialects
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

selected_dialect = "ar-SA"

# عداد الجمل
sentence_count = 0

# تحويل الأحرف الخاصة للهجات
def convert_special_characters(text):
    """
    تحويل الأصوات الخاصة إلى أحرف عربية:
    - صوت Ch يصبح چ (Jeem مع 3 نقاط)
    - صوت V يصبح ڤ (Faa مع نقطة فوق)
    """
    # تحويل الأصوات إلى الأحرف العربية
    text = text.replace('ch', 'چ')
    text = text.replace('Ch', 'چ')
    text = text.replace('CH', 'چ')
    
    text = text.replace('v', 'ڤ')
    text = text.replace('V', 'ڤ')
    text = text.replace('ف ع', 'ڤ')  # إذا كتبت "ف ع" بدل v
    
    return text

def format_text_output(text):
    """
    تنسيق النص وعرضه بطريقة منظمة مع:
    - رقم الجملة
    - الوقت والتاريخ
    - فاصل واضح
    """
    global sentence_count
    from datetime import datetime
    
    sentence_count += 1
    current_time = datetime.now().strftime("%H:%M:%S")
    
    # تنسيق الجملة
    formatted_text = f"\n【 جملة #{sentence_count} 】 [{current_time}]\n{text}\n" + ("=" * 60)
    
    return formatted_text

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
dialect_combo.set("العربية الفصحى (ar-SA)")
dialect_combo.pack(side="left", padx=5)

def on_dialect_change(event=None):
    global selected_dialect
    selected_dialect = ARABIC_DIALECTS[dialect_combo.get()]

dialect_combo.bind("<<ComboboxSelected>>", on_dialect_change)

# =====================
# Microphone Button
# =====================
mic_button = tk.Button(main_frame, text="🎙️ Start Recording", font=("Segoe UI", 14), width=20, height=2, bg="#3498db", fg="white", relief="flat")
mic_button.pack(pady=15)

# Control Buttons Frame
control_frame = tk.Frame(main_frame)
control_frame.pack(fill="x", pady=10)

pause_button = tk.Button(control_frame, text="⏸️ Pause", font=("Segoe UI", 11), width=10, bg="#a9b5eb", fg="white", relief="flat", state="disabled")
pause_button.pack(side="left", padx=5)

resume_button = tk.Button(control_frame, text="▶️ Resume", font=("Segoe UI", 11), width=10, bg="#9eebdc", fg="white", relief="flat", state="disabled")
resume_button.pack(side="left", padx=5)

# =====================
# Text Area + Scrollbar
# =====================
text_frame = tk.Frame(main_frame)
text_frame.pack(fill="both", expand=True, pady=10)

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side="right", fill="y")

text_area = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Segoe UI", 11))
text_area.pack(side="top", fill="both", expand=True)

scrollbar.config(command=text_area.yview)

# =====================
# Action Buttons Frame (يجب أن يكون بعد text_area)
# =====================
action_buttons_frame = tk.Frame(main_frame)
action_buttons_frame.pack(fill="x", pady=10)

# =====================
# Button Functions
# =====================
def update_timer():
    """تحديث العداد بشكل مستمر"""
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
            except:
                pass
        
        time.sleep(0.1)

def pause_recording():
    """إيقاف مؤقت للتسجيل"""
    global paused, start_time, paused_time
    
    if recording and not paused:
        paused = True
        paused_time = time.time() - start_time
        status_label.config(text="Status: Paused", fg="#9b59b6")
        pause_button.config(state="disabled")
        resume_button.config(state="normal")

def resume_recording():
    """استئناف التسجيل"""
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
        # Start Recording
        recording = True
        paused = False
        paused_time = 0
        timer_running = True
        start_time = time.time()
        
        mic_button.config(text="⏹️ Stop Recording", bg="#e74c3c")
        pause_button.config(state="normal")
        resume_button.config(state="disabled")
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
            status_label.config(text="Status: Listening...", fg="blue")
            audio_data = recognizer.listen(source, timeout=30)
            
        status_label.config(text="Status: Converting...", fg="purple")
        
        # Try to convert speech to text using Google API
        try:
            text = recognizer.recognize_google(audio_data, language=selected_dialect)
            # تحويل الأحرف الخاصة
            text = convert_special_characters(text)
            # تنسيق وعرض النص
            formatted_text = format_text_output(text)
            text_area.insert(tk.END, formatted_text)
            # تمرير تلقائي للأسفل
            text_area.see(tk.END)
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
    
    # إنشнякة لنسخ النص للمشاركة
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

# Exit Button
save_button = tk.Button(action_buttons_frame, text="💾 حفظ الملف", font=("Segoe UI", 11), width=12, bg="#27ae60", fg="white", relief="flat", command=save_text)
save_button.pack(side="left", padx=5)

copy_button = tk.Button(action_buttons_frame, text="📋 نسخ", font=("Segoe UI", 11), width=10, bg="#3498db", fg="white", relief="flat", command=copy_to_clipboard)
copy_button.pack(side="left", padx=5)

share_button = tk.Button(action_buttons_frame, text="📤 مشاركة", font=("Segoe UI", 11), width=12, bg="#1abc9c", fg="white", relief="flat", command=share_text)
share_button.pack(side="left", padx=5)

clear_button = tk.Button(action_buttons_frame, text="🗑️ مسح النص", font=("Segoe UI", 11), width=12, bg="#f39c12", fg="white", relief="flat", command=clear_text)
clear_button.pack(side="left", padx=5)

exit_button = tk.Button(action_buttons_frame, text="❌ الخروج", font=("Segoe UI", 11), width=10, bg="#e74c3c", fg="white", relief="flat", command=exit_app)
exit_button.pack(side="left", padx=5)

# Connect Microphone Button
mic_button.config(command=record_audio)
pause_button.config(command=pause_recording)
resume_button.config(command=resume_recording)

# Run App
# =====================
root.mainloop()