import subprocess
import os;
import shutil;
import cv2;
from tqdm import tqdm;
import json;



FILENAME = "segment.mp4"
AR = 0.525
CAMERA_MOVE_PER_FRAME = 2 #px


OUTPUT_FILE_NAME = "output.mp4"
FRAME_DIR = "frames"
OUTPUT_FRAMES_DIR = "out_frames"
AUDIO_FILE_NAME = "audio.aac"

def create_video_from_images(image_path_format, fps, pix_fmt):
    subprocess.run(["ffmpeg", "-framerate", str(fps), "-i", image_path_format, "-c:v", "libx264", "-r", str(fps),"-pix_fmt", pix_fmt, "-y", OUTPUT_FILE_NAME], shell=True)

def establish_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

def detach_audio():
    subprocess.run(["ffmpeg", "-i", FILENAME, "-vn", "-c:a", "copy", "-y", AUDIO_FILE_NAME], shell=True)

def attach_audio():
    subprocess.run(["ffmpeg", "-i", OUTPUT_FILE_NAME, "-i", AUDIO_FILE_NAME, "-c", "copy", "-map", "0:v:0", "-map", "1:a:0", "-y", "final_video.mp4" ], shell=True)

def crop_images(video_width, video_height, fps):
    clip_width = int(video_height * AR)
    end = video_width - clip_width
    establish_dir(OUTPUT_FRAMES_DIR)
    print("Cropping...")
    for (_, _, files) in os.walk(FRAME_DIR):
        for file in tqdm(files):
            img = cv2.imread(f"{FRAME_DIR}/{file}")
            y=0
            x=end
            h=video_height
            w=clip_width
            crop = img[y:y+h, x:x+w]
            cv2.imwrite(f"{OUTPUT_FRAMES_DIR}/{file}",crop)
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
    subprocess.run(["ffmpeg", "-i", FILENAME, f"{FRAME_DIR}/%03d.png"], shell=True)
    

if __name__ == '__main__':
    width, height, fps, pix_fmt = get_video_metadata()
    detach_audio()
    break_video_into_images()
    crop_images(width, height, fps)
    create_video_from_images(f"{OUTPUT_FRAMES_DIR}/%03d.png", fps, pix_fmt)
    attach_audio()
    clean_up()