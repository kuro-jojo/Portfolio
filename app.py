import datetime
from dotenv import load_dotenv

load_dotenv()

import logging
import socket
from logging.handlers import SysLogHandler
import os
from flask import Flask, render_template, request, redirect, url_for
from src.models.UserMessage import UserMessage
from src.models import UserMessage

from src.modules.form import fetch_contact_data

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///portfolio.db"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS '] = False
db = UserMessage.db
db.init_app(app)


@app.route("/")
def home():
    """ Send to homepage """
    
    with open("user_visits.txt", "a") as f:
        f.write("IP : " + request.remote_addr)
        f.write("\t")
        f.write("On : " + datetime.datetime.now().strftime("%d-%m-%Y at %H:%M:%S"))
        f.write("\t")
        f.write("\t")
        f.write("Browser : " + request.headers.get("User-Agent").split(" ")[0])
        f.write("\n")
    return render_template("index.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """save a message from the user into a databse

    Returns:
        Response: redirection to the homepage
    """
    if request.method == "POST":
        try:
            userMessage = fetch_contact_data(request.form)
            db.session.add(userMessage)
            db.session.commit()
            return "Message sent successfully ."
        except Exception as e:
            print(f"Exception found : {e}")
            return redirect(url_for("home"))

    return redirect(url_for("home"))


# @app.before_request
# def init():
#     """Initialize some configurations"""
#     # create tables
#     with app.app_context():
#         db.create_all()

@app.before_request
def log():
    """ Logs message to a remote log viewer"""
    if not paperTrailAppUrl and not paperTrailAppPort:
        raise TypeError("An url and a port is requested")
    
    syslog = SysLogHandler(address=(paperTrailAppUrl, paperTrailAppPort))
    print(paperTrailAppPort, paperTrailAppUrl)
    syslog.addFilter(ContextFilter())

    format = "%(asctime)s %(hostname)s - %(message)s"
    formatter = logging.Formatter(format, datefmt="%b %d %H:%M:%S")
    syslog.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(syslog)
    logger.setLevel(logging.INFO)
    message = request.headers.get('User-Agent').split(' ')[0]
    logger.info(f"Browser : {message}")
    
class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True

if __name__ == "__main__":
    paperTrailAppUrl = os.getenv("PAPER_TRAIL_URL")
    paperTrailAppPort = os.getenv("PAPER_TRAIL_PORT")
    app.run(host="0.0.0.0", debug=True)
