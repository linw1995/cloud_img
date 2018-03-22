import logging

import peewee
from aiohttp import web
# TODO: reimplement `login_required` decorator
from aiohttp_security.api import forget, login_required, remember
from jsonschema import ValidationError, validate

from ..models.user import User


logger = logging.getLogger(__name__)
argsSchema = {
    "type": "object",
    "properties": {
        "username": {
            "type": "string",
            "minLength": 4,
            "maxLength": 32,
        },
        "password": {
            "type":
            "string",
            "minLength":
            8,
            "maxLength":
            64,
            "pattern": ("^((?=.*\d)"
                        "(?=.*[a-z])"
                        "(?=.*[A-Z])"
                        "(?=.*[\!\@\#\$\%\^\&\*\(\)\_\+])).+$"),
        },
    },
    "required": ["username", "password"],
    "additionalProperties": False,
}
"""
(			# Start of group
  (?=.*\d)		#   must contains one digit from 0-9
  (?=.*[a-z])		#   must contains one lowercase characters
  (?=.*[A-Z])		#   must contains one uppercase characters
  (?=.*[\!\@\#\$\%\^\&\*\(\)\_\+])
  #   must contains one special symbols in the list "!@#$%^&*()_+"
              .		#     match anything with previous condition checking
)			# End of group
"""


async def login(request, *args, **kwargs):
    logger.debug("login arguments: args=%r, kwargs=%r", args, kwargs)
    db_manager = request.app['db_manager']
    reqBody = await request.json()
    try:
        validate(reqBody, argsSchema)
    except ValidationError as err:
        logger.debug('args schema validate failure: %r', err)
        return web.json_response({'message': 'paramaters error'}, status=400)

    username = reqBody['username']
    password = reqBody['password']
    try:
        user = await db_manager.get(User, username=username)
    except User.DoesNotExist as err:
        logger.debug(err)
    else:
        valid = user.validate_password(password)
        if valid:
            logger.debug('%r login success', user)
            response = web.json_response({'message': 'login success'})
            await remember(request, response, user.identity)
            return response
    logger.debug('User(username=%r) login failure', username)
    return web.json_response(
        {
            'message': 'wrong username or password'
        }, status=400)


async def signup(request):
    db_manager = request.app['db_manager']

    reqBody = await request.json()
    try:
        validate(reqBody, argsSchema)
    except ValidationError as err:
        logger.debug('args schema validate failure: %r', err)
        return web.json_response({'message': 'paramaters error'}, status=400)

    username = reqBody['username']
    password = reqBody['password']

    try:
        await db_manager.create(User, username=username, password=password)
    except peewee.IntegrityError as err:
        logger.debug('User(username=%r) signup failure: %r', username, err)
        return web.json_response(
            {
                'message': 'signup fail due to %r' % err
            }, status=400)
    logger.debug('User(username=%r) signup success', username)
    return web.json_response({'message': 'signup success'})


@login_required
async def logout(request):
    response = web.json_response({'message': 'logout success'})
    await forget(request, response)
    return response
