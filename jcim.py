import argparse
import base64
import glob
import math
import os
import platform
import time
from shutil import copyfile

import numpy
import youtube_dl
import ffmpeg
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile

ARGUMENTS_HELP = {
    'description': 'Modifies a file to play at different speeds varying accordingly to audio level',
    'i': 'sets the video input or url',
    'o': 'sets the output file',
    'q': 'show less information, error messages are still shown to user',
    'v': 'show more information about process',
    'silent_threshold': 'sets the sensitivity to be considered "sounded".range: 0 (silence) to 1 (max volume). '
                        'default: 0.03',
    'sounded_speed': 'sets which speed sounded frames should be played at.default: 1.5',
    'silent_speed': 'sets which speed silent frames should be played at.default: 5',
    'frame_margin': 'sets what amount of frames should be kept before and after the cut clips, for context. '
                    'default: 1',
    'sample_rate': 'sets sample rate of the input and output videos',
    'frame_rate': 'sets frame rate of the input and output videos',
    'frame_quality': 'sets the quality for the extracted frames from video input.range: 1 (highest) to 31 (lowest). '
                     'default: 3 '}


def send(message, message_type=''):
    if not QUIET:
        if message_type == 'error':
            print('jcim: [!] ' + str(message))
        elif message_type == 'info':
            print('jcim: [I] ' + str(message))
        else:
            if VERBOSE:
                print('jcim: [V] ' + str(message))
    else:
        if message_type == 'error':
            print('jcim: [!] ' + str(message))


def create_temp(temp):
    """
    Creates temp folder with jcim and an ID based of the time.
    :return: path to temp folder
    """
    if temp == "":
        send("TEMP is not set", "error")
        exit()

    # temp folder will always start with "jcim-"
    folder_name = ["jcim-"]

    # get current time in base64
    folder_id = str(base64.urlsafe_b64encode(str(time.time()).encode("utf-8")), "utf-8")

    # appends to folder name
    folder_name.append(folder_id)

    send("temp folder name is set to: \'" + str().join(folder_name) + "\'", "info")

    # path to variable
    path = os.path.join(temp, str().join(folder_name))

    try:
        send("creating temp folder at: \'" + path + "\'")
        # tries to create temp folder
        os.mkdir(path)
    except OSError:
        send("an error occurred when creating temp folder", "error")
        exit()

    send("successfully created temp folder")

    # cleaning variables
    folder_name = folder_id = None
    del folder_name, folder_id

    send("temp path is set to: \'" + path + "\'")

    return path


def download_video(url, path):
    """
    Download a video with youtube-dl
    :param url: url to video
    :param path: sets download path to video
    :return: full path to downloaded file
    """

    # options for youtube-dl
    options = {
        'quiet': QUIET,
        'verbose': VERBOSE,
        'merge_output_format': 'mkv',
        'noplaylist': True,
        'outtmpl': os.path.join(path, '') + '%(title)s.%(ext)s'
    }
    try:
        with youtube_dl.YoutubeDL(options) as video:

            # download video
            video.extract_info(url)

            # empty variable to store video filename
            name_buffer = ''

            # get the downloaded video filename from temp folder
            fileset = [os.path.basename(file) for file in glob.glob(path + "**/*.*")]

            # gets the only file inside of the folder
            for file in fileset:
                name_buffer = file
            send(name_buffer + " has been selected")

            # create new filename with full path
            output = os.path.join(path, str(name_buffer).replace(" ", "_"))

            try:
                # rename file with new name
                os.rename(os.path.join(path, name_buffer), output)
                send("file has been renamed to: " + name_buffer.replace(" ", "_"))
            except OSError as error:
                send(error, "error")
                exit(1)

            # cleaning variables
            name_buffer = fileset = file = None
            del name_buffer, fileset, file

            return output
    except Exception as exception:
        send(exception, "error")
        exit(1)


def get_audio_max_volume(data):
    max_volume = float(numpy.max(data))
    min_volume = float(numpy.min(data))
    return max(max_volume, -min_volume)


def get_video_path(video):
    """
    Wrapper for input. If video fed is a url, it will attempt to download.
    :param video: file path or web URL
    :return: full path to video.
    """
    global JCIM_TEMP

    if os.path.isfile(video):
        return os.path.abspath(video)
    else:
        return download_video(video, JCIM_TEMP)


def get_video_metadata(video, stream_type, key):
    """
    Get video metadata based on FFmpeg.
    :param video: video path
    :param stream_type: FFmpeg stream type, it can be 'video' or 'audio'
    :param key: is the specific information for given stream
    :return: stored item for given key
    """
    probe = ffmpeg.probe(video)

    info_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == stream_type), None)
    info_dict = dict(info_stream)

    return info_dict[key]


def get_video_output_name(name):
    """
    Get output name for new video
    :param name: original video
    :return: output name
    """
    output = "OUTPUT_" + (os.path.basename(name))
    if os.path.isfile(output):
        os.rename(output, output + "_old")
    return output


def copy_frame(in_frame, out_frame):
    """
    Copy frames
    :param in_frame: input frame
    :param out_frame: output frame
    :return: True or False if completed successfully
    """
    src = JCIM_TEMP + "/frame{:07d}".format(in_frame + 1) + ".jpg"
    dst = JCIM_TEMP + "/new_frame{:07d}".format(out_frame + 1) + ".jpg"
    if not os.path.isfile(src):
        return False
    copyfile(src, dst)
    return True


def fix_ffmpeg_behaviour():
    """ 
    Fixes strange behaviour of CLI after running FFmpeg
    """
    if platform.system() == "Linux":
        os.system("stty sane")
    


parser = argparse.ArgumentParser(description=ARGUMENTS_HELP.get('description'))
parser.add_argument('-i', '--input_file', type=str, help=ARGUMENTS_HELP.get('i'), required=True)
parser.add_argument('-o', '--output_file', type=str, default="", help=ARGUMENTS_HELP.get('o'))
parser.add_argument('-q', '--quiet', action='store_true', help=ARGUMENTS_HELP.get('q'))
parser.add_argument('-v', '--verbose', action='store_true', help=ARGUMENTS_HELP.get('v'))
parser.add_argument('--frame_margin', type=float, default=0, help=ARGUMENTS_HELP.get('frame_margin'))
parser.add_argument('--frame_quality', type=int, default=3, help=ARGUMENTS_HELP.get('frame_quality'))
parser.add_argument('--frame_rate', type=float, default=0, help=ARGUMENTS_HELP.get('frame_rate'))
parser.add_argument('--sample_rate', type=float, default=0, help=ARGUMENTS_HELP.get('sample_rate'))
parser.add_argument('--silent_threshold', type=float, default=0.03, help=ARGUMENTS_HELP.get('silent_threshold'))
parser.add_argument('--silent_speed', type=float, default=5.00, help=ARGUMENTS_HELP.get('silent_speed'))
parser.add_argument('--sounded_speed', type=float, default=1.50, help=ARGUMENTS_HELP.get('sounded_speed'))
argument = parser.parse_args()

QUIET = argument.quiet
VERBOSE = argument.verbose
TEMP = os.getcwd()
JCIM_TEMP = create_temp(TEMP)

INPUT_FILE = get_video_path(argument.input_file)

if argument.frame_rate == 0:
    send("--frame_rate not set, automatically detecting frame rate..")
    FRAME_RATE = eval(get_video_metadata(INPUT_FILE, 'video', 'r_frame_rate'))
else:
    FRAME_RATE = argument.frame_rate

if argument.sample_rate == 0:
    send("--sample_rate not set, automatically detecting sample rate..")
    SAMPLE_RATE = eval(get_video_metadata(INPUT_FILE, 'audio', 'sample_rate'))
else:
    SAMPLE_RATE = argument.frame_rate

if str(argument.output_file).strip(" ") == "":
    OUTPUT_FILE = get_video_output_name(INPUT_FILE)
    send("--output_file not set, using " + OUTPUT_FILE)
else:
    OUTPUT_FILE = argument.output_file

AUDIO_FADE_ENVELOPE_SIZE = 400
FRAME_MARGIN = argument.frame_margin
FRAME_QUALITY = argument.frame_quality
NEW_SPEED = [argument.silent_speed, argument.sounded_speed]
SILENT_THRESHOLD = argument.silent_threshold

send("input file is " + str(os.path.basename(INPUT_FILE)))
send("frame margin is " + str(FRAME_MARGIN))
send("frame quality is " + str(FRAME_QUALITY))
send("frame rate is " + str(FRAME_RATE))
send("sample rate is " + str(SAMPLE_RATE))
send("silent threshold is " + str(SILENT_THRESHOLD))
send("new speed set (silent, sounded) is " + str(NEW_SPEED))

send("extracting resources from video", "info")

try:
    a = ffmpeg \
        .input(INPUT_FILE) \
        .output(os.path.join(JCIM_TEMP, "") + "audio.wav",
                **{'loglevel': 'error', 'nostats': '-hide_banner'}) \
        .run_async(quiet=QUIET)
    ffmpeg \
        .input(INPUT_FILE) \
        .output(os.path.join(JCIM_TEMP, "") + "frame%07d.jpg",
                **{'qscale:v': FRAME_QUALITY, 'loglevel': 'error', 'stats': '-hide_banner'}) \
        .run(quiet=QUIET)
    a.wait()
except Exception as e:
    send(e, "error")
    exit(1)
finally:
    fix_ffmpeg_behaviour()

send("successfully extracted", "info")

send("started editing process", "info")
# sample_rate and audio_data of extracted "audio.wav" file
sample_rate, audio_data = wavfile.read(os.path.join(JCIM_TEMP, "") + "audio.wav")

audio_sample_count = audio_data.shape[0]
# get the maximum volume of media
max_audio_volume = get_audio_max_volume(audio_data)
samples_per_frame = sample_rate / FRAME_RATE
# get amount of frames with audio
audio_frame_count = int(math.ceil(audio_sample_count / samples_per_frame))
# array to store the frames with loud audio
has_loud_audio = numpy.zeros(audio_frame_count)

for i in range(audio_frame_count):
    start = int(i * samples_per_frame)
    end = min(int((i + 1) * samples_per_frame), audio_sample_count)
    # get respective audio data for frames
    audio_chunks = audio_data[start:end]
    max_chunks_volume = float(get_audio_max_volume(audio_chunks)) / max_audio_volume
    # if maximum volume surpasses the silent threshold, it'll add an item to has_loud_audio array
    if max_chunks_volume >= SILENT_THRESHOLD:
        has_loud_audio[i] = 1

chunks = [[0, 0, 0]]

# array of frames that should be included
should_include_frame = numpy.zeros(audio_frame_count)

for i in range(audio_frame_count):
    start = int(max(0, i - FRAME_MARGIN))
    end = int(min(audio_frame_count, i + 1 + FRAME_MARGIN))
    # includes frame if has loud audio
    should_include_frame[i] = numpy.max(has_loud_audio[start:end])
    if (i >= 1) and should_include_frame[i] != should_include_frame[i - 1]:
        chunks.append([chunks[-1][1], i, should_include_frame[i - 1]])

chunks.append([chunks[-1][1], audio_frame_count, should_include_frame[-1]])
chunks = chunks[1:]

output_audio_data = numpy.zeros((0, audio_data.shape[1]))
output_pointer = 0

last_existing_frame = None
for chunk in chunks:
    audio_chunk = audio_data[int(chunk[0] * samples_per_frame): int(chunk[1] * samples_per_frame)]

    start_file = os.path.join(JCIM_TEMP, "") + "temp_start.wav"
    end_file = os.path.join(JCIM_TEMP, "") + "temp_end.wav"

    wavfile.write(start_file, SAMPLE_RATE, audio_chunk)
    with WavReader(start_file) as reader:
        with WavWriter(end_file, reader.channels, reader.samplerate) as writer:
            audio_stretch = phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])])
            audio_stretch.run(reader, writer)

    altered_audio_data = wavfile.read(end_file)[1]
    length = altered_audio_data.shape[0]
    end_pointer = output_pointer + length
    output_audio_data = numpy.concatenate((output_audio_data, altered_audio_data / max_audio_volume))

    if length < AUDIO_FADE_ENVELOPE_SIZE:
        # audio is smaller than 0.01s, let's remove it
        output_audio_data[output_pointer:end_pointer] = 0
    else:
        pre_mask = numpy.arange(AUDIO_FADE_ENVELOPE_SIZE) / AUDIO_FADE_ENVELOPE_SIZE
        # makes fade-envelope mask stereo
        mask = numpy.repeat(pre_mask[:, numpy.newaxis], 2, axis=1)
        output_audio_data[output_pointer:output_pointer + AUDIO_FADE_ENVELOPE_SIZE] *= mask
        output_audio_data[end_pointer - AUDIO_FADE_ENVELOPE_SIZE:end_pointer] *= 1 - mask

    start_output_frame = int(math.ceil(output_pointer / samples_per_frame))
    end_output_frame = int(math.ceil(end_pointer / samples_per_frame))

    for output_frame in range(start_output_frame, end_output_frame):
        input_frame = int(chunk[0] + NEW_SPEED[int(chunk[2])] * (output_frame - start_output_frame))
        did_it_work = copy_frame(input_frame, output_frame)
        if did_it_work:
            last_existing_frame = input_frame
        else:
            copy_frame(last_existing_frame, output_frame)
    output_pointer = end_pointer

wavfile.write(os.path.join(JCIM_TEMP, "") + "new_audio.wav", SAMPLE_RATE, output_audio_data)

send("exporting the video", "info")
try:
    f_video = ffmpeg.input(os.path.join(JCIM_TEMP, "") + "new_frame*.jpg", pattern_type='glob', framerate=FRAME_RATE)
    f_audio = ffmpeg.input(os.path.join(JCIM_TEMP, "") + "new_audio.wav")
    out = ffmpeg.output(f_video, f_audio, OUTPUT_FILE, framerate=FRAME_RATE,
                        **{'loglevel': 'error', 'stats': '-hide_banner'})
    out.overwrite_output().run(quiet=QUIET)
except Exception as e:
    send(e, "error")
    exit(1)
finally:
    fix_ffmpeg_behaviour()

send("process done", "info")
exit(0)