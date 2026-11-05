from database.connection import ensure_database
from database.seed import seed_default_data
from interfaces.login import LoginWindow


def main():
    ensure_database()
    seed_default_data()
    window = LoginWindow()
    window.mainloop()


if __name__ == "__main__":
    main()
