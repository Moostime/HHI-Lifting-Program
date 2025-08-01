import customtkinter as ctk
from auth.auth_dal import login_user

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Login")
        self.geometry("300x250")
        self.user_data = None

        self.user_label = ctk.CTkLabel(self, text="Username:")
        self.user_label.pack(pady=(20, 5))
        self.user_entry = ctk.CTkEntry(self)
        self.user_entry.pack(pady=5, padx=20, fill="x")

        self.pass_label = ctk.CTkLabel(self, text="Password:")
        self.pass_label.pack(pady=(10, 5))
        self.pass_entry = ctk.CTkEntry(self, show="*")
        self.pass_entry.pack(pady=5, padx=20, fill="x")

        self.login_button = ctk.CTkButton(self, text="Login", command=self.attempt_login)
        self.login_button.pack(pady=20)
        
        self.pass_entry.bind("<Return>", self.attempt_login)
        self.protocol("WM_DELETE_WINDOW", self.cancel_login)
        self.after(100, self.user_entry.focus_set)
        self.lift()
        self.attributes("-topmost", True)

    def attempt_login(self, event=None):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        if username and password:
            self.user_data = login_user(username, password)
            if self.user_data:
                print("Login successful.")
                self.destroy()
            else:
                self.pass_entry.delete(0, 'end')
                print("Login failed. Invalid username or password.")
    
    def cancel_login(self):
        self.user_data = None
        self.destroy()