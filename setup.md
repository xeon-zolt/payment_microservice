# used to setup local on mac m1 should work with *nix type OS

install pyenv to install custom python version
then use
```
pyenv  install 3.10.1
```

check readme for how to include it in path for pyenv
```
export PATH=~/.pyenv/shims:~/.pyenv/bin:"$PATH"
```

set 3.10.1 to loacl
```
pyenv local 3.10.1
```

run
```
python3.10 -m venv .env
```
once env is created use this to activate env
```
source .env/bin/activate
```

install requirements
```
pip install -r requirements.txt
```

run migrations (when you create new model add model path to init file in model)
```
alembic upgrade head
```

run
```
uvicorn payment_app.main:app --reload
```

before first commit
```
pre-commit install
```

Run tests
---------
Tests for this project are defined in the ``tests/`` folder.

This project uses `pytest
<https://docs.pytest.org/>`_ to define tests because it allows you to use the ``assert`` keyword with good formatting for failed assertations.

To run all the tests of a project, simply run the ``pytest`` command: ::
```
pytest
```
If you want to run a specific test, you can do this with this pytest feature:
```
pytest -s payment_app/tests/test_routes/test_utils.py::test_check_ip_in_range
```
runs pytest using coverage
```
coverage run -m pytest
```
generates the coverage report
```
coverage report -m
```
display coverage report in web view
```
coverage html
```