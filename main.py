import argparse

from aiohttp import web

from cloud_img import MODE, create_app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=8080)
    parser.add_argument('-s', '--host', default='localhost')

    args = parser.parse_args()

    app = create_app(mode=MODE.DEBUG)
    web.run_app(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()
