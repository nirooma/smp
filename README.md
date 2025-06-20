### Building and running your application

When you're ready, start your application by running:
`docker compose up --build`.

Your application will be available at http://localhost:8000.

## address
```
curl -X 'GET' \
  'http://0.0.0.0:8000/address/1DEP8i3QJCsomS4BSMY2RpU1upv62aGvhD' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json'
```

## transaction
```
curl -X 'GET' \
  'http://0.0.0.0:8000/transaction/f854aebae95150b379cc1187d848d58225f3c4157fe992bcd166f58bd5063449' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json'
```


