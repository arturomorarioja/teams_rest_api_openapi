# Football Teams
REST API example with OpenAPI documentation.

## Installation
- Start the API: `docker compose up -d --build`
- Stop the API: `docker compose down -v`

### Endpoints

|Method|Endpoint|Body params|
|-|-|-|
|GET|/teams||
|GET|/teams/:id||
|POST|/teams|name, city, country, stadium, foundation_year|
|PUT|/teams/:id|name, city, country, stadium, foundation_year|
|DELETE|/teams/:id||

### Testing
The folder `Postman` contains a Postman collection and environment with test scripts.

### Documentation
Find the OpenAPI description at `http://localhost:5000/openapi.json`.

Find the OpenAPI documentation at `http://localhost:5000/docs`.

## Tools
SQLite / Flask / Python

## Author
ChatGPT 5.2, prompted by Arturo Mora-Rioja.