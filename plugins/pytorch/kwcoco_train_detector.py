# ckwg +29
# Copyright 2025 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#    * Neither name of Kitware, Inc. nor the names of any contributors may be used
#    to endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Base class and helpers used to adapt the input data format into COCO / KWCoco
"""
import math
import numpy as np
import os
import random
# import ubelt as ub
from PIL import Image
import scriptconfig as scfg
from distutils.util import strtobool

# from kwiver.vital.types import Image
from kwiver.vital.types import ImageContainer
from kwiver.vital.types import DetectedObjectSet
from kwiver.vital.types import DetectedObjectType
from kwiver.vital.types import BoundingBoxD

from kwiver.vital.algo import TrainDetector
from .netharn_utils import safe_crop


class KWCocoTrainDetectorConfig(scfg.DataConfig):
    """
    Configuration options for trainers that use the Coco data adapter.
    """
    area_lower_bound = 0
    area_upper_bound = 0
    border_exclude = -1
    chip_expansion = 1.0
    chip_extension = '.png'
    chip_method = 'use_box'
    chip_height = 640
    chip_width = 640
    detector_model = ''
    gt_frames_only = False
    max_neg_per_frame = 5
    max_overlap_for_negative = 0.05
    max_scale_wrt_chip = 2.0
    min_overlap_for_association = 0.90
    mode = 'detector'
    negative_category = 'background'
    no_format = False
    reduce_category = ''

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.gt_frames_only, str):
            self.gt_frames_only = strtobool(self.gt_frames_only)
        if isinstance(self.no_format, str):
            self.no_format = strtobool(self.no_format)

        import kwutil
        self.area_lower_bound = kwutil.Yaml.coerce(self.area_lower_bound)
        self.area_upper_bound = kwutil.Yaml.coerce(self.area_upper_bound)
        self.border_exclude = kwutil.Yaml.coerce(self.border_exclude)
        self.chip_expansion = kwutil.Yaml.coerce(self.chip_expansion)
        self.chip_height = kwutil.Yaml.coerce(self.chip_height)
        self.chip_width = kwutil.Yaml.coerce(self.chip_width)
        self.max_scale_wrt_chip = kwutil.Yaml.coerce(self.max_scale_wrt_chip)
        self.min_overlap_for_association = kwutil.Yaml.coerce(self.min_overlap_for_association)
        self.max_neg_per_frame = kwutil.Yaml.coerce(self.max_neg_per_frame)
        self.max_overlap_for_negative = kwutil.Yaml.coerce(self.max_overlap_for_negative)


class KWCocoTrainDetector(TrainDetector):
    """
    Base class for detector trainers that can operate on kwcoco files
    """
    def __init__( self ):
        TrainDetector.__init__( self )
        self._config = KWCocoTrainDetectorConfig()

    def filter_truth( self, init_truth, categories ):
        print('[KWCocoTrainDetector] filter_truth')

        filtered_truth = DetectedObjectSet()
        use_frame = True
        max_length = int( self._max_scale_wrt_chip * float( self._chip_width ) )
        for i, item in enumerate( init_truth ):
            if item.type is None:
                continue
            class_lbl = item.type.get_most_likely_class()
            if categories is not None and not categories.has_class_name( class_lbl ):
                if self._mode == "detection_refiner":
                    class_lbl = self._negative_category
                else:
                    continue
            if categories is not None:
                class_lbl = categories.get_class_name( class_lbl )
            elif class_lbl not in self._categories:
                self._categories.append( class_lbl )

            item.type = DetectedObjectType( class_lbl, 1.0 )

            if self._mode == "detector" and \
               ( item.bounding_box.width() > max_length or
                 item.bounding_box.height() > max_length ):
                use_frame = False
                break

            filtered_truth.add( item )

        if self._gt_frames_only and len( init_truth ) == 0:
            use_frame = False

        return filtered_truth, use_frame

    def compute_scale_factor( self, detections, min_scale=0.10, max_scale=10.0 ):
        print('[KWCocoTrainDetector] compute_scale_factor')
        cumulative = 0.0
        count = 0
        for i, item in enumerate( detections ):
            if item.type is None:
                continue
            class_lbl = item.type.get_most_likely_class()
            if class_lbl not in self._target_type_scales:
                continue
            box_width = item.bounding_box.width()
            box_height = item.bounding_box.height()
            box_area = float( box_width * box_height )
            if box_area < 1.0:
                continue
            cumulative += math.sqrt( self._target_type_scales[ class_lbl ] / box_area )
            count += 1
        if count == 0:
            output = 1.0
        else:
            output = cumulative / count
        if output >= max_scale:
            output = max_scale
        if output <= min_scale:
            output = min_scale
        print( "Computed image dim scale factor: " + str( output ) )
        return output

    def extract_chips_for_dets( self, image_files, truth_sets ):
        print('[KWCocoTrainDetector] extract_chips_for_dets')
        import cv2
        output_files = []
        output_dets = []

        for i in range( len( image_files ) ):
            filename = image_files[ i ]
            groundtruth = truth_sets[ i ]
            detections = []
            scale = 1.0

            if self._target_type_scales:
                scale = self.compute_scale_factor( groundtruth )

            if len( groundtruth ) > 0:
                img = cv2.imread( filename )

                if len( np.shape( img ) ) < 2:
                    continue

                img_max_x = np.shape( img )[1]
                img_max_y = np.shape( img )[0]

                # Optionally scale image
                if scale != 1.0:
                    img_max_x = int( scale * img_max_x )
                    img_max_y = int( scale * img_max_y )
                    img = cv2.resize( img, ( img_max_x, img_max_y ) )

                # Run optional background detector on data
                if self._detector_model:
                    kw_image = Image( img )
                    kw_image_container = ImageContainer( kw_image )
                    detections = self._detector.detect( kw_image_container )

            if len( groundtruth ) == 0 and len( detections ) == 0:
                continue

            overlaps = np.zeros( ( len( detections ), len( groundtruth ) ) )
            det_boxes = []

            for det in detections:
                bbox = det.bounding_box
                det_boxes.append( ( int( bbox.min_x() ),
                                    int( bbox.min_y() ),
                                    int( bbox.width() ),
                                    int( bbox.height() ) ) )

            for i, gt in enumerate( groundtruth ):
                # Extract chip for this detection
                bbox = gt.bounding_box

                bbox_min_x = int( bbox.min_x() * scale )
                bbox_max_x = int( bbox.max_x() * scale )
                bbox_min_y = int( bbox.min_y() * scale )
                bbox_max_y = int( bbox.max_y() * scale )

                bbox_width = bbox_max_x - bbox_min_x
                bbox_height = bbox_max_y - bbox_min_y

                max_overlap = 0.0

                for j, det in enumerate( det_boxes ):

                    # Compute overlap between detection and truth
                    ( det_min_x, det_min_y, det_width, det_height ) = det

                    # Get the overlap rectangle
                    overlap_x0 = max( bbox_min_x, det_min_x )
                    overlap_y0 = max( bbox_min_y, det_min_y )
                    overlap_x1 = min( bbox_max_x, det_min_x + det_width )
                    overlap_y1 = min( bbox_max_y, det_min_y + det_height )

                    # Check if there is an overlap
                    if overlap_x1 - overlap_x0 <= 0 or overlap_y1 - overlap_y0 <= 0:
                        continue

                    # If yes, calculate the ratio of the overlap
                    det_area = float( det_width * det_height )
                    gt_area = float( bbox_width * bbox_height )
                    int_area = float( ( overlap_x1 - overlap_x0 ) * ( overlap_y1 - overlap_y0 ) )
                    overlap = min( int_area / det_area, int_area / gt_area )
                    overlaps[ j, i ] = overlap

                    if overlap >= self._min_overlap_for_association and overlap > max_overlap:
                        max_overlap = overlap

                        bbox_min_x = det_min_x
                        bbox_min_y = det_min_y
                        bbox_max_x = det_min_x + det_width
                        bbox_max_y = det_min_y + det_height

                        bbox_width = det_width
                        bbox_height = det_height

                if self._chip_method == "fixed_width" or self._chip_method == "native_square":
                    if self._chip_method == "fixed_width":
                        chip_width = int( self._chip_width )
                        chip_height = int( self._chip_height )
                    else:
                        chip_width = max( bbox_width, bbox_height )
                        chip_height = chip_width
                    half_width = int( chip_width / 2 )
                    half_height = int( chip_height / 2 )

                    bbox_min_x = int( ( bbox_min_x + bbox_max_x ) / 2 ) - half_width
                    bbox_min_y = int( ( bbox_min_y + bbox_max_y ) / 2 ) - half_height
                    bbox_max_x = bbox_min_x + chip_width
                    bbox_max_y = bbox_min_y + chip_height

                    bbox_width = chip_width
                    bbox_height = chip_height

                if self._chip_expansion != 1.0:
                    bbox_width = int( bbox_width * self._chip_expansion )
                    bbox_height = int( bbox_height * self._chip_expansion )

                    bbox_min_x = int( ( bbox_min_x + bbox_max_x ) / 2 - bbox_width / 2 )
                    bbox_min_y = int( ( bbox_min_y + bbox_max_y ) / 2 - bbox_height / 2 )
                    bbox_max_x = bbox_min_x + bbox_width
                    bbox_max_y = bbox_min_y + bbox_height

                bbox_area = bbox_width * bbox_height

                if self._area_lower_bound > 0 and bbox_area < self._area_lower_bound:
                    continue
                if self._area_upper_bound > 0 and bbox_area > self._area_upper_bound:
                    continue

                if self._reduce_category and gt.type() and \
                  gt.type().get_most_likely_class() == self._reduce_category and \
                  random.uniform( 0, 1 ) < 0.90:
                    continue

                if self._border_exclude > 0:
                    if bbox_min_x <= self._border_exclude:
                        continue
                    if bbox_min_y <= self._border_exclude:
                        continue
                    if bbox_max_x >= img_max_x - self._border_exclude:
                        continue
                    if bbox_max_y >= img_max_y - self._border_exclude:
                        continue

                crop = safe_crop( img, bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y )

                if crop.shape[0] < 4 or crop.shape[1] < 4:
                    continue

                self._sample_count = self._sample_count + 1
                crop_str = ( '%09d' %  self._sample_count ) + self._chip_extension
                new_file = os.path.join( self._chip_directory, crop_str )
                cv2.imwrite( new_file, crop )

                # Set new box size for this detection
                gt.bounding_box = BoundingBoxD( 0, 0, np.shape( crop )[1], np.shape( crop )[0] )
                new_set = DetectedObjectSet()
                new_set.add( gt )

                output_files.append( new_file )
                output_dets.append( new_set )

            neg_count = 0

            for j, det in enumerate( detections ):

                if max( overlaps[j] ) >= self._max_overlap_for_negative:
                    continue

                bbox = det.bounding_box

                bbox_min_x = int( bbox.min_x() )
                bbox_max_x = int( bbox.max_x() )
                bbox_min_y = int( bbox.min_y() )
                bbox_max_y = int( bbox.max_y() )

                bbox_width = bbox_max_x - bbox_min_x
                bbox_height = bbox_max_y - bbox_min_y

                bbox_area = bbox_width * bbox_height

                if self._chip_method == "fixed_width" or self._chip_method == "native_square":
                    if self._chip_method == "fixed_width":
                        chip_width = int( self._chip_width )
                        chip_height = int( self._chip_height )
                    else:
                        chip_width = max( bbox_width, bbox_height )
                        chip_height = chip_width
                    half_width = int( chip_width / 2 )
                    half_height = int( chip_height / 2 )

                    bbox_min_x = int( ( bbox_min_x + bbox_max_x ) / 2 ) - half_width
                    bbox_min_y = int( ( bbox_min_y + bbox_max_y ) / 2 ) - half_height
                    bbox_max_x = bbox_min_x + chip_width
                    bbox_max_y = bbox_min_y + chip_height

                    bbox_width = chip_width
                    bbox_height = chip_height

                if self._chip_expansion != 1.0:
                    bbox_width = int( bbox_width * self._chip_expansion )
                    bbox_height = int( bbox_height * self._chip_expansion )

                    bbox_min_x = int( ( bbox_min_x + bbox_max_x ) / 2 - bbox_width / 2 )
                    bbox_min_y = int( ( bbox_min_y + bbox_max_y ) / 2 - bbox_height / 2 )
                    bbox_max_x = bbox_min_x + bbox_width
                    bbox_max_y = bbox_min_y + bbox_height

                if self._area_lower_bound > 0 and bbox_area < self._area_lower_bound:
                    continue
                if self._area_upper_bound > 0 and bbox_area > self._area_upper_bound:
                    continue

                if self._border_exclude > 0:
                    if bbox_min_x <= self._border_exclude:
                        continue
                    if bbox_min_y <= self._border_exclude:
                        continue
                    if bbox_max_x >= img_max_x - self._border_exclude:
                        continue
                    if bbox_max_y >= img_max_y - self._border_exclude:
                        continue

                # Handle random factor
                if self._max_neg_per_frame < 1.0 and random.uniform( 0, 1 ) >= self._max_neg_per_frame:
                    continue

                crop = safe_crop( img, bbox_min_x, bbox_min_y, bbox_max_x, bbox_max_y )

                if crop.shape[0] < 4 or crop.shape[1] < 4:
                    continue

                self._sample_count = self._sample_count + 1
                crop_str = ( '%09d' %  self._sample_count ) + self._chip_extension
                new_file = os.path.join( self._chip_directory, crop_str )
                cv2.imwrite( new_file, crop )

                # Set new box size for this detection
                det.bounding_box = BoundingBoxD( 0, 0, np.shape( crop )[1], np.shape( crop )[0] )
                det.type = DetectedObjectType( self._negative_category, 1.0 )
                new_set = DetectedObjectSet()
                new_set.add( det )

                output_files.append( new_file )
                output_dets.append( new_set )

                # Check maximum negative count
                neg_count = neg_count + 1
                if self._max_neg_per_frame >= 1.0 and neg_count > self._max_neg_per_frame:
                    break

        return [ output_files, output_dets ]

    def add_data_from_disk( self, categories, train_files, train_dets, test_files, test_dets ):
        print('[KWCocoTrainDetector] add_data_from_disk')
        print("Number of selected test files : ", len(test_files))

        if self._no_format:
            return
        if len( train_files ) != len( train_dets ):
            print( "Error: train file and groundtruth count mismatch" )
            return
        if categories is not None:
            if self._detector_model and not categories.has_class_name( self._negative_category ):
                categories.add_class( self._negative_category, "", -1 )
            self._categories = categories.all_class_names()
        if self._mode == "detection_refiner":
            [ train_files, train_dets ] = self.extract_chips_for_dets( train_files, train_dets )
            [ test_files, test_dets ] = self.extract_chips_for_dets( test_files, test_dets )
        for i in range( len( train_files ) + len( test_files ) ):
            if i < len( train_files ):
                filename = train_files[ i ]
                groundtruth, use_frame = self.filter_truth( train_dets[ i ], categories )
                if use_frame:
                    self._training_writer.write_set( groundtruth, os.path.abspath( filename ) )
            else:
                filename = test_files[ i - len( train_files ) ]
                groundtruth, use_frame = self.filter_truth( test_dets[ i - len( train_files ) ], categories )
                if use_frame:
                    self._validation_writer.write_set( groundtruth, os.path.abspath( filename ) )
