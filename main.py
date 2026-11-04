from database.connection import initialize_database
from database.seed import seed_default_data
from interfaces.login import LoginWindow


def main():
    initialize_database()
    seed_default_data()
    window = LoginWindow()
    window.mainloop()


if __name__ == "__main__":
    main()
