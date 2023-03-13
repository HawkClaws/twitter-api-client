import asyncio
import hashlib
import inspect
import logging.config
import mimetypes
import sys
import time
from copy import deepcopy
from enum import Enum, auto
from functools import wraps, partial
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid1, getnode

import ujson
from tqdm import tqdm

from .config.log_config import log_config
from .config.operations import operations
from .config.settings import *
from .login import Session, Response

try:
    if get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
        import nest_asyncio
        nest_asyncio.apply()
except:
    ...

if sys.platform != 'win32':
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
else:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.config.dictConfig(log_config)
logger = logging.getLogger(__name__)


class Operation(Enum):
    CreateTweet = auto()
    CreateScheduledTweet = auto()
    DeleteTweet = auto()
    UserTweets = auto()
    FavoriteTweet = auto()
    UnfavoriteTweet = auto()
    CreateRetweet = auto()
    DeleteRetweet = auto()
    CreateBookmark = auto()
    DeleteBookmark = auto()
    BookmarksAllDelete = auto()
    TweetStats = auto()
    # DM
    useSendMessageMutation = auto()


def log(fn=None, *, level: int = logging.DEBUG, info: list = None) -> callable:
    if fn is None:
        return partial(log, level=level, info=info)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        args_info = " ".join(
            f'{k}={v}' for k, v in dict(zip(inspect.getfullargspec(fn)[0], args)).items()
            if '_id' in k or '_name' in k or 'Id' in k or 'Name' in k
        )
        r = fn(*args, **kwargs)
        try:
            if 200 <= r.status_code < 300:
                # info.remove('status_code')
                message = f'[{SUCCESS}SUCCESS{RESET}] {r.status_code} ({BOLD}{fn.__name__}{RESET}) {args_info}'
                for k in info:
                    if callable(k):
                        logger.log(level, f'{message} {k(r)}')
                    else:
                        attr = getattr(r, k)
                        v = attr() if callable(attr) else attr
                        d = {f"{k}": v}
                        logger.log(level, f'{message} {d}')
            else:
                logger.log(level, f'[{WARN}ERROR{RESET}] ({fn.__name__}) {args_info} {r.status_code} {r.text}')
        except Exception as e:
            logger.log(level, f'[{WARN}FAILED{RESET}] ({fn.__name__}) {args_info} {r.status_code} {e}')
        return r

    return wrapper


@log(level=logging.DEBUG, info=['json'])
def bookmark(_id: int, session: Session) -> Response:
    return graphql_request(_id, Operation.CreateBookmark.name, 'tweet_id', session)


@log(level=logging.DEBUG, info=['json'])
def unbookmark(_id: int, session: Session) -> Response:
    return graphql_request(_id, Operation.DeleteBookmark.name, 'tweet_id', session)


@log(level=logging.DEBUG, info=['json'])
def unbookmark_all(_id: int, session: Session) -> Response:
    return graphql_request(_id, Operation.BookmarksAllDelete.name, 0, session)


def graphql_request(_id: int, operation: any, key: str | int, session: Session) -> Response:
    params = deepcopy(operations[operation])
    qid = params['queryId']
    if key: params['variables'][key] = _id
    url = f"https://api.twitter.com/graphql/{qid}/{operation}"
    r = session.post(url, headers=get_auth_headers(session), json=params)
    return r


def api_request(settings: dict, path: str, session: Session) -> Response:
    headers = get_auth_headers(session)
    headers['content-type'] = 'application/x-www-form-urlencoded'
    url = f'https://api.twitter.com/1.1/{path}'
    r = session.post(url, headers=headers, data=urlencode(settings))
    return r


def get_auth_headers(session: Session) -> dict:
    return {
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'accept-encoding': 'gzip, deflate, br',
        'cookie': '; '.join(f'{k}={v}' for k, v in session.cookies.items()),
        'referer': 'https://twitter.com/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'x-csrf-token': session.cookies.get('ct0'),
    }


# async def get_status(media_id: str, auth_session: Session, check_after_secs: int = 1):
#     url = 'https://upload.twitter.com/i/media/upload.json'
#     headers = get_auth_headers(auth_session)
#     params = {'command': 'STATUS', 'media_id': media_id}
#     while 1:
#         await asyncio.sleep(check_after_secs)
#         async with aiohttp.ClientSession(headers=headers) as s:
#             async with s.get(url, params=params) as r:
#                 data = await r.json()
#         info = data['processing_info']
#         state = info['state']
#         if state == 'succeeded':
#             logger.debug(f'{media_id}: {SUCCESS}processing complete{RESET}')
#             return data
#         if state == 'in_progress':
#             progress = info["progress_percent"]
#             check_after_secs = info.get('check_after_secs', check_after_secs)
#             logger.debug(f'{media_id}: upload {progress = }%')
#         else:
#             logger.debug(f'{media_id}: upload {state = }')
#
#
# async def upload_media(fname: str, auth_session: Session, is_dm=False):
#     """
#     https://developer.twitter.com/en/docs/twitter-api/v1/media/upload-media/uploading-media/media-best-practices
#     """
#     url = 'https://upload.twitter.com/i/media/upload.json'
#     headers = get_auth_headers(auth_session)
#     conn = aiohttp.TCPConnector(limit=0, ssl=False, ttl_dns_cache=69)
#     async with aiohttp.ClientSession(headers=headers, connector=conn) as s:
#         file = Path(fname)
#         total_bytes = file.stat().st_size
#         upload_type = 'dm' if is_dm else 'tweet'
#         media_type = mimetypes.guess_type(file)[0]
#         media_category = f'{upload_type}_{media_type.split("/")[0]}'
#
#         if media_category in {'dm_image', 'tweet_image'} and total_bytes > MAX_IMAGE_SIZE:
#             raise Exception(f'Image too large: max is {(MAX_IMAGE_SIZE / 1e6):.2f} MB')
#         if media_category in {'dm_gif', 'tweet_gif'} and total_bytes > MAX_GIF_SIZE:
#             raise Exception(f'GIF too large: max is {(MAX_GIF_SIZE / 1e6):.2f} MB')
#         if media_category in {'dm_video', 'tweet_video'} and total_bytes > MAX_VIDEO_SIZE:
#             raise Exception(f'Video too large: max is {(MAX_VIDEO_SIZE / 1e6):.2f} MB')
#
#         params = {
#             'command': 'INIT',
#             'total_bytes': total_bytes,
#             'media_type': media_type,
#             'media_category': media_category
#         }
#         async with s.post(url, headers=headers, params=params) as r:
#             info = await r.json()
#             logger.debug(f'INIT {info}')
#             media_id = info['media_id']
#
#         with open(fname, 'rb') as f:
#             i = 0
#             while chunk := f.read(MAX_IMAGE_SIZE):  # todo: arbitrary max size for now
#                 with aiohttp.MultipartWriter('form-data') as mpw:
#                     part = mpw.append(chunk)
#                     part.set_content_disposition('form-data', name='media', filename='blob')
#                     s.cookie_jar.update_cookies(auth_session.cookies)  # csrf cookie/header update
#                     r = await s.post(
#                         url,
#                         data=mpw,
#                         headers=headers,
#                         params={'command': 'APPEND', 'media_id': media_id, 'segment_index': i}
#                     )
#                     logger.debug(f'APPEND {r.status}')
#                     i += 1
#         finalize_params = {
#             'command': 'FINALIZE',
#             'media_id': media_id,
#             'allow_async': 'true'
#         }
#         if is_dm:
#             finalize_params |= {'original_md5': hashlib.md5(Path(fname).read_bytes()).hexdigest()}
#         async with s.post(url, headers=headers, params=finalize_params) as r:
#             res = await r.json()
#             logger.debug(f'FINALIZE {res}')
#
#         if processing_info := res.get('processing_info', {}):
#             state = processing_info.get('state')
#             if state == 'pending':
#                 logger.debug(f'{media_id}: {state}')
#                 return await get_status(media_id, auth_session, processing_info.get('check_after_secs', 1))
#             logger.debug(f'{media_id}: {SUCCESS}upload complete{RESET}')
#     return res

def upload_media(filename: str, session: Session, is_dm=False):
    url = 'https://upload.twitter.com/1.1/media/upload.json'
    total_bytes = Path(filename).stat().st_size
    headers = get_auth_headers(session)

    upload_type = 'dm' if is_dm else 'tweet'
    media_type = mimetypes.guess_type(filename)[0]
    media_category = f'{upload_type}_{media_type.split("/")[0]}'

    if media_category in {'dm_image', 'tweet_image'} and total_bytes > MAX_IMAGE_SIZE:
        raise Exception(f'Image too large: max is {(MAX_IMAGE_SIZE / 1e6):.2f} MB')
    if media_category in {'dm_gif', 'tweet_gif'} and total_bytes > MAX_GIF_SIZE:
        raise Exception(f'GIF too large: max is {(MAX_GIF_SIZE / 1e6):.2f} MB')
    if media_category in {'dm_video', 'tweet_video'} and total_bytes > MAX_VIDEO_SIZE:
        raise Exception(f'Video too large: max is {(MAX_VIDEO_SIZE / 1e6):.2f} MB')

    data = {'command': 'INIT', 'media_type': media_type, 'total_bytes': total_bytes, 'media_category': media_category}
    r = session.post(url=url, headers=headers, data=data)
    media_id = r.json()['media_id']
    with tqdm(total=total_bytes, desc=f"uploading: {filename}") as pbar:
        with open(filename, 'rb') as f:
            i = 0
            while chunk := f.read(4 * 1024 * 1024):  # todo: arbitrary max size for now
                data = {'command': 'APPEND', 'media_id': media_id, 'segment_index': i}
                files = {'media': chunk}
                r = session.post(url=url, headers=headers, data=data, files=files)
                if r.status_code < 200 or r.status_code > 299:
                    logger.debug(f'{r.status_code} {r.text}')
                    raise Exception('Upload failed')
                i += 1
                pbar.update(f.tell() - pbar.n)

    data = {'command': 'FINALIZE', 'media_id': media_id, 'allow_async': 'true'}
    if is_dm:
        data |= {'original_md5': hashlib.md5(Path(filename).read_bytes()).hexdigest()}
    r = session.post(url=url, headers=headers, data=data)
    # logger.debug(f'FINALIZE {r.json()}')

    logger.debug(f'processing, please wait...')
    processing_info = r.json().get('processing_info')
    while processing_info:
        state = processing_info['state']
        if state == 'succeeded':
            break
        if state == 'failed':
            raise Exception('Media processing failed')
        check_after_secs = processing_info['check_after_secs']
        # logger.debug(f'{check_after_secs = }')
        time.sleep(check_after_secs)
        params = {'command': 'STATUS', 'media_id': media_id}
        r = session.get(url=url, headers=headers, params=params)
        processing_info = r.json().get('processing_info')
    logger.debug('processing complete')

    return media_id


@log(level=logging.DEBUG, info=['text'])
def add_alt_text(text: str, media_id: int, session: Session) -> Response:
    params = {"media_id": media_id, "alt_text": {"text": text}}
    url = 'https://api.twitter.com/1.1/media/metadata/create.json'
    r = session.post(url, headers=get_auth_headers(session), json=params)
    return r


@log(level=logging.DEBUG, info=['json'])
def like(tweet_id: int, session: Session) -> Response:
    return graphql_request(tweet_id, Operation.FavoriteTweet.name, 'tweet_id', session)


@log(level=logging.DEBUG, info=['json'])
def unlike(tweet_id: int, session: Session) -> Response:
    return graphql_request(tweet_id, Operation.UnfavoriteTweet.name, 'tweet_id', session)


@log(level=logging.DEBUG, info=['json'])
def tweet(text: str, session: Session, media: list[dict | str] = None, **kwargs) -> Response:
    operation = Operation.CreateTweet.name
    params = deepcopy(operations[operation])
    qid = params['queryId']
    params['variables']['tweet_text'] = text
    if media:
        for m in media:
            if isinstance(m, dict):
                media_id = upload_media(m['file'], session)
                params['variables']['media']['media_entities'].append({
                    'media_id': media_id,
                    'tagged_users': m.get('tagged_users', [])
                })
                if alt := m.get('alt'):
                    add_alt_text(alt, media_id, session)
            # for convenience, so we can just pass list of strings
            elif isinstance(m, str):
                media_id = upload_media(m, session)
                params['variables']['media']['media_entities'].append({
                    'media_id': media_id,
                    'tagged_users': []
                })

    if reply_params := kwargs.get('reply_params', {}):
        params['variables'] |= reply_params
    if quote_params := kwargs.get('quote_params', {}):
        params['variables'] |= quote_params
    if poll_params := kwargs.get('poll_params', {}):
        params['variables'] |= poll_params

    url = f"https://api.twitter.com/graphql/{qid}/{operation}"
    r = session.post(url, headers=get_auth_headers(session), json=params)
    return r


def comment(text: str, tweet_id: int, session: Session, media: list[dict | str] = None) -> Response:
    params = {"reply": {"in_reply_to_tweet_id": tweet_id, "exclude_reply_user_ids": []}}
    return tweet(text, session, media, reply_params=params)


def quote(text: str, screen_name: str, tweet_id: int, session: Session, media: list[dict | str] = None) -> Response:
    """ no unquote operation, just DeleteTweet"""
    params = {"attachment_url": f"https://twitter.com/{screen_name}/status/{tweet_id}"}
    return tweet(text, session, media, quote_params=params)


@log(level=logging.DEBUG, info=['json'])
def untweet(tweet_id: int, session: Session) -> Response:
    return graphql_request(tweet_id, Operation.DeleteTweet.name, 'tweet_id', session)


# def __batch_delete_tweets(user_id: int, session: Session) -> None:
#     tweets = get_tweets(user_id, session).json()
#     ids = set(map(int, find_key(find_key(tweets, 'tweet_results'), 'rest_id'))) - {user_id}
#     [untweet(_id, session) for _id in ids]


@log(level=logging.DEBUG, info=['json'])
def retweet(tweet_id: int, session: Session) -> Response:
    return graphql_request(tweet_id, Operation.CreateRetweet.name, 'tweet_id', session)


@log(level=logging.DEBUG, info=['json'])
def unretweet(tweet_id: int, session: Session) -> Response:
    return graphql_request(tweet_id, Operation.DeleteRetweet.name, 'source_tweet_id', session)


@log(level=logging.DEBUG, info=['json'])
def get_tweets(user_id: int, session: Session) -> Response:
    operation = Operation.UserTweets.name
    params = deepcopy(operations[operation])
    qid = params['queryId']
    params['variables']['userId'] = user_id
    query = build_query(params)
    url = f"https://api.twitter.com/graphql/{qid}/{operation}?{query}"
    r = session.get(url, headers=get_auth_headers(session))
    return r


@log(level=logging.DEBUG, info=['json'])
def follow(user_id: int, session: Session) -> Response:
    settings = follow_settings.copy()
    settings |= {"user_id": user_id}
    return api_request(settings, 'friendships/create.json', session)


@log(level=logging.DEBUG, info=['json'])
def unfollow(user_id: int, session: Session) -> Response:
    settings = follow_settings.copy()
    settings |= {"user_id": user_id}
    return api_request(settings, 'friendships/destroy.json', session)


@log(level=logging.DEBUG, info=['json'])
def mute(user_id: int, session: Session) -> Response:
    settings = {'user_id': user_id}
    return api_request(settings, 'mutes/users/create.json', session)


@log(level=logging.DEBUG, info=['json'])
def unmute(user_id: int, session: Session) -> Response:
    settings = {'user_id': user_id}
    return api_request(settings, 'mutes/users/destroy.json', session)


@log(level=logging.DEBUG, info=['json'])
def enable_notifications(user_id: int, session: Session) -> Response:
    settings = notification_settings.copy()
    settings |= {'id': user_id, 'device': 'true'}
    return api_request(settings, 'friendships/update.json', session)


@log(level=logging.DEBUG, info=['json'])
def disable_notifications(user_id: int, session: Session) -> Response:
    settings = notification_settings.copy()
    settings |= {'id': user_id, 'device': 'false'}
    return api_request(settings, 'friendships/update.json', session)


@log(level=logging.DEBUG, info=['json'])
def block(user_id: int, session: Session) -> Response:
    settings = {'user_id': user_id}
    return api_request(settings, 'blocks/create.json', session)


@log(level=logging.DEBUG, info=['json'])
def unblock(user_id: int, session: Session) -> Response:
    settings = {'user_id': user_id}
    return api_request(settings, 'blocks/destroy.json', session)


@log(level=logging.DEBUG, info=['text'])
def update_search_settings(session: Session, hide_blocked=False, hide_nsfw=False) -> Response:
    settings = account_search_settings.copy()
    settings['optInFiltering'] = hide_nsfw
    settings['optInBlocking'] = hide_blocked
    twid = int(session.cookies.get_dict()['twid'].split('=')[-1].strip('"'))
    headers = get_auth_headers(session=session)
    r = session.post(
        url=f'https://api.twitter.com/1.1/strato/column/User/{twid}/search/searchSafety',
        headers=headers,
        json=settings,
    )
    return r


@log(level=logging.DEBUG, info=['json'])
def update_content_settings(session: Session, **kwargs) -> Response:
    """
    Update content settings

    @param session: authenticated session
    @param kwargs: settings to enable/disable
    @return: updated settings
    """
    kwargs |= content_settings
    return api_request(kwargs, 'account/settings.json', session)


def build_query(params: dict) -> str:
    return '&'.join(f'{k}={ujson.dumps(v)}' for k, v in params.items())


@log(level=logging.DEBUG, info=['json'])
def stats(rest_id: int, session: Session) -> Response:
    """private endpoint?"""
    operation = Operation.TweetStats.name
    params = deepcopy(operations[operation])
    qid = params['queryId']
    params['variables']['rest_id'] = rest_id
    query = build_query(params)
    url = f"https://api.twitter.com/graphql/{qid}/{operation}?{query}"
    r = session.get(url, headers=get_auth_headers(session))
    return r


@log(level=logging.DEBUG, info=['json'])
def dm(text: str, receivers: list[int], session: Session, filename: str = '') -> Response:
    operation = Operation.useSendMessageMutation.name
    params = deepcopy(operations[operation])
    qid = params['queryId']
    params['variables']['target'] = {"participant_ids": receivers}
    params['variables']['requestId'] = str(uuid1(getnode()))  # can be anything
    url = f"https://api.twitter.com/graphql/{qid}/{operation}"
    if filename:
        media_id = upload_media(filename, session, is_dm=True)
        params['variables']['message']['media'] = {'id': media_id, 'text': text}
    else:
        params['variables']['message']['text'] = {'text': text}
    r = session.post(url, headers=get_auth_headers(session), json=params)
    return r
