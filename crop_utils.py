from PIL import Image
import concurrent.futures
import os


NUM_THREADS = 4

def crop_image(input_path, output_path, box):
    image = Image.open(input_path)
    cropped_image = image.crop(box)
    cropped_image.save(output_path)
    image.close()

def crop_images_in_parallel(input_folder, output_folder, crop_box, num_threads = NUM_THREADS):
    os.makedirs(output_folder, exist_ok=True)
    input_paths = [os.path.join(input_folder, filename) for filename in os.listdir(input_folder)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for input_path in input_paths:
            filename = os.path.basename(input_path)
            output_path = os.path.join(output_folder, filename)
            executor.submit(crop_image, input_path, output_path, crop_box)

if __name__ == "__main__":
    input_folder = "input_images_folder"
    output_folder = "output_images_folder"
    crop_box = (100, 100, 300, 300)  # (left, upper, right, lower)
    crop_images_in_parallel(input_folder, output_folder, crop_box)
