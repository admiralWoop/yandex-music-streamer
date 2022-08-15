import asyncio
import math
from asyncio import *

from yandex_music import Client

from mp3 import *

token = ''

track_num = 0
client = Client(token)
client.init()


def load_next_file(file_name: str = 'buffer.mp3'):
    global track_num
    album = client.users_likes_tracks()
    track = album[track_num].fetch_track()
    track.download(file_name, bitrate_in_kbps=192)
    track_num = (track_num + 1) % len(album)


async def get_connection_handler(file_name: str):
    load_next_file(file_name)

    async def read_and_send_mp3_frame(reader: StreamReader, writer: StreamWriter):
        buffer_time = 10
        current_buffer_duration = 0
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        if message[:6] != 'GET / ':
            responce = 'HTTP/1.1 404 Not Found\r\n'
            writer.write(responce.encode('utf8'))
            await writer.drain()
            writer.close()
            return

        while True:
            for frame in fetch_frames(file_name):
                writer.write(frame)
                frame_duration = len(frame) * 8 / (get_bitrate(frame) * 1000)
                current_buffer_duration += frame_duration
                if current_buffer_duration > buffer_time:
                    current_buffer_duration -= 5
                    await asyncio.sleep(current_buffer_duration)
                await writer.drain()
            load_next_file(file_name)

    return read_and_send_mp3_frame


async def main():
    conn_handler = await get_connection_handler('buffer.mp3')
    server = await asyncio.start_server(conn_handler, '', 8083)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())

