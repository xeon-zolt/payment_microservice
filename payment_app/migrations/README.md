Generic single-database configuration with an async dbapi.

to generate migration file run 
```
alembic revision --autogenerate -m "<name of migration>"
```

to run migrations
```
alembic upgrade head
```
