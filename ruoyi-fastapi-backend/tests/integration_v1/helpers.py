from types import SimpleNamespace

from fastapi import FastAPI, Request


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.calls = []

    async def get(self, key):
        self.calls.append(('get', key))
        return self.values.get(key)

    async def set(self, key, value, **kwargs):
        self.calls.append(('set', key))
        self.values[key] = value
        return True

    async def delete(self, key):
        self.calls.append(('delete', key))
        return int(self.values.pop(key, None) is not None)


class FakeDB:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.statements = []
        self.result = None

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1

    async def execute(self, statement):
        self.statements.append(statement)
        return SimpleNamespace(scalar_one_or_none=lambda: self.result)


def make_request(redis, authorization=None, path='/public/battle/invite-a/leave'):
    app = FastAPI()
    app.state.redis = redis
    headers = [] if authorization is None else [(b'authorization', authorization.encode())]
    return Request(
        {'type': 'http', 'method': 'POST', 'path': path, 'query_string': b'', 'headers': headers, 'app': app}
    )
