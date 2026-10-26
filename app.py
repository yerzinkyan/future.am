import os
from flask import Flask, render_template, request, session, redirect, url_for
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from sqlalchemy import text, inspect

from werkzeug.security import check_password_hash
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "future783")
app.json.ensure_ascii = False

# --- Languages ---
SUPPORTED_LANGUAGES = ['hy', 'ru', 'en']
DEFAULT_LANGUAGE = 'hy'

# --- Տվյալների բազայի կոնֆիգուրացիա (PostgreSQL) ---
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Admin օգտատեր (առանց առանձին DB աղյուսակի, credential-ները .env-ից) ---
class AdminUser(UserMixin):
    def __init__(self, username):
        self.id = username


ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "")

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Խնդրում ենք մուտք գործել այս էջը տեսնելու համար։"


@login_manager.user_loader
def load_user(user_id):
    if user_id == ADMIN_USERNAME:
        return AdminUser(user_id)
    return None


# --- Մոդելներ (Աղյուսակներ բազայում) ---

class SiteText(db.Model):
    __tablename__ = 'site_texts'

    id = db.Column(db.Integer, primary_key=True)
    # key_name-ը նույն տեքստի բոլոր լեզուների համար նույնն է
    # (օր.՝ 'about_us_arm'), իսկ lang-ը զատում է թարգմանությունները
    key_name = db.Column(db.String(100), nullable=False)
    lang = db.Column(db.String(5), nullable=False, default=DEFAULT_LANGUAGE)
    # content-ը բուն տեքստն է, որը կցուցադրվի կայքում
    content = db.Column(db.Text, nullable=False)
    # description-ը զուտ քեզ (ադմինին) հուշելու համար է, թե սա որ տեքստն է
    description = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('key_name', 'lang', name='uq_site_texts_key_lang'),
    )

    def __str__(self):
        return f"{self.key_name} [{self.lang}]"

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
        return redirect(url_for('login', next=request.url))


class SecuredAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))


class SiteTextAdmin(SecuredModelView):
    column_list = ('key_name', 'lang', 'content', 'description')
    column_filters = ('lang', 'key_name')
    form_columns = ('key_name', 'lang', 'content', 'description')

class TerminalModels(SecuredModelView):
    column_list = ('name', 'vendor')
    form_columns = ('name', 'vendor')

admin = Admin(app, name='FPS Admin', template_mode='bootstrap4',
              index_view=SecuredAdminIndexView())
admin.add_view(SiteTextAdmin(SiteText, db.session, name="Կայքի Տեքստեր"))
admin.add_view(TerminalModels(TerminalModel, db.session, name="Տերմինալներ"))

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
        # 1) Add the missing column, backfilling existing rows with 'hy'
        conn.execute(text("""
            ALTER TABLE site_texts
            ADD COLUMN IF NOT EXISTS lang VARCHAR(5) NOT NULL DEFAULT 'hy'
        """))

        # 2) Drop the old single-column unique constraint on key_name,
        #    if it still exists (its default Postgres name for a column
        #    declared unique=True at table creation).
        conn.execute(text("""
            ALTER TABLE site_texts
            DROP CONSTRAINT IF EXISTS site_texts_key_name_key
        """))

        # 3) Add the new composite (key_name, lang) unique constraint,
        #    only if it isn't already there.
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

    # եթե ընտրված լեզվով դեռ թարգմանություն չկա բազայում,
    # հետ ենք ընկնում default (հայերեն) տեքստերին, որ էջը դատարկ չմնա
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if username == ADMIN_USERNAME and ADMIN_PASSWORD_HASH \
                and check_password_hash(ADMIN_PASSWORD_HASH, password):
            login_user(AdminUser(username))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.index'))
        error = 'Սխալ մուտքանուն կամ գաղտնաբառ։'

    return render_template('login.html', error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# Աշխատում է անկախ deploy եղանակից՝ և՛ `python app.py`-ով,
# և՛ gunicorn/WSGI-ով (`gunicorn app:app`), քանի որ սա module-ի
# import-ի պահին է կանչվում, ոչ թե միայն __main__ բլոկում։
with app.app_context():
    run_migrations()
    db.create_all()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7070, debug=True)