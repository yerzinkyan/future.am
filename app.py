import os

from dotenv import load_dotenv
from flask import Flask, render_template, request, session

load_dotenv()

app = Flask(__name__)
# Ключ нужен только для подписи session-cookie (в ней хранится выбранный язык).
app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is not set")

# --- Languages ---
SUPPORTED_LANGUAGES = ['hy', 'ru', 'en']
DEFAULT_LANGUAGE = 'hy'

TEMPLATE_BY_LANG = {
    'hy': 'index_arm.html',
    'ru': 'index_ru.html',
    'en': 'index_en.html',
}


@app.before_request
def resolve_language():
    """?lang=xx-ը փոխում է լեզուն ու պահվում է session-ում, հակառակ դեպքում
    օգտագործվում է նախկինում ընտրված (կամ default) լեզուն."""
    requested_lang = request.args.get('lang')
    if requested_lang in SUPPORTED_LANGUAGES:
        session['lang'] = requested_lang
    elif session.get('lang') not in SUPPORTED_LANGUAGES:
        session['lang'] = DEFAULT_LANGUAGE


@app.route('/')
def home():
    lang = request.args.get('lang', DEFAULT_LANGUAGE)
    template = TEMPLATE_BY_LANG.get(lang, TEMPLATE_BY_LANG[DEFAULT_LANGUAGE])
    return render_template(template)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7070,
            debug=os.environ.get("FLASK_DEBUG", "0") == "1")