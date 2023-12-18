import subprocess
import os;
import shutil;
import cv2;
from tqdm import tqdm;
import json;
from PIL import Image
from concurrent.futures import ThreadPoolExecutor



FILENAME = "segment.mp4"
AR = 0.525
CAMERA_MOVE_PER_FRAME = 5 #px
NUM_THREADS = 3

OUTPUT_FILE_NAME = "output.mp4"
FRAME_DIR = "frames"
OUTPUT_FRAMES_DIR = "out_frames"
AUDIO_FILE_NAME = "audio.aac"


def create_video_from_images(image_path_format, fps, pix_fmt):
    subprocess.run(["ffmpeg", "-progress", "-", "-nostats", "-framerate", str(fps), "-i", image_path_format, "-c:v", "libx264", "-r", str(fps),"-pix_fmt", pix_fmt, "-y", OUTPUT_FILE_NAME])

def establish_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

def detach_audio():
    subprocess.run(["ffmpeg", "-progress", "-", "-nostats", "-i", FILENAME, "-vn", "-c:a", "copy", "-y", AUDIO_FILE_NAME])


def attach_audio():
    subprocess.run(["ffmpeg", "-progress", "-", "-nostats", "-i", OUTPUT_FILE_NAME, "-i", AUDIO_FILE_NAME, "-c", "copy", "-map", "0:v:0", "-map", "1:a:0", "-y", "final_video.mp4" ])


def crop_image(input_path, output_path, box):
    image = Image.open(input_path)
    cropped_image = image.crop(box)
    cropped_image.save(output_path)
    image.close()


def crop_images(video_width, video_height, fps):
    clip_width = int(video_height * AR)
    end = video_width - clip_width
    establish_dir(OUTPUT_FRAMES_DIR)
    input_paths = [os.path.join(FRAME_DIR, filename) for filename in os.listdir(FRAME_DIR)]
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for input_path in tqdm(input_paths):
            filename = os.path.basename(input_path)
            output_path = os.path.join(OUTPUT_FRAMES_DIR, filename)
            executor.submit(crop_image, input_path, output_path, (end, 0, end+clip_width, video_height))
            end=max(end-CAMERA_MOVE_PER_FRAME, 0)


def clean_up(): 
    os.remove(OUTPUT_FILE_NAME)
    os.remove(AUDIO_FILE_NAME)
    shutil.rmtree(FRAME_DIR)
    shutil.rmtree(OUTPUT_FRAMES_DIR)


def get_video_metadata():
    output = subprocess.check_output(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", FILENAME])
    json_data = json.loads(output.decode('utf-8'))
    video_meta_data = json_data['streams'][0]
    width, height, fps, pix_fmt = video_meta_data['width'], video_meta_data['height'], int(video_meta_data['r_frame_rate'].split('/')[0]), video_meta_data['pix_fmt']
    return width, height, fps, pix_fmt


def break_video_into_images():
    establish_dir(FRAME_DIR)
    subprocess.run(["ffmpeg", "-progress", "-", "-nostats", "-i", FILENAME, f"{FRAME_DIR}/%03d.jpg"])
    
if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        metadata = executor.submit(get_video_metadata)
        executor.submit(detach_audio)
        image_generator = executor.submit(break_video_into_images)
    width, height, fps, pix_fmt = metadata.result()
    crop_images(width, height, fps)
    create_video_from_images(f"{OUTPUT_FRAMES_DIR}/%03d.jpg", fps, pix_fmt)
    attach_audio()
    clean_up()