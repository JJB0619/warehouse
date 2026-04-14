from flask import Flask
from config import Config
from models import db, User
from routes import bp
from services import init_system
from flask_login import LoginManager
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'routes.login_page'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(bp)

with app.app_context():
    db.create_all()
    init_system()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)