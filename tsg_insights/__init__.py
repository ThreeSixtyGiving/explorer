import requests_cache
import os

from flask import Flask, send_from_directory, request
import pandas as pd

from .data.registry import THREESIXTY_STATUS_JSON
from .blueprints import home, fetch, job, data, cache
from .commands import registry, worker, datafile
from .data.cache import get_cache
from .data.utils import CustomJSONEncoder

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        JSON_SORT_KEYS=False,

        # Newsletter
        NEWSLETTER_FORM_ACTION=os.environ.get("NEWSLETTER_FORM_ACTION"),
        NEWSLETTER_FORM_U=os.environ.get("NEWSLETTER_FORM_U"),
        NEWSLETTER_FORM_ID=os.environ.get("NEWSLETTER_FORM_ID"),

        # 360Giving registry URL
        THREESIXTY_STATUS_JSON=os.environ.get(
            "THREESIXTY_STATUS_JSON", THREESIXTY_STATUS_JSON),

        # Mapbox maps
        MAPBOX_ACCESS_TOKEN=os.environ.get("MAPBOX_ACCESS_TOKEN"),
        MAPBOX_STYLE=os.environ.get("MAPBOX_STYLE"),

        # limit of file size for the tool
        FILE_SIZE_LIMIT=os.environ.get("FILE_SIZE_LIMIT", 50000000),

        # google analytics property ID
        GOOGLE_ANALYTICS_TRACKING_ID=os.environ.get("GOOGLE_ANALYTICS_TRACKING_ID")

        # Redis variables - not set here
        # REDIS_DEFAULT_URL='redis://localhost:6379/0' # default URL for redis instance
        # REDIS_ENV_VAR='REDIS_URL'                    # name of the environmental variable that will be looked up for the redis url
        # CACHE_DEFAULT_PREFIX='file_'
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # overwrite default JSON encoder
    app.json_encoder = CustomJSONEncoder

    # register blueprints for pages
    app.register_blueprint(home.bp)
    app.register_blueprint(fetch.bp, url_prefix='/fetch')
    app.register_blueprint(job.bp, url_prefix='/job')
    app.register_blueprint(data.bp, url_prefix='/data')
    app.register_blueprint(cache.bp, url_prefix='/cache')
    app.add_url_rule('/', endpoint='index')

    # register command line interface
    app.cli.add_command(registry.cli)
    app.cli.add_command(worker.cli)
    app.cli.add_command(datafile.cli)

    # where to serve images from
    @app.route('/images/<path:path>')
    def send_images(path):
        return send_from_directory('static/images', path)

    # add caching
    one_week_in_seconds = 60*60*24*7
    requests_cache.install_cache(
        backend='redis',
        connection=get_cache(),
        expire_after=one_week_in_seconds,
        allowable_methods=('GET', 'HEAD',),
    )

    # add cookie check
    @app.context_processor
    def inject_template_scope():
        injections = dict()

        def cookies_consented():
            value = request.cookies.get('cookie_consent')
            return value == 'true'

        def cookies_asked():
            value = request.cookies.get('cookie_consent')
            return value is not None
        
        injections.update(cookies_consented=cookies_consented, cookies_asked=cookies_asked)

        return injections

    return app