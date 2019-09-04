from flask import Blueprint, jsonify, request, Response, abort
from sqlalchemy import func

from ..data.models import Grant
from ..db import db
from ..data.graphql import schema

from flask_graphql import GraphQLView

bp = Blueprint('api', __name__)

@bp.route('/')
def api_endpoint():

    result = db.session.query(
        Grant.fundingOrganization_id,
        func.count(Grant.id).label("grants")
    ).group_by(
        Grant.fundingOrganization_id
    ).all()
    print([r._asdict() for r in result])
    return {
        "by_funder": [r._asdict() for r in result]
    }


bp.add_url_rule(
    "/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=True)
)
