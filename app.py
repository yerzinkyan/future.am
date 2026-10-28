import os
from urllib.parse import urlsplit

from flask import Flask, render_template, request, session, redirect, url_for, abort
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_admin.form import SecureForm
from wtforms import PasswordField
from wtforms.validators import ValidationError
from sqlalchemy import text, inspect

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)

load_dotenv()

app = Flask(__name__)
# Обязательный ключ: без запасного значения в коде.
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")
app.json.ensure_ascii = False

# --- Languages ---
SUPPORTED_LANGUAGES = ['hy', 'ru', 'en']
DEFAULT_LANGUAGE = 'hy'

# --- Տվյալների բազայի կոնֆիգուրացիա (PostgreSQL) ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Отбрасывает «мёртвые» соединения (например, после рестарта БД)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}

db = SQLAlchemy(app)

# --- Admin օգտատեր (առանց առանձին DB աղյուսակի, credential-ները .env-ից) ---
class AdminUser(UserMixin):
    def __init__(self, username, is_root=False):
        self.id = username
        # is_root = главный админ из .env (единственный, кто управляет пользователями)
        self.is_root = is_root


ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Խնդրում ենք մուտք գործել այս էջը տեսնելու համար։"


@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return AdminUser(user_id, is_root=True)
    # Остальные админы хранятся в БД; деактивированный/удалённый вылетает сразу
    acc = AdminAccount.query.filter_by(username=user_id, is_active=True).first()
    return AdminUser(acc.username) if acc else None


def authenticate(username, password):
    """Главный админ (.env) или активный пользователь из таблицы admin_accounts."""
    if username == ADMIN_USERNAME:
        if ADMIN_PASSWORD_HASH and check_password_hash(ADMIN_PASSWORD_HASH, password):
            return AdminUser(username, is_root=True)
        return None
    acc = AdminAccount.query.filter_by(username=username, is_active=True).first()
    if acc and check_password_hash(acc.password_hash, password):
        return AdminUser(acc.username)
    return None


# --- Մոդելներ (Աղյուսակներ բազայում) ---

class SiteText(db.Model):
    __tablename__ = 'site_texts'

    id = db.Column(db.Integer, primary_key=True)
    key_name = db.Column(db.String(100), nullable=False)
    lang = db.Column(db.String(5), nullable=False, default=DEFAULT_LANGUAGE)
    content = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('key_name', 'lang', name='uq_site_texts_key_lang'),
    )

    def __str__(self):
        return f"{self.key_name} [{self.lang}]"

class AdminAccount(db.Model):
    """Дополнительные пользователи админки (главный админ остаётся в .env)."""
    __tablename__ = 'admin_accounts'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __str__(self):
        return self.username


class TerminalModel(db.Model):
    __tablename__ = 'terminal_models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vendor = db.Column(db.Text, nullable=True)

    def __str__(self):
        return self.name


# --- Flask-Admin կոնֆիգուրացիա (պաշտպանված login-ով) ---

class SecuredModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.full_path.rstrip('?')))


class SecuredAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.full_path.rstrip('?')))


class SiteTextAdmin(SecuredModelView):
    form_base_class = SecureForm
    # Кнопка Export в админке: скачать все тексты в Excel (xlsx) или CSV
    can_export = True
    export_types = ['xlsx']
    column_export_list = ('key_name', 'lang', 'content', 'description')
    column_list = ('key_name', 'lang', 'content', 'description')
    column_filters = ('lang', 'key_name')
    form_columns = ('key_name', 'lang', 'content', 'description')

class TerminalModels(SecuredModelView):
    form_base_class = SecureForm
    can_export = True
    export_types = ['xlsx']
    column_list = ('name', 'vendor')
    form_columns = ('name', 'vendor')

class AdminAccountView(SecuredModelView):
    """Таблица пользователей админки. Видна и доступна только главному админу."""
    form_base_class = SecureForm
    column_list = ('username', 'is_active')
    form_columns = ('username', 'password', 'is_active')
    form_extra_fields = {
        'password': PasswordField('Գաղտնաբառ (խմբագրելիս դատարկ թողնել՝ չփոխելու համար)')
    }

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'is_root', False)

    def inaccessible_callback(self, name, **kwargs):
        if current_user.is_authenticated:
            abort(403)
        return redirect(url_for('login', next=request.full_path.rstrip('?')))

    def on_model_change(self, form, model, is_created):
        model.username = (model.username or '').strip()
        if not model.username:
            raise ValidationError('Մուտքանունը պարտադիր է։')
        if model.username.lower() == ADMIN_USERNAME.lower():
            raise ValidationError('Այս մուտքանունը զբաղված է գլխավոր ադմինի կողմից։')
        password = form.password.data
        if is_created and not password:
            raise ValidationError('Նոր օգտատիրոջ համար գաղտնաբառը պարտադիր է։')
        if password:
            if len(password) < 8:
                raise ValidationError('Գաղտնաբառը պետք է լինի առնվազն 8 նիշ։')
            model.password_hash = generate_password_hash(password)


admin = Admin(app, name='FPS Admin', template_mode='bootstrap4',
              index_view=SecuredAdminIndexView())
admin.add_view(SiteTextAdmin(SiteText, db.session, name="Կայքի Տեքստեր"))
admin.add_view(TerminalModels(TerminalModel, db.session, name="Տերմինալներ"))
admin.add_view(AdminAccountView(AdminAccount, db.session, name="Օգտատերեր"))

admin.add_link(MenuLink(name='Դեպի Կայք', category='', url='/'))
admin.add_link(MenuLink(name='Ելք (Logout)', category='', url='/logout'))

@app.before_request
def resolve_language():
    """?lang=xx-ը փոխում է լեզուն ու պահվում է session-ում, հակառակ դեպքում
    օգտագործվում է նախկինում ընտրված (կամ default) լեզուն."""
    requested_lang = request.args.get('lang')
    if requested_lang in SUPPORTED_LANGUAGES:
        session['lang'] = requested_lang
    elif 'lang' not in session:
        session['lang'] = DEFAULT_LANGUAGE


@app.context_processor
def inject_current_lang():
    return {'current_lang': session.get('lang', DEFAULT_LANGUAGE)}


def run_migrations():
    """Idempotent, safe-to-run-every-startup migration for databases that
    predate the multi-language 'lang' column. Does nothing if the table
    doesn't exist yet (db.create_all() will build it correctly from
    scratch) or if the schema is already up to date."""
    if not inspect(db.engine).has_table('site_texts'):
        return

    with db.engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE site_texts
            ADD COLUMN IF NOT EXISTS lang VARCHAR(5) NOT NULL DEFAULT 'hy'
        """))
        conn.execute(text("""
            ALTER TABLE site_texts
            DROP CONSTRAINT IF EXISTS site_texts_key_name_key
        """))
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_site_texts_key_lang'
                ) THEN
                    ALTER TABLE site_texts
                    ADD CONSTRAINT uq_site_texts_key_lang UNIQUE (key_name, lang);
                END IF;
            END $$;
        """))

        conn.commit()


TEMPLATE_BY_LANG = {
    'hy': 'index_arm.html',
    'ru': 'index_ru.html',
    'en': 'index_en.html',
}


@app.route('/')
def home():
    current_lang = session.get('lang', DEFAULT_LANGUAGE)

    query = SiteText.query.filter_by(lang=current_lang).all()
    if not query and current_lang != DEFAULT_LANGUAGE:
        query = SiteText.query.filter_by(lang=DEFAULT_LANGUAGE).all()

    texts_dict = {
        item.key_name: {
            'content': item.content,
            'description': item.description
        } for item in query
    }
    terminals = TerminalModel.query.all()
    template_name = TEMPLATE_BY_LANG.get(current_lang, TEMPLATE_BY_LANG[DEFAULT_LANGUAGE])
    return render_template(template_name, texts=texts_dict, current_lang=current_lang, terminals=terminals)


# --- Admin login / logout ---

def is_safe_redirect_target(target):
    """Только относительные пути своего сайта (защита от open redirect)."""
    if not target or any(ch.isspace() or ord(ch) < 32 for ch in target):
        return False
    target = target.replace('\\', '/')
    parts = urlsplit(target)
    return (not parts.scheme and not parts.netloc
            and target.startswith('/') and not target.startswith('//'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        user = authenticate(username, password)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            if not is_safe_redirect_target(next_page):
                next_page = url_for('admin.index')
            return redirect(next_page)
        error = 'Սխալ մուտքանուն կամ գաղտնաբառ։'

    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Схема создаётся один раз в master-процессе gunicorn (--preload),
# до того как он форкнет воркеры.
with app.app_context():
    run_migrations()
    db.create_all()
    # Закрыть соединения, открытые до fork, чтобы воркеры не делили их между собой
    db.engine.dispose()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7070,
            debug=os.environ.get("FLASK_DEBUG", "0") == "1")