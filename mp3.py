from typing import Generator


def fetch_frames(file_name: str = 'buffer.mp3') -> Generator[bytes, None, None]:
    with open('buffer.mp3', 'rb', buffering=1024) as mp3_buffer:
        while mp3_buffer.peek(1) != b'':
            header = mp3_buffer.read(4)
            frame_len = get_frame_len(bytes(header))
            yield header + mp3_buffer.read(frame_len - 4)
        mp3_buffer.close()


def get_frame_len(header: bytes):
    layer = get_layer(header)
    padding = int.from_bytes([header[2] >> 1], 'big') & 0x1
    bitrate = get_bitrate_from_header(header)
    sample_rate = get_samplerate_from_header(header)
    if layer == 3:
        return int(12 * bitrate * 1000 / sample_rate + padding) * 4
    else:
        return int(144 * bitrate * 1000 / sample_rate) + padding


def get_bitrate(frame: bytes):
    header = frame[0:4]
    return get_bitrate_from_header(header)


def get_bitrate_from_header(header: bytes):
    version = get_version(header)
    layer = get_layer(header)
    bitrate_index = int.from_bytes([header[2] >> 4], 'big') & 0xf
    if version == 3:
        if layer == 3:
            bitrate = 32 * bitrate_index
        elif layer == 2:
            bitrate = [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384, 'bad'][bitrate_index]
        elif layer == 1:
            bitrate = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 'bad'][bitrate_index]
        else:
            raise ValueError('invalid MPEG layer')
    elif version in [2, 0]:
        if layer == 3:
            bitrate = [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256, 'bad'][bitrate_index]
        elif (layer == 2) or (layer == 1):
            bitrate = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 'bad'][bitrate_index]
        else:
            raise ValueError('invalid MPEG layer')
    else:
        raise ValueError('invalid MPEG version')
    return bitrate


def get_samplerate_from_header(header: bytes):
    sample_rate_index = int.from_bytes([header[2] >> 2], 'big') & 0x3
    version = get_version(header)
    if version == 3:
        sample_rate = [44100, 48000, 32000, 'bad'][sample_rate_index]
    elif version in [2, 0]:
        if version == 2:
            sample_rate = [22050, 24000, 16000, 'bad'][sample_rate_index]
        else:
            sample_rate = [11025, 12000, 8000, 'bad'][sample_rate_index]
    else:
        raise ValueError('invalid MPEG version')
    return sample_rate


def get_version(header: bytes):
    return int.from_bytes([header[1] >> 3], 'big') & 0x3


def get_layer(header: bytes):
    return int.from_bytes([header[1] >> 1], 'big') & 0x3
