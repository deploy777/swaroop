import socket
import threading
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import base64
import os
import struct

username = input("Enter your name: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1', 5000))

connected = True
emoji_popup = None

def send_msg(sock, data):
    raw = data.encode('utf-8')
    header = struct.pack('>I', len(raw))
    sock.sendall(header + raw)

def recv_exact(sock, n):
    data = b''
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def recv_msg(sock):
    raw_header = recv_exact(sock, 4)
    if not raw_header:
        return None
    msg_len = struct.unpack('>I', raw_header)[0]
    raw_body = recv_exact(sock, msg_len)
    if not raw_body:
        return None
    return raw_body.decode('utf-8')

window = tk.Tk()
window.title(f"KIET Chat Client - {username}")
window.geometry("500x700")
window.configure(bg="#0f172a")
window.minsize(400, 500)

header = tk.Frame(window, bg="#1e293b", height=70)
header.pack(fill="x")
header.pack_propagate(False)

header_left = tk.Frame(header, bg="#1e293b")
header_left.pack(side="left", padx=15, pady=10)

tk.Label(header_left, text="KIET Engineering College", bg="#1e293b", fg="white",
         font=("Arial", 16, "bold")).pack(anchor="w")
tk.Label(header_left, text=f"Client Chat - {username}", bg="#1e293b", fg="#94a3b8",
         font=("Arial", 10)).pack(anchor="w")

status_frame = tk.Frame(header, bg="#1e293b")
status_frame.pack(side="right", padx=15)

status_dot = tk.Canvas(status_frame, width=12, height=12, bg="#1e293b", highlightthickness=0)
status_dot.create_oval(2, 2, 10, 10, fill="#22c55e", outline="#22c55e", tags="dot")
status_dot.pack(side="left", padx=(0, 5))

status_label = tk.Label(status_frame, text="Online", bg="#1e293b", fg="#22c55e",
                        font=("Arial", 9, "bold"))
status_label.pack(side="left")

top_frame = tk.Frame(window, bg="#0f172a")
top_frame.pack(fill="both", expand=True)

canvas = tk.Canvas(top_frame, bg="#0f172a", highlightthickness=0)
scrollbar = tk.Scrollbar(top_frame, command=canvas.yview)

scrollable_frame = tk.Frame(canvas, bg="#0f172a")
scrollable_frame.bind("<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas_win = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def on_canvas_resize(event):
    canvas.itemconfig(canvas_win, width=event.width)

canvas.bind("<Configure>", on_canvas_resize)
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

bottom_frame = tk.Frame(window, bg="#1e293b", height=70)
bottom_frame.pack(fill="x")
bottom_frame.pack_propagate(False)

msg_entry = tk.Entry(bottom_frame, font=("Arial", 12), bg="#334155", fg="white",
                     insertbackground="white", relief="flat")
msg_entry.pack(side="left", fill="x", expand=True, padx=(10,5), pady=15, ipady=8)
msg_entry.focus_set()

def add_message(message, sender):
    frame = tk.Frame(scrollable_frame, bg="#0f172a")
    time_str = datetime.now().strftime("%I:%M %p")

    if sender == "client":
        bf = tk.Frame(frame, bg="#0f172a")
        bf.pack(anchor="e", padx=10)
        tk.Label(bf, text=message, bg="#2563eb", fg="white", padx=15, pady=10,
                 wraplength=280, justify="left", font=("Arial", 10)).pack()
        tk.Label(bf, text=time_str, bg="#0f172a", fg="#64748b",
                 font=("Arial", 7)).pack(anchor="e")
    else:
        bf = tk.Frame(frame, bg="#0f172a")
        bf.pack(anchor="w", padx=10)
        tk.Label(bf, text=message, bg="#334155", fg="white", padx=15, pady=10,
                 wraplength=280, justify="left", font=("Arial", 10)).pack()
        tk.Label(bf, text=time_str, bg="#0f172a", fg="#64748b",
                 font=("Arial", 7)).pack(anchor="w")

    frame.pack(fill="x", pady=3)
    canvas.update_idletasks()
    canvas.yview_moveto(1.0)

def add_system_msg(message):
    frame = tk.Frame(scrollable_frame, bg="#0f172a")
    tk.Label(frame, text=f"- {message} -", bg="#0f172a", fg="#64748b",
             font=("Arial", 8, "italic")).pack(pady=5)
    frame.pack(fill="x", pady=2)
    canvas.update_idletasks()
    canvas.yview_moveto(1.0)

def set_disconnected():
    global connected
    connected = False
    status_dot.delete("dot")
    status_dot.create_oval(2, 2, 10, 10, fill="#ef4444", outline="#ef4444", tags="dot")
    status_label.config(text="Offline", fg="#ef4444")

def send_message(event=None):
    message = msg_entry.get().strip()
    if not message:
        return
    time_str = datetime.now().strftime("%I:%M %p")
    full_msg = f"{username}: {message} ({time_str})"
    try:
        send_msg(client, full_msg)
        add_message(full_msg, "client")
    except (BrokenPipeError, ConnectionResetError, OSError):
        set_disconnected()
        add_system_msg("Server disconnected")
    msg_entry.delete(0, tk.END)

EMOJIS = ["😊","😂","😍","🤔","😎","👍","👏","🙏",
          "❤️","🔥","🎉","💯","😢","😡","🤣","😜",
          "🥳","😇","🤗","👋","✅","⭐","💪","🎓"]

def add_emoji(emoji):
    msg_entry.insert(tk.END, emoji)
    msg_entry.focus_set()

def toggle_emoji_picker():
    global emoji_popup
    if emoji_popup and emoji_popup.winfo_exists():
        emoji_popup.destroy()
        emoji_popup = None
        return
    emoji_popup = tk.Toplevel(window)
    emoji_popup.title("Emojis")
    emoji_popup.geometry("300x160")
    emoji_popup.configure(bg="#1e293b")
    emoji_popup.resizable(False, False)
    emoji_popup.attributes("-topmost", True)
    gf = tk.Frame(emoji_popup, bg="#1e293b")
    gf.pack(padx=8, pady=8)
    for i, em in enumerate(EMOJIS):
        r, c = divmod(i, 8)
        tk.Button(gf, text=em, font=("Arial", 14), bg="#334155", fg="white",
                  relief="flat", width=2,
                  command=lambda e=em: add_emoji(e)).grid(row=r, column=c, padx=2, pady=2)

def send_file():
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        filename = os.path.basename(file_path)
        send_msg(client, f"FILE:{filename}:{content}")
        add_message(f"📁 You sent: {filename}", "client")
    except (BrokenPipeError, ConnectionResetError, OSError):
        set_disconnected()
        add_system_msg("Server disconnected")
    except Exception as e:
        add_system_msg(f"File send failed: {e}")

def send_image():
    file_path = filedialog.askopenfilename(
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")])
    if not file_path:
        return
    try:
        with open(file_path, "rb") as img:
            encoded = base64.b64encode(img.read()).decode()
        filename = os.path.basename(file_path)
        send_msg(client, f"IMAGE:{filename}:{encoded}")
        add_message(f"🖼️ You sent image: {filename}", "client")
    except (BrokenPipeError, ConnectionResetError, OSError):
        set_disconnected()
        add_system_msg("Server disconnected")
    except Exception as e:
        add_system_msg(f"Image send failed: {e}")

btn_cfg = {"fg": "white", "font": ("Arial", 10, "bold"), "relief": "flat",
           "padx": 10, "pady": 5, "cursor": "hand2"}

tk.Button(bottom_frame, text="Send", command=send_message,
          bg="#2563eb", activebackground="#1d4ed8", **btn_cfg).pack(side="right", padx=(3,10), pady=15)
tk.Button(bottom_frame, text="📁", command=send_file,
          bg="#2563eb", activebackground="#1d4ed8", **btn_cfg).pack(side="right", padx=3, pady=15)
tk.Button(bottom_frame, text="🖼️", command=send_image,
          bg="#2563eb", activebackground="#1d4ed8", **btn_cfg).pack(side="right", padx=3, pady=15)
tk.Button(bottom_frame, text="😊", command=toggle_emoji_picker,
          bg="#2563eb", activebackground="#1d4ed8", **btn_cfg).pack(side="right", padx=3, pady=15)

window.bind("<Return>", send_message)

def receive():
    while connected:
        try:
            msg = recv_msg(client)
            if msg is None:
                window.after(0, set_disconnected)
                window.after(0, add_system_msg, "Server disconnected")
                break

            if msg.startswith("IMAGE:"):
                _, filename, data = msg.split(":", 2)
                img_data = base64.b64decode(data)
                save_name = "received_" + filename
                with open(save_name, "wb") as f:
                    f.write(img_data)
                window.after(0, add_message, f"🖼️ Image received: {save_name}", "server")

            elif msg.startswith("FILE:"):
                _, name, content = msg.split(":", 2)
                fname = "received_" + os.path.basename(name)
                with open(fname, "w", encoding="utf-8") as f:
                    f.write(content)
                window.after(0, add_message, f"📁 Received file: {fname}", "server")

            else:
                window.after(0, add_message, msg, "server")

        except (ConnectionResetError, OSError):
            window.after(0, set_disconnected)
            window.after(0, add_system_msg, "Connection lost")
            break

threading.Thread(target=receive, daemon=True).start()

add_system_msg("Connected to server")

def on_close():
    global connected
    connected = False
    try:
        client.close()
    except OSError:
        pass
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_close)
window.mainloop()