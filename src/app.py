import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configuración de la Base de Datos
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Manejo de errores
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generar el mapa del sitio (muestra todos los endpoints disponibles)
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# --- ENDPOINTS DE PERSONAJES (PEOPLE) ---
@app.route('/people', methods=['GET'])
def get_people():
    people_query = People.query.all()
    results = [person.serialize() for person in people_query]
    return jsonify(results), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_single_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"msg": "Person not found"}), 404
    return jsonify(person.serialize()), 200

# --- ENDPOINTS DE PLANETAS (PLANETS) ---
@app.route('/planets', methods=['GET'])
def get_planets():
    planets_query = Planet.query.all()
    results = [planet.serialize() for planet in planets_query]
    return jsonify(results), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200

# --- ENDPOINTS DE USUARIOS (USERS) ---
@app.route('/users', methods=['GET'])
def get_users():
    users_query = User.query.all()
    results = [user.serialize() for user in users_query]
    return jsonify(results), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    # NOTA: Como no tenemos Login todavía, usamos el ID=1 hardcodeado
    current_user_id = 1
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Buscamos los favoritos de este usuario
    favorites = Favorite.query.filter_by(user_id=current_user_id).all()
    results = [fav.serialize() for fav in favorites]
    return jsonify(results), 200

# --- ENDPOINTS PARA AGREGAR FAVORITOS (POST) ---
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    current_user_id = 1 # Hardcodeado por ahora
    
    # Verificamos si el planeta existe
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"msg": "Planet not found"}), 404
        
    # Verificamos si ya lo tiene como favorito para no duplicar
    existing_fav = Favorite.query.filter_by(user_id=current_user_id, planet_id=planet_id).first()
    if existing_fav:
        return jsonify({"msg": "Favorite already exists"}), 400

    new_fav = Favorite(user_id=current_user_id, planet_id=planet_id)
    db.session.add(new_fav)
    db.session.commit()
    
    return jsonify({"msg": "Favorite planet added"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    current_user_id = 1 # Hardcodeado por ahora
    
    # Verificamos si el personaje existe
    person = People.query.get(people_id)
    if not person:
        return jsonify({"msg": "Person not found"}), 404
        
    existing_fav = Favorite.query.filter_by(user_id=current_user_id, people_id=people_id).first()
    if existing_fav:
        return jsonify({"msg": "Favorite already exists"}), 400

    new_fav = Favorite(user_id=current_user_id, people_id=people_id)
    db.session.add(new_fav)
    db.session.commit()
    
    return jsonify({"msg": "Favorite person added"}), 200

# --- ENDPOINTS PARA ELIMINAR FAVORITOS (DELETE) ---
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    current_user_id = 1
    fav = Favorite.query.filter_by(user_id=current_user_id, planet_id=planet_id).first()
    
    if not fav:
        return jsonify({"msg": "Favorite not found"}), 404
        
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite planet deleted"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    current_user_id = 1
    fav = Favorite.query.filter_by(user_id=current_user_id, people_id=people_id).first()
    
    if not fav:
        return jsonify({"msg": "Favorite not found"}), 404
        
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Favorite person deleted"}), 200

# Ejecutar la aplicación
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)