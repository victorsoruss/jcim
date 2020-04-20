# jcim 1.0.1

### What's **jcim**? ###

jcim is an improved version of [carykh](https://github.com/carykh)'s [jumpcutter](https://github.com/carykh/jumpcutter). Jumpcutter Improved is an automated video editing tool that modifies the video speed accordingly to audio level.

### What's different? ###

The code has been refactored and mostly commented. Now using youtube-dl instead of pytube ([see carykh/jumpcutter#120](https://github.com/carykh/jumpcutter/issues/120)) and using ffmpeg-python instead of ffmpeg from command line ([see carykh/jumpcutter#154](https://github.com/carykh/jumpcutter/issues/154)). By the way, thanks to [BohdanOpyr](https://github.com/BohdanOpyr), his fork helped me understand how to use ffmpeg-python module. I will be working on adding some features in the future.

## Dependencies ##

Requires [Python](https://www.python.org/downloads/) 3.x and [FFmpeg](https://ffmpeg.org/download.html) installed on the system to work properly.

You will also need to install the following Python 3 modules:

- `audiotsm`
- `ffmpeg-python`
- `numpy`
- `scipy`
- `youtube_dl`

Use pip to install these via the command `pip install <module_name>`. You can learn more about pip [here](https://pip.pypa.io/en/stable/).

## Using jcim ##

Run it with python interpreter, here's the basic syntax:

~~~ 
python jcim.py [option] [argument]
~~~

You may add some other options, here's a list of all available options:

| Option             | Description                                                 | Default value         | Type        | Range                           |
| ------------------ | ----------------------------------------------------------- | --------------------- | ----------- | ------------------------------- |
| -h, --help         | show help                                                   | N/A                   | N/A         | N/A                             |
| -v, --verbose      | show more verbosity info                                    | N/A                   | N/A         | N/A                             |
| -q, --quiet        | show only error messages                                    | N/A                   | N/A         | N/A                             |
| -i, --input_file   | sets video or url you want to modify                        | N/A                   | File or URL | N/A                             |
| -o, --output_file  | sets name of output file                                    | `OUTPUT_<input_file>` | File        | N/A                             |
| --frame_margin     | sets amount of frames that should be kept between cut clips | `0`                   | Integer     | N/A                             |
| --frame_quality    | sets the quality of output frames                           | `3`                   | Integer     | from 1 (highest) to 31 (lowest) |
| --sample_rate      | sets sample rate of input and output video                  | Auto detected by jcim | Float       | N/A                             |
| --frame_rate       | sets frame rate of input and output video                   | Auto detected by jcim | Float       | N/A                             |
| --silent_threshold | sets the sensitivity to be considered "sounded"             | `0.03`                | Float       | from 0 (silence) to 1 (max vol) |
| --silent_speed     | sets which speed silent frames should be played             | `5.0 `                | Float       | N/A                             |
| --sounded_speed    | sets which speed sounded frames should be played a          | `1.5 `                | Float       | N/A                             |

Remember that the only option required to run jcim is `--input_file`, all the others are optional.

Here are some examples:

### Making the Jump Cut effect ###

Let's say we have a video called file.mp4 and we want to make the jump cut effect, you can use the following options:

~~~
python jcim.py -i file.mp4 --silent_speed 999999 --sounded_speed 1
~~~

You may notice the transition isn't as smooth as you may want it to be, you can fix it by using the `--frame_margin` option, which adds a margin of silent frames to the sounded clips . Let's add a margin of two frames for each cut:

~~~
python jcim.py -i file.mp4 --silent_speed 999999 --sounded_speed 1 --frame_margin 2
~~~

The ouput file for the command above will be named "OUTPUT_file.mp4", but let's say you want to call it "food.mp4", you can make it via this command:

~~~
python jcim.py -i file.mp4 --silent_speed 999999 --sounded_speed 1 --frame_margin 2 -o food.mp4
~~~

### Using a video from web as jcim input ###

Let's say you have a video you want to download and edit with jcim, you can directly input the URL of the video and jcim will download the best quality for given video. Example:

~~~
python jcim.py -i http://example.com/video.mp4 [other options]
~~~

Note: When you use a video from the web, jcim will merge the output file to MKV format. You can modify this behaviour with `-o, --output_file` option, here's an example:

~~~
python jcim.py -i http://example.com/video.mp4 [other options] -o video.mp4
~~~

### Using a file with spaces in the name ###

You need to escape spaces when your filename has spaces in it.

Let's say your file is called "video demonstration.mp4", you would do something like:

~~~
python jcim.py -i "video demonstration.mp4" [other options]
~~~

## License ##

jcim is licensed under the MIT license.
