from itertools import chain
from typing import Any, Callable, Optional

import requests
from requests import Request, Response
from requests.exceptions import RetryError

from requests.adapters import HTTPAdapter
from requests.auth import AuthBase
from urllib3 import Retry

hook = Callable[[Request | Response, Any, Any], Any]


def merge_dicts(*dicts) -> dict[str, list[hook] | None]:
    merged_dict = {}
    for d in dicts:
        for key, value in d.items():
            if key in merged_dict:
                if isinstance(merged_dict[key], list):
                    if isinstance(value, list):
                        merged_dict[key].extend(value)
                    else:
                        merged_dict[key].append(value)
                else:
                    merged_dict[key] = [merged_dict[key], value]
            else:
                if isinstance(value, list):
                    merged_dict[key] = value
                else:
                    merged_dict[key] = [value]

    return merged_dict


class RequestService:

    def __init__(
            self,
            base_url: str,
    ):
        self._hooks = {}
        self._base_url = base_url
        self._session = requests.Session()
        self._retries = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504, 520],
        )
        self._session.mount('https://', HTTPAdapter(max_retries=self._retries))

    def _make_request(
            self,
            method: str,
            url: str,
            params=None,
            data=None,
            json=None,
            **kwargs: Optional[Any]
    ) -> Response:
        full_url = self._base_url + url
        hooks = merge_dicts(self._hooks, kwargs.pop('hooks', {}))

        response = self._session.request(
            method=method,
            url=full_url,
            hooks=hooks,
            params=params,
            data=data,
            json=json,
            **kwargs
        )

        return response

    def register_global_hooks(self, hooks=dict[str, hook]):
        self._hooks = hooks

    def add_auth(self, auth: AuthBase):
        self._session.auth = auth

    def add_headers(self, headers: dict[str, str]):
        self._session.headers.update(headers)

    def get(self, url: Optional[str] = '', data=None, json=None, **kwargs):
        try:
            return self._make_request(url=url, method='GET', data=data, json=json, **kwargs)
        except RetryError:
            raise

    def post(self, url: Optional[str] = '', data=None, json=None, **kwargs):
        try:
            return self._make_request(url=url, method='POST', data=data, json=json, **kwargs)
        except Exception:
            raise

    def delete(self, url: Optional[str] = '', data=None, json=None, **kwargs):
        try:
            return self._make_request(url=url, method='DELETE', data=data, json=json, **kwargs)
        except Exception:
            raise


def print_url(response: Response, *args, **kwargs):
    print(response.status_code, response.headers, )
    print('ARGS--', args, 'KW------', kwargs)


r = RequestService('https://onet.pl')
r.register_global_hooks(dict(response=print_url))
r.add_headers({'Auth': '123'})
res = r.get(allow_redirects=True, proxies={}, hooks=dict(response=print_url))
print(res.status_code)
