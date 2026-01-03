import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests

API_BASE_URL = "http://127.0.0.1:8000"

window: tk.Tk
tree: ttk.Treeview
text_input: tk.Text
author_input: tk.Entry
tags_input: tk.Entry
status_label: tk.Label
btn_update: tk.Button
btn_delete: tk.Button
selected_quote_id: int | None = None


def update_status(message, clear_after=0):
    """更新狀態列文字"""
    status_label.config(text=message)
    if clear_after > 0:
        window.after(clear_after * 1000, lambda: status_label.config(text="就緒"))


def clear_inputs():
    """清空所有輸入框"""
    text_input.delete("1.0", tk.END)
    author_input.delete(0, tk.END)
    tags_input.delete(0, tk.END)


def reset_buttons():
    """重置按鈕為禁用狀態"""
    global selected_quote_id
    selected_quote_id = None
    btn_update.config(state=tk.DISABLED)
    btn_delete.config(state=tk.DISABLED)


#  Treeview 選取事件

def on_tree_select(event):
    """當使用者在 Treeview 選取項目時觸發"""
    global selected_quote_id
    
    selected_items = tree.selection()
    if not selected_items:
        return
    
    # 取得選中項目的資料
    item = tree.item(selected_items[0])
    values = item['values']
    
    if values:
        selected_quote_id = values[0]  # ID
        
        # 將資料填入輸入框
        clear_inputs()
        author_input.insert(0, values[1])  # Author
        text_input.insert("1.0", values[2])  # Text
        tags_input.insert(0, values[3])  # Tags
        
        # 啟用更新和刪除按鈕
        btn_update.config(state=tk.NORMAL)
        btn_delete.config(state=tk.NORMAL)
        
        # 更新狀態列顯示已選取的 ID
        update_status(f"已選取 ID: {selected_quote_id}")


def api_get_quotes():
    """取得所有名言"""
    try:
        response = requests.get(f"{API_BASE_URL}/quotes", timeout=10)
        response.raise_for_status()
        data = response.json()
        window.after(0, lambda: update_treeview_success(data))
    except requests.exceptions.ConnectionError:
        window.after(0, lambda: update_status("錯誤：無法連線至後端 API。請確認 API 是否已啟動。"))
    except requests.exceptions.RequestException as e:
        window.after(0, lambda: update_status(f"錯誤：{str(e)}"))


def api_create_quote(quote_data):
    """新增名言"""
    try:
        response = requests.post(f"{API_BASE_URL}/quotes", json=quote_data, timeout=10)
        response.raise_for_status()
        window.after(0, lambda: on_create_success())
    except requests.exceptions.ConnectionError:
        window.after(0, lambda: update_status("錯誤：無法連線至後端 API。請確認 API 是否已啟動。"))
    except requests.exceptions.RequestException as e:
        window.after(0, lambda: update_status(f"新增失敗：{str(e)}"))


def api_update_quote(quote_id, quote_data):
    """更新名言"""
    try:
        response = requests.put(f"{API_BASE_URL}/quotes/{quote_id}", json=quote_data, timeout=10)
        if response.status_code == 404:
            window.after(0, lambda: update_status("錯誤：操作失敗，找不到目標資料。"))
            return
        response.raise_for_status()
        window.after(0, lambda: on_update_success())
    except requests.exceptions.ConnectionError:
        window.after(0, lambda: update_status("錯誤：無法連線至後端 API。請確認 API 是否已啟動。"))
    except requests.exceptions.RequestException as e:
        window.after(0, lambda: update_status(f"更新失敗：{str(e)}"))


def api_delete_quote(quote_id):
    """刪除名言"""
    try:
        response = requests.delete(f"{API_BASE_URL}/quotes/{quote_id}", timeout=10)
        if response.status_code == 404:
            window.after(0, lambda: update_status("錯誤：操作失敗，找不到目標資料。"))
            return
        response.raise_for_status()
        window.after(0, lambda: on_delete_success())
    except requests.exceptions.ConnectionError:
        window.after(0, lambda: update_status("錯誤：無法連線至後端 API。請確認 API 是否已啟動。"))
    except requests.exceptions.RequestException as e:
        window.after(0, lambda: update_status(f"刪除失敗：{str(e)}"))


def update_treeview_success(data):
    """更新 Treeview 資料"""
    for item in tree.get_children():
        tree.delete(item)
    
    for quote in data:
        tree.insert("", tk.END, values=(
            quote['id'],
            quote['author'],
            quote['text'],
            quote['tags']
        ))
    
    current_status = status_label.cget("text")
    if "連線中" in current_status:
        update_status("資料載入完成")


def on_create_success():
    """[主執行緒] 新增成功後的處理"""
    update_status("新增成功！")
    clear_inputs()
    # 靜默重新整理列表（不改變狀態列訊息）
    do_refresh_silent()


def on_update_success():
    """[主執行緒] 更新成功後的處理"""
    update_status("更新成功！")
    clear_inputs()
    reset_buttons()
    do_refresh_silent()


def on_delete_success():
    """[主執行緒] 刪除成功後的處理"""
    update_status("刪除成功！")
    clear_inputs()
    reset_buttons()
    do_refresh_silent()


def do_refresh():
    """重新整理資料"""
    update_status("連線中，請稍候...")
    threading.Thread(target=api_get_quotes, daemon=True).start()


def do_refresh_silent():
    """靜默重新整理資料"""
    threading.Thread(target=api_get_quotes, daemon=True).start()


def do_add():
    """新增名言"""
    text = text_input.get("1.0", tk.END).strip()
    author = author_input.get().strip()
    tags = tags_input.get().strip()
    
    if not text or not author:
        messagebox.showwarning("警告", "名言內容和作者為必填欄位！")
        return
    
    quote_data = {
        "text": text,
        "author": author,
        "tags": tags
    }
    
    update_status("連線中，請稍候...")
    threading.Thread(target=api_create_quote, args=(quote_data,), daemon=True).start()


def do_update():
    """更新名言"""
    global selected_quote_id
    
    if selected_quote_id is None:
        messagebox.showwarning("警告", "請先選擇要更新的項目！")
        return
    
    text = text_input.get("1.0", tk.END).strip()
    author = author_input.get().strip()
    tags = tags_input.get().strip()
    
    if not text or not author:
        messagebox.showwarning("警告", "名言內容和作者為必填欄位！")
        return
    
    quote_data = {
        "text": text,
        "author": author,
        "tags": tags
    }
    
    update_status("連線中，請稍候...")
    threading.Thread(target=api_update_quote, args=(selected_quote_id, quote_data), daemon=True).start()


def do_delete():
    """刪除名言"""
    global selected_quote_id
    
    if selected_quote_id is None:
        messagebox.showwarning("警告", "請先選擇要刪除的項目！")
        return
    
    # 確認刪除
    if not messagebox.askyesno("確認刪除", "確定要刪除選取的名言嗎？"):
        return
    
    update_status("連線中，請稍候...")
    threading.Thread(target=api_delete_quote, args=(selected_quote_id,), daemon=True).start()


# 建立 GUI 介面

def create_gui():
    """建立主視窗介面"""
    global window, tree, text_input, author_input, tags_input
    global status_label, btn_update, btn_delete
    
    window = tk.Tk()
    window.title("名言佳句管理系統")
    window.geometry("800x600")
    window.resizable(True, True)
    
    tree_frame = tk.Frame(window)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    columns = ("ID", "Author", "Text", "Tags")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
    
    tree.heading("ID", text="ID")
    tree.heading("Author", text="作者")
    tree.heading("Text", text="名言內容")
    tree.heading("Tags", text="標籤")
    
    tree.column("ID", width=50, anchor=tk.CENTER)
    tree.column("Author", width=120, anchor=tk.W)
    tree.column("Text", width=450, anchor=tk.W)
    tree.column("Tags", width=150, anchor=tk.W)
    
    tree.bind("<<TreeviewSelect>>", on_tree_select)
    
    scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=tree.xview)
    tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    edit_frame = tk.LabelFrame(window, text="新增 / 編輯區", padx=10, pady=10)
    edit_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(edit_frame, text="名言內容 (Text):").grid(row=0, column=0, sticky=tk.W, pady=2)
    text_input = tk.Text(edit_frame, height=5, width=80)
    text_input.grid(row=1, column=0, columnspan=4, sticky=tk.W+tk.E, pady=2)
    
    tk.Label(edit_frame, text="作者 (Author):").grid(row=2, column=0, sticky=tk.W, pady=2)
    author_input = tk.Entry(edit_frame, width=40)
    author_input.grid(row=2, column=1, sticky=tk.W, pady=2)
    
    tk.Label(edit_frame, text="標籤 (Tags):").grid(row=2, column=2, sticky=tk.W, pady=2, padx=(20, 0))
    tags_input = tk.Entry(edit_frame, width=40)
    tags_input.grid(row=2, column=3, sticky=tk.W, pady=2)
    
    edit_frame.grid_columnconfigure(1, weight=1)
    edit_frame.grid_columnconfigure(3, weight=1)
    
    button_frame = tk.Frame(window)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    btn_refresh = tk.Button(button_frame, text="重新整理", width=12, command=do_refresh)
    btn_refresh.pack(side=tk.LEFT, padx=5)
    
    btn_add = tk.Button(button_frame, text="新增", width=12, command=do_add)
    btn_add.pack(side=tk.LEFT, padx=5)
    
    btn_update = tk.Button(button_frame, text="更新", width=12, command=do_update, state=tk.DISABLED)
    btn_update.pack(side=tk.LEFT, padx=5)
    
    btn_delete = tk.Button(button_frame, text="刪除", width=12, command=do_delete, state=tk.DISABLED)
    btn_delete.pack(side=tk.LEFT, padx=5)
    
    # 清空按鈕
    btn_clear = tk.Button(button_frame, text="清空輸入", width=12, command=lambda: [clear_inputs(), reset_buttons()])
    btn_clear.pack(side=tk.RIGHT, padx=5)
    
    status_label = tk.Label(window, text="就緒", relief=tk.SUNKEN, anchor=tk.W, padx=10)
    status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=5)
    
    window.after(100, do_refresh)
    
    return window


#  主程式 

def main():
    """主程式進入點"""
    window = create_gui()
    window.mainloop()


if __name__ == "__main__":
    main()
