import customtkinter as ctk
from auth.login_view import LoginWindow
from views.main_view import App

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.withdraw() 
    login_window = LoginWindow(root)
    
    root.wait_window(login_window)

    if login_window.user_data:
        main_app = App(user_data=login_window.user_data)
        main_app.mainloop()
    else:
        print("Login failed or was cancelled. Exiting application.")
        root.destroy()