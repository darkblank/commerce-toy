결제 전 주문까지

`.env` 파일 추가 후 아래 내용 추가

```dotenv
DB_HOST=toy_psql
DB_NAME={DB_NAME}
DB_PORT={DB_PORT}
DB_USER={DB_USER}
DB_PASSWORD={DB_PASSWORD}
REDIS_ENDPOINT=toy_redis
REDIS_PORT={REDIS_PORT}
DJANGO_SECRET_KEY={DJANGO_SECRET_KEY}
```


이후 `$ docker-compose up (--options)` 로 runserver 실행 가능

