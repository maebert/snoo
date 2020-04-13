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


class Session:
    _map = {}

    def __init__(self, id):
        self.id = id
        self.levels = []

    @property
    def start_time(self):
        if not self.levels:
            return None
        return min([level["startTime"] for level in self.levels])

    @property
    def duration(self):
        if not self.levels:
            return 0
        return sum([level["stateDuration"] for level in self.levels])

    @property
    def asleep_duration(self):
        if not self.levels:
            return 0
        return sum(
            [
                level["stateDuration"]
                for level in self.levels
                if level["type"] == "asleep"
            ]
        )

    @property
    def soothing_duration(self):
        if not self.levels:
            return 0
        return sum(
            [
                level["stateDuration"]
                for level in self.levels
                if level["type"] == "soothing"
            ]
        )

    @property
    def end_time(self):
        return self.start_time.shift(seconds=self.duration)

    def __repr__(self):
        return f"<{self.start_time:MMM D, HH:mm} - {self.end_time:HH:mm}>"

    @classmethod
    def _from_data(cls, sessionId, **kwargs):
        if sessionId not in cls._map:
            cls._map[sessionId] = Session(sessionId)
        if "startTime" in kwargs:
            kwargs["startTime"] = arrow.get(kwargs["startTime"])
        cls._map[sessionId].levels.append(kwargs)
        return cls._map[sessionId]

    def to_dict(self):
        return {
            "start_time": self.start_time.format("YYYY-MM-DDTHH:mm:ss"),
            "end_time": self.end_time.format("YYYY-MM-DDTHH:mm:ss"),
            "duration": self.duration,
            "asleep": self.asleep_duration,
            "soothing": self.soothing_duration,
        }

    @classmethod
    def export(cls):
        result = []
        for session in sorted(cls._map.values(), key=lambda s: s.start_time):
            result.append(session.to_dict())
        return result


class Day:
    _all = []

    def __init__(self, start_time):
        self.start_time = start_time
        self.sessions = []
        self.data = {}

    def __repr__(self):
        return f"<{self.start_time:MMM D} ({len(self.sessions)} sessions)>"

    @classmethod
    def _from_data(cls, start_time, data):
        day = cls(start_time)
        day.sessions = set(
            [Session._from_data(**level) for level in data.pop("levels")]
        )
        day.data = data
        cls._all.append(day)
        return day

    def to_dict(self):
        result = {"date": self.start_time.format("YYYY-MM-DD")}
        result.update(self.data)
        return result

    @classmethod
    def export(cls):
        result = []
        for day in sorted(cls._all, key=lambda d: d.start_time):
            result.append(day.to_dict())
        return result


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

    def request(
        self, endpoint, payload=None, params=None, method="get", use_token=True
    ):
        headers = {"User-Agent": self.USER_AGENT}
        if use_token:
            headers["Authorization"] = f"Bearer {self.get_token()}"
        response = requests.request(
            method=method,
            url=self.BASE_URL + endpoint,
            json=payload,
            params=params,
            headers=headers,
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

    def get_history(self, start_time, end_time):
        result = []
        for day in arrow.Arrow.range("day", start_time, end_time):
            data = self.request(
                self.DATA_ENDPOINT,
                method="get",
                params={"startTime": day.format("MM/DD/YYYY hh:mm:ss")},
            )
            result.append(Day._from_data(day, data))
        return result

    def export_sessions(self, start_time, end_time):
        self.get_history(start_time, end_time)
        return Client._dict_to_csv(Session.export())

    def export_stats(self, start_time, end_time):
        self.get_history(start_time, end_time)
        return Client._dict_to_csv(Day.export())

    @classmethod
    def _dict_to_csv(cls, rows):
        fields = rows[0].keys()
        result = ",".join(fields) + "\n"
        for row in rows:
            result += ",".join([str(row[f]) for f in fields]) + "\n"
        return result

    def get_current_session(self):
        if self.session["last_updated"]:
            if (
                arrow.get(self.session["last_updated"]).shift(
                    seconds=int(self.config["update_interval"])
                )
                > arrow.utcnow()
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

    @classmethod
    def _humanize(cls, duration):
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
        elif session["level"] in ["BASELINE", "WEANING_BASELINE"]:
            status = "Asleep"
        else:
            status = "Soothing"
        return f"{status} {Client._humanize(session['duration'])}"
