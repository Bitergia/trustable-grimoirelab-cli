import logging

import requests


class GrimoireLabClient:
    """
    Client to interact with GrimoireLab API.

    :param url: GrimoireLab API URL.
    :param user: Username to use when authentication is required.
    :param password: Password to use when authentication is required.
    """

    def __init__(self, url: str, user: str = None, password: str = None):
        self.url = url
        self.user = user
        self.password = password
        self.session = None
        self._token = None
        self._refresh_token = None

    def connect(self):
        """Establish a connection to the server, and create a token"""

        self.session = requests.Session()
        if not (self.user and self.password):
            return

        credentials = {"username": self.user, "password": self.password}
        res = self.post("token/", json=credentials)
        res.raise_for_status()
        data = res.json()

        self._token = data.get("access")
        self._refresh_token = data.get("refresh")

        self.session.headers.update({"Authorization": f"Bearer {self._token}"})

    def get(self, uri: str, *args, **kwargs) -> requests.Response:
        """
        Make a GET request to the GrimoireLab API.
        Check if the token is still valid, if not, refresh it.

        :param uri: URI to request.
        """
        return self._make_request("get", uri, *args, **kwargs)

    def post(self, uri: str, *args, **kwargs) -> requests.Response:
        """
        Make a POST request to the GrimoireLab API.
        Check if the token is still valid, if not, refresh it.

        :param uri: URI to request.
        """
        return self._make_request("post", uri, *args, **kwargs)

    def _make_request(self, method: str, uri: str, *args, **kwargs) -> requests.Response:
        """
        Make a request to the GrimoireLab API.
        Check if the token is still valid, if not, refresh it.

        :param method: HTTP method to use (get or post).
        :param uri: URI to request.
        """
        if not self.session:
            raise ValueError("Session not connected. Call connect() first.")

        url = f"{self.url}/{uri}"
        try:
            response = self.session.request(method, url, *args, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            if e.response.status_code == 403:
                if not self._refresh_token:
                    raise
                self._refresh_auth_token()
                return self.session.request(method, url, *args, **kwargs)
            return e.response

    def _refresh_auth_token(self):
        """Refresh the access token using the refresh token"""

        logging.debug("Refreshing token...")

        credentials = {"refresh": self._refresh_token}
        response = self.post("token/refresh/", json=credentials)
        response.raise_for_status()
        data = response.json()

        self._token = data.get("access")

        self.session.headers.update({"Authorization": f"Bearer {self._token}"})
