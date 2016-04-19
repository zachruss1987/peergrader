# Example homework assignment 1

import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def to_grayscale(img):
    """Converts an RGB image to grayscale
    Args:
        img: numpy array of the input 3-channel RGB image
    Returns:
        numpy output array of single channel grayscale image
    """
    gray = img.mean(axis=2)
    return gray.astype(img.dtype)

def split_channels(img):
    """Splits an RGB image into 3 grayscale channel images
    Args:
        img: numpy array of the input 3-channel RGB image
    Returns:
        List of grayscale channel images as numpy arrays
    """
    channels = [img[:,:,i] for i in range(3)]
    return channels
    
def average(img1, img2):
    """Averages two images together at the pixel level
    Args:
        img2: numpy array of the first input 3-channel RGB image
        img1: numpy array of the second input 3-channel RGB image
    Returns:
        numpy output array of the averaged pixels of the input
    """
    averaged = np.mean(np.array([img1, img2]), axis=0)
    return averaged.astype(img1.dtype)
    
def lighten(img1, img2):
    """Performs the "lighten" blend operation on two images
        Lighten operation takes the maximum value between the two images
        for each channel and pixel location
    Args:
        img2: numpy array of the first input 3-channel RGB image
        img1: numpy array of the second input 3-channel RGB image
    Returns:
        numpy output array of the lightened pixels of the input
    """
    lightened = np.max(np.array([img1, img2]), axis=0)
    return lightened.astype(img1.dtype)
    
def darken(img1, img2):
    """Performs the "darken" blend operation on two images
        Darken operation takes the minimum value between the two images
        for each channel and pixel location
    Args:
        img2: numpy array of the first input 3-channel RGB image
        img1: numpy array of the second input 3-channel RGB image
    Returns:
        numpy output array of the darkened pixels of the input
    """
    darkened = np.min(np.array([img1, img2]), axis=0)
    return darkened.astype(img1.dtype)
    
def glow(img1, img2):
    """Performs the "glow" blend operation on two images
        Glow operation applies the following formula to each pixel:
        (image1 ** 2) / (255 - image2)
    Args:
        img2: numpy array of the upper input 3-channel RGB image
        img1: numpy array of the lower input 3-channel RGB image
    Returns:
        numpy output array of the darkened pixels of the input
    """
    glowing = img1.astype(np.float32) ** 2
    glowing = glowing / (255 - img2)
    glowing = np.clip(glowing, 0, 255)
    return glowing.astype(img1.dtype)
    
def showtext(image, text):
    font = ImageFont.truetype(font='FreeMono.ttf', size=100)
    draw = ImageDraw.Draw(image)
    white = (200,200,200)
    black = (0,0,0)
    if image.mode == 'L':
        white = 200
        black = 0
    x, y = 10, max(0, image.size[1] - 100)
    for xoffset in [-2,2]:
        for yoffset in [-2,2]:
            draw.text((x+xoffset, y+yoffset), text, font=font, fill=white)
    draw.text((x,y), text, font=font, fill=black)
    del draw
    return image
    
def main():
    if not os.path.exists('output'):
        os.makedirs('output')
    print 'Loading balloon image'
    balloon_image = Image.open('images/balloon.jpg')
    balloon = np.array(balloon_image)
    showtext(balloon_image, 'Balloon Original')
    balloon_image.show()
    
    print 'Testing to_grayscale'
    output = to_grayscale(balloon)
    gray = Image.fromarray(output, 'L')
    showtext(gray, 'Balloon Grayscale')
    gray.show()
    gray.save('output/to_grayscale.jpg')
    
    print 'Testing split_channels'
    channels = ['Red', 'Green', 'Blue']
    for index, channel in enumerate(split_channels(balloon)):
        split = Image.fromarray(channel, 'L')
        showtext(split, 'Balloon %s Channel' % channels[index])
        split.show()
        split.save('output/split_channels_%s.jpg' % channels[index].lower())
        
    print 'Loading sky image'
    sky_image = Image.open('images/sky.jpg')
    sky = np.array(sky_image)
    showtext(sky_image, 'Sky Original')
    sky_image.show()
    
    print 'Testing average'
    output = average(balloon, sky)
    averaged = Image.fromarray(output)
    showtext(averaged, 'Average Effect')
    averaged.show()
    averaged.save('output/average.jpg')
    
    print 'Testing lighten'
    output = lighten(balloon, sky)
    lightened = Image.fromarray(output)
    showtext(lightened, 'Lighten Effect')
    lightened.show()
    lightened.save('output/lighten.jpg')
    
    print 'Testing darken'
    output = darken(balloon, sky)
    darkened = Image.fromarray(output)
    showtext(darkened, 'Darken Effect')
    darkened.show()
    darkened.save('output/darken.jpg')
    
    print 'Testing glow'
    output = glow(balloon, sky)
    glowing = Image.fromarray(output)
    showtext(glowing, 'Glow Effect')
    glowing.show()
    glowing.save('output/glow.jpg')

if __name__ == "__main__":
    main()