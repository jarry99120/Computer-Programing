import tkinter as tk
root = tk.Tk()
root.title("測試 Tkinter")
root.geometry("400x200")
label = tk.Label(root, text="如果看到這個視窗，就代表 Tkinter 正常！", font=("Noto Sans CJK TC", 14))
label.pack(pady=50)
root.mainloop()
