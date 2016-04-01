# Tests for hw1

import numpy as np
from numpy.random import RandomState
from hw1 import to_grayscale, split_channels, average, lighten, darken, glow

class TestHw1:
    def setup(self):
        self.random = RandomState(1337)
        self.large_shape_rgb = (200, 200, 3)
        self.large_shape_gray = (200, 200)
        self.large_black_rgb = np.zeros(self.large_shape_rgb, dtype=np.uint8)
        self.large_white_rgb = np.full(self.large_shape_rgb, 255, dtype=np.uint8)
        self.large_white_gray = np.full(self.large_shape_gray, 255, dtype=np.uint8)
        
    def check_equal(self, image1, image2):
        assert (image1==image2).all()
        
    def check_image(self, image):
        assert image.dtype == np.uint8
        
    def check_large_rgb(self, image):
        self.check_image(image)
        assert image.shape == self.large_shape_rgb
        
    def check_large_gray(self, image):
        self.check_image(image)
        assert image.shape == self.large_shape_gray
        
    def test_all_sanity(self):
        to_grayscale(self.large_white_rgb)
        split_channels(self.large_white_rgb)
        average(self.large_white_rgb, self.large_white_rgb)
        lighten(self.large_white_rgb, self.large_black_rgb)
        darken(self.large_white_rgb, self.large_white_rgb)
        glow(self.large_white_rgb, self.large_black_rgb)
        
    def test_to_grayscale_sanity(self):
        output = to_grayscale(self.large_white_rgb)
        self.check_large_gray(output)
        self.check_equal(output, self.large_white_gray)
        
    def test_split_channels_sanity(self):
        output = split_channels(self.large_white_rgb)
        assert len(output) == 3
        for channel in output:
            self.check_large_gray(channel)
            self.check_equal(channel, self.large_white_gray)
        
    def test_average_sanity(self):
        output = average(self.large_white_rgb, self.large_white_rgb)
        self.check_large_rgb(output)
        self.check_equal(output, self.large_white_rgb)
        
    def test_lighten_sanity(self):
        output = lighten(self.large_white_rgb, self.large_black_rgb)
        self.check_large_rgb(output)
        self.check_equal(output, self.large_white_rgb)
        
    def test_darken_sanity(self):
        output = darken(self.large_white_rgb, self.large_white_rgb)
        self.check_large_rgb(output)
        self.check_equal(output, self.large_white_rgb)
        
    def test_glow_sanity(self):
        output = glow(self.large_white_rgb, self.large_black_rgb)
        self.check_large_rgb(output)
        self.check_equal(output, self.large_white_rgb)