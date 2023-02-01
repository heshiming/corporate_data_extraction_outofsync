import os
import shutil
import urllib.request, urllib.parse

from sanic import Sanic, exceptions, response
from sanic.log import logger
from sanic_ext import Extend


app = Sanic("osc-de")
app.config.CORS_ORIGINS = 'http://localhost,http://127.0.0.1'
Extend(app)


def sanitize_filename(filename):
    return filename.replace(':', '_').replace('/', '_').replace('\\', '_').strip('.')


@app.post('/upload/<session>')
async def upload(request, session):
    if not session:
        raise exceptions.BadRequest()
    if not request.files:
        raise exceptions.BadRequest()
    if len(request.files) == 0:
        raise exceptions.BadRequest()
    session_path = os.path.join(os.environ['FILE_PATH'], session, 'interim', 'pdfs')
    os.makedirs(session_path, exist_ok=True)
    for k, v in request.files.items():
        filename = sanitize_filename(v[0].name)
        file_fullpath = os.path.join(session_path, filename)
        with open(file_fullpath, 'wb') as f:
            f.write(v[0].body)
            logger.info('wrote {}\n'.format(file_fullpath))
    return response.json({
        'status': 'ok'
    })


@app.get('/files/<session>')
async def files(request, session):
    if not session:
        raise exceptions.BadRequest()
    session_path = os.path.join(os.environ['FILE_PATH'], session, 'interim', 'pdfs')
    try:
        ret = []
        for filename in os.listdir(session_path):
            if not filename.lower().endswith('.pdf'):
                continue
            ret.append(filename)
        return response.json({
            'status': 'ok',
            'data': ret
        })
    except FileNotFoundError:
        return response.json({
            'status': 'ok',
            'data': []
        })


@app.get('/extract/<session>')
async def extract(request, session):
    if not session:
        raise exceptions.BadRequest()
    req = urllib.request.Request('http://host.docker.internal:8000/run?{}'.format(urllib.parse.urlencode({'project_name': session, 'verbosity': 2})), method='GET')
    with urllib.request.urlopen(req) as resp:
        pass
    return response.json({
        'status': 'ok'
    })


@app.get('/extract_status/<session>/<bytes_read>')
async def extract_status(request, session, bytes_read):
    if not session:
        raise exceptions.BadRequest()
    if not bytes_read:
        raise exceptions.BadRequest()
    bytes_read = int(bytes_read)
    log_path = os.path.join(os.environ['FILE_PATH'], session, 'log.txt')
    try:
        with open(log_path, 'rb') as f:
            f.seek(bytes_read, 0)
            ret_bytes = f.read()
            pos = f.tell()
            return response.json({
                'status': 'ok',
                'data': {
                    'pos': pos,
                    'content': ret_bytes.decode('utf-8')
                }
            })
    except UnicodeDecodeError:
        # not enough bytes to decode utf-8
        return response.json({
            'status': 'ok',
            'data': {
                'pos': bytes_read,
                'content': ''
            }
        })
    except Exception as e:
        return response.json({
            'status': 'fail',
            'reason': str(e)
        })


@app.get('/download/<session>')
async def download(request, session):
    if not session:
        raise exceptions.BadRequest()
    output_path = os.path.join(os.environ['FILE_PATH'], session, 'output')
    shutil.make_archive(os.path.join(os.environ['FILE_PATH'], session, session), 'zip', output_path)
    return await response.file(os.path.join(os.environ['FILE_PATH'], session, '{}.zip'.format(session)))


if __name__ == '__main__':
    app.run()
