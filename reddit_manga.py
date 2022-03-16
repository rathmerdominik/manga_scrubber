import praw
import os
import configparser
import datetime
import sqlite3

CONF_DIR: str = os.environ["HOME"] + "/.config/manga_scrubber"
CONF_FILE: str = CONF_DIR + "/login_data.ini"
if os.path.exists(CONF_DIR):
    DB_CONN = sqlite3.connect(CONF_DIR + "/manga_scrubber.db")


class tcolors:
    RED = "\u001b[31m"
    GREEN = "\u001b[32m"
    BLUE = "\u001b[34m"
    END = "\033[0;0m"


def setup_login(username: str, password: str, client_id: str, client_secret: str):

    config = configparser.ConfigParser()
    if not os.path.exists(CONF_DIR):
        os.mkdir(CONF_DIR)

    config["DEFAULT"]["username"] = username
    config["DEFAULT"]["password"] = password
    config["DEFAULT"]["client_id"] = client_id
    config["DEFAULT"]["client_secret"] = client_secret

    with open(CONF_FILE, "w") as configfile:
        config.write(configfile)
        configfile.close()


def get_login_data() -> tuple:

    configfile = configparser.ConfigParser()
    configfile.read(CONF_FILE)

    username: str = configfile["DEFAULT"]["username"]
    password: str = configfile["DEFAULT"]["password"]
    client_id: str = configfile["DEFAULT"]["client_id"]
    client_secret: str = configfile["DEFAULT"]["client_secret"]

    return username, password, client_id, client_secret


def save_manga_submission(submission: dict) -> bool:
    c = DB_CONN.execute(
        "SELECT id FROM submissions WHERE title=?",
        (submission["title"],),
    )
    if c.fetchone() is None:
        DB_CONN.execute(
            "INSERT INTO submissions VALUES(null,?,?)",
            (submission["title"], submission["creation_date"]),
        )
        DB_CONN.commit()
    else:
        return False
    return True


def read_manga_submissions() -> tuple:
    c = DB_CONN.execute("SELECT id, title, creation_date FROM submissions")
    mangaset = c.fetchall()

    for row in mangaset:
        yield row


if __name__ == "__main__":
    try:

        if not os.path.isfile(CONF_FILE):
            print(
                "------------------------- Setting up Login ----------------------------- \n"
                "Please follow these steps in case you did not add a new app in Reddit \n"
                "https://github.com/reddit-archive/reddit/wiki/OAuth2-Quick-Start-Example#first-steps"
            )
            username: str = input("Please input your Reddit Username > ")
            password: str = input("Please input your Reddit Password > ")
            client_id: str = input("Please input your app's client id > ")
            client_secret: str = input("Pease input your client_secret    > ")

            setup_login(username, password, client_id, client_secret)

            DB_CONN.execute(
                "CREATE TABLE submissions( "
                "id INTEGER, "
                "title TEXT NOT NULL, "
                "creation_date DATE NOT NULL, "
                "PRIMARY KEY(id)"
                ")"
            )

            DB_CONN = sqlite3.connect(CONF_DIR + "/manga_scrubber.db")

            os.system("clear")

        username, password, client_id, client_secret = get_login_data()

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            password=password,
            user_agent="MangaScrubber by u/" + username,
            username=username,
        )

        for manga in read_manga_submissions():
            print(
                f"{tcolors.GREEN}{manga[0]} | {tcolors.RED} {manga[2]} - {tcolors.BLUE}{manga[1]}{tcolors.END}"
            )

        for submission in reddit.subreddit("manga").stream.submissions():
            if "[DISC]" in submission.title:
                sub_time = datetime.datetime.fromtimestamp(submission.created)
                save_manga_submission(
                    {
                        "title": submission.title.replace("[DISC] ", ""),
                        "creation_date": sub_time.strftime("%d-%m-%Y %H:%M:%S"),
                    }
                )

    except KeyboardInterrupt:
        print("\nGoodbye!")
        DB_CONN.close()
        exit(0)
