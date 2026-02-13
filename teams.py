import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from flask import Flask, Response, g, jsonify, request, url_for
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__, static_url_path='/static', static_folder='static')

DB_PATH = 'teams.db'

REQUIRED_FIELDS = [
    'name',
    'city',
    'country',
    'stadium',
    'foundation_year',
]


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON;')
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exc: Optional[BaseException]) -> None:
    conn = g.pop('db', None)
    if conn is not None:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        'id': row['id'],
        'name': row['name'],
        'city': row['city'],
        'country': row['country'],
        'stadium': row['stadium'],
        'foundation_year': row['foundation_year'],
    }


def validate_payload(payload: Any) -> Tuple[bool, Optional[str]]:
    if not isinstance(payload, dict):
        return False, 'Request body must be a JSON object.'

    for field in REQUIRED_FIELDS:
        if field not in payload:
            return False, f'Missing required field: {field}.'

    for field in REQUIRED_FIELDS:
        if payload[field] is None:
            return False, f'Field "{field}" must not be null.'
        if isinstance(payload[field], str) and payload[field].strip() == '':
            return False, f'Field "{field}" must not be blank.'

    foundation_year = payload.get('foundation_year')
    if not isinstance(foundation_year, int):
        return False, 'Field "foundation_year" must be an integer.'

    current_year = datetime.utcnow().year
    if foundation_year < 1800 or foundation_year > current_year:
        return False, f'Field "foundation_year" must be between 1800 and {current_year}.'

    for field in ['name', 'city', 'country', 'stadium']:
        if not isinstance(payload.get(field), str):
            return False, f'Field "{field}" must be a string.'

    return True, None


def error_response(status_code: int, message: str) -> Response:
    return jsonify({'error': message}), status_code


# Swagger UI served at /docs, pointing at a static file under /static/openapi.json
SWAGGER_URL = '/docs'
API_URL = '/static/openapi.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Teams API',
    },
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.get('/teams')
def list_teams() -> Response:
    try:
        db = get_db()
        rows = db.execute(
            """
            SELECT id, name, city, country, stadium, foundation_year
            FROM teams
            ORDER BY id ASC;
            """
        ).fetchall()
        return jsonify([row_to_dict(r) for r in rows]), 200
    except sqlite3.OperationalError as exc:
        return error_response(500, f'Database error: {exc}. Ensure teams.db exists and has the expected schema.')


@app.get('/teams/<int:team_id>')
def get_team(team_id: int) -> Response:
    try:
        db = get_db()
        row = db.execute(
            """
            SELECT id, name, city, country, stadium, foundation_year
            FROM teams
            WHERE id = ?;
            """,
            (team_id,),
        ).fetchone()

        if row is None:
            return error_response(404, 'Team not found.')

        return jsonify(row_to_dict(row)), 200
    except sqlite3.OperationalError as exc:
        return error_response(500, f'Database error: {exc}. Ensure teams.db exists and has the expected schema.')


@app.post('/teams')
def create_team() -> Response:
    payload = request.get_json(silent=True)
    is_valid, err = validate_payload(payload)
    if not is_valid:
        return error_response(400, err)

    try:
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO teams (name, city, country, stadium, foundation_year)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                payload['name'].strip(),
                payload['city'].strip(),
                payload['country'].strip(),
                payload['stadium'].strip(),
                payload['foundation_year'],
            ),
        )
        db.commit()

        new_id = cur.lastrowid
        location = url_for('get_team', team_id=new_id, _external=True)

        row = db.execute(
            """
            SELECT id, name, city, country, stadium, foundation_year
            FROM teams
            WHERE id = ?;
            """,
            (new_id,),
        ).fetchone()

        return jsonify(row_to_dict(row)), 201, {'Location': location}
    except sqlite3.OperationalError as exc:
        return error_response(500, f'Database error: {exc}. Ensure teams.db exists and has the expected schema.')


@app.put('/teams/<int:team_id>')
def update_team(team_id: int) -> Response:
    payload = request.get_json(silent=True)
    is_valid, err = validate_payload(payload)
    if not is_valid:
        return error_response(400, err)

    try:
        db = get_db()
        existing = db.execute(
            'SELECT id FROM teams WHERE id = ?;',
            (team_id,),
        ).fetchone()

        if existing is None:
            return error_response(404, 'Team not found.')

        db.execute(
            """
            UPDATE teams
            SET name = ?, city = ?, country = ?, stadium = ?, foundation_year = ?
            WHERE id = ?;
            """,
            (
                payload['name'].strip(),
                payload['city'].strip(),
                payload['country'].strip(),
                payload['stadium'].strip(),
                payload['foundation_year'],
                team_id,
            ),
        )
        db.commit()

        row = db.execute(
            """
            SELECT id, name, city, country, stadium, foundation_year
            FROM teams
            WHERE id = ?;
            """,
            (team_id,),
        ).fetchone()

        return jsonify(row_to_dict(row)), 200
    except sqlite3.OperationalError as exc:
        return error_response(500, f'Database error: {exc}. Ensure teams.db exists and has the expected schema.')


@app.delete('/teams/<int:team_id>')
def delete_team(team_id: int) -> Response:
    try:
        db = get_db()
        existing = db.execute(
            'SELECT id FROM teams WHERE id = ?;',
            (team_id,),
        ).fetchone()

        if existing is None:
            return error_response(404, 'Team not found.')

        db.execute('DELETE FROM teams WHERE id = ?;', (team_id,))
        db.commit()

        return ('', 204)
    except sqlite3.OperationalError as exc:
        return error_response(500, f'Database error: {exc}. Ensure teams.db exists and has the expected schema.')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
