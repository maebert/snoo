import arrow
import requests
import getpass
import configparser
import xdg.BaseDirectory
import os


class APIError(Exception):
    def __init__(self, url, status, response):
        self.url = url
        self.status = status
        self.response = response


class Client:
    USER_AGENT = "SNOO/351 CFNetwork/1121.2 Darwin/19.2.0"
    BASE_URL = "https://snoo-api.happiestbaby.com"
    LOGIN_ENDPOINT = "/us/login"
    DATA_ENDPOINT = "/ss/v2/sessions/aggregated"
    CURRENT_ENDPOINT = "/ss/v2/sessions/last"

    def __init__(self):
        self._config_path = None
        self._config = configparser.ConfigParser()
        self._config.read(self.config_path)

        if "default" not in self._config:
            self._config["default"] = {
                "update_interval": "60",
            }
        self.config = self._config["default"]

        if "auth" not in self._config:
            self._config["auth"] = {
                "username": "",
                "password": "",
                "token": "",
                "token_expiry": "",
                "refresh_token": "",
            }
        self.auth = self._config["auth"]

        if "session" not in self._config:
            self._config["session"] = {
                "start_time": "",
                "end_time": "",
                "duration": "",
                "level": "",
                "last_updated": "",
            }
        self.session = self._config["session"]

    def save(self):
        with open(self.config_path, "w") as configfile:
            self._config.write(configfile)

    @property
    def config_path(self):
        if not self._config_path:
            user_home = os.path.expanduser("~")
            config_path = xdg.BaseDirectory.save_config_path("snoo") or user_home
            config_file_path = os.path.join(config_path, "snoo.config")
            config_file_path_fallback = os.path.join(user_home, ".snoo_config")
            self._config_path = (
                config_file_path
                if os.path.exists(config_file_path)
                else config_file_path_fallback
            )
        return self._config_path

    def request(self, endpoint, payload=None, method="get", use_token=True):
        headers = {"User-Agent": self.USER_AGENT}
        if use_token:
            headers["Authorization"] = f"Bearer {self.get_token()}"
        response = requests.request(
            method=method, url=self.BASE_URL + endpoint, json=payload, headers=headers,
        )
        if response.ok:
            return response.json()
        else:
            raise APIError(endpoint, response.status_code, response.text)

    @property
    def username(self):
        if not self.auth["username"]:
            self.auth["username"] = input("SNOO Username: ")
        return self.auth["username"]

    @property
    def password(self):
        if not self.auth["password"]:
            self.auth["password"] = getpass.getpass()
        return self.auth["password"]

    def get_token(self):
        if self.auth["token"] and arrow.get(self.auth["token_expiry"]) > arrow.utcnow():
            return self.auth["token"]

        payload = {"username": self.username, "password": self.password}
        data = self.request(
            self.LOGIN_ENDPOINT, method="post", payload=payload, use_token=False
        )

        self.auth["token"] = data["access_token"]
        self.auth["token_expiry"] = str(
            arrow.utcnow().shift(seconds=data["expires_in"])
        )
        self.auth["refresh_token"] = data["refresh_token"]
        self.save()
        return self.auth["token"]

    def get_current_session(self):
        if self.session["last_updated"]:
            if (
                arrow.get(self.session["last_updated"]).shift(
                    seconds=int(self.config["update_interval"])
                )
                < arrow.utcnow()
            ):
                return self.session

        data = self.request(self.CURRENT_ENDPOINT)
        start_time = arrow.get(data["startTime"])
        end_time = arrow.get(data["endTime"]) if data["endTime"] else ""
        now = arrow.utcnow()
        if end_time:
            duration = int((now - end_time).total_seconds())
        else:
            duration = int((now - start_time).total_seconds())
        level = data["levels"][-1]["level"]

        self.session["start_time"] = str(start_time)
        self.session["end_time"] = str(end_time)
        self.session["last_updated"] = str(now)
        self.session["duration"] = str(duration)
        self.session["level"] = level
        self.save()
        return self.session

    def _humanize(self, duration):
        if not duration:
            return "0m"
        if isinstance(duration, str):
            duration = int(duration)
        minutes = int(duration // 60)
        if minutes >= 60:
            hours = minutes // 60
            return f"{hours}h {minutes % 60}m"
        return f"{minutes}m"

    def status(self):
        session = self.get_current_session()
        status = ""
        if session["end_time"]:
            status = "Awake"
        elif session["level"] == "BASELINE":
            status = "Asleep"
        else:
            status = "Soothing"
        return f"{status} {self._humanize(session['duration'])}"
