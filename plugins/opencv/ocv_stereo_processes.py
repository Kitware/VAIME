# -*- coding: utf-8 -*-
#ckwg +28
# Copyright 2017 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  * Neither name of Kitware, Inc. nor the names of any contributors may be used
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
Ignore:
    workon_py2
    source ~/code/VIAME/build/install/setup_viame.sh
    cd ~/code/VIAME/plugins/opencv

    feat1 = vital.types.Feature(loc=(10, 1))
    feat2 = vital.types.Feature(loc=(2, 3))

    np.sum((feat1.location - feat2.location) ** 2)

CommandLine:
    # OPENCV 3.X VERSION
    cd ~/code/VIAME/plugins/opencv/python
    export PYTHONPATH=$(pwd):$PYTHONPATH

    workon_py2
    cd ~/code/VIAME/build-cv3-py2

    export KWIVER_PLUGIN_PATH=""
    export SPROKIT_MODULE_PATH=""
    source install/setup_viame.sh

    export KWIVER_DEFAULT_LOG_LEVEL=debug
    export KWIVER_DEFAULT_LOG_LEVEL=info
    export KWIVER_PYTHON_DEFAULT_LOG_LEVEL=info
    export SPROKIT_PYTHON_MODULES=kwiver.processes:viame.processes

    python ~/code/VIAME/plugins/opencv/python/run_opencv.py
    python run_opencv.py

    ~/code/VIAME/build/install/bin/kwiver runner ~/.cache/sprokit/temp_pipelines/temp_pipeline_file.pipe
    ~/code/VIAME/build/install/bin/kwiver runner opencv.pipe -S pythread_per_process

CommandLine:
    # OPENCV 2.4 VERSION
    cd ~/code/VIAME/plugins/opencv/python
    export PYTHONPATH=$(pwd):$PYTHONPATH

    workon_py2
    cd ~/code/VIAME/build

    export KWIVER_PLUGIN_PATH=""
    export SPROKIT_MODULE_PATH=""
    source ~/code/VIAME/build/install/setup_viame.sh
    export KWIVER_DEFAULT_LOG_LEVEL=debug
    export KWIVER_DEFAULT_LOG_LEVEL=info
    export KWIVER_PYTHON_DEFAULT_LOG_LEVEL=info
    export SPROKIT_PYTHON_MODULES=kwiver.processes:viame.processes

    # export KWIVER_PYTHON_COLOREDLOGS=1

    python ~/code/VIAME/plugins/opencv/python/run_opencv.py
    python run_opencv.py

    ~/code/VIAME/build/install/bin/kwiver runner ~/.cache/sprokit/temp_pipelines/temp_pipeline_file.pipe  -S pythread_per_process
    ~/code/VIAME/build/install/bin/kwiver runner opencv.pipe -S pythread_per_process

SeeAlso
    ~/code/VIAME/packages/kwiver/vital/bindings/python/vital/types
"""
from __future__ import absolute_import, print_function, division

import numpy as np

from kwiver.vital.types import (
    BoundingBoxD,
    DetectedObject,
    DetectedObjectSet,
    DetectedObjectType,
    ImageContainer,
    Point2d,
)

from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from kwiver.sprokit.pipeline import process
from kwiver.sprokit.pipeline import datum  # NOQA

import ubelt as ub
import os
import itertools as it

from . import ocv_stereo_algos as ctalgo

from kwiver.vital import vital_logging

logger = vital_logging.getLogger(__name__)
print = logger.info


# TODO: add something similar in sprokit proper
TMP_SPROKIT_PROCESS_REGISTRY = []


def tmp_sprokit_register_process(name=None, doc=''):
    def _wrp(cls):
        name_ = name
        if name is None:
            name_ = cls.__name__
        TMP_SPROKIT_PROCESS_REGISTRY.append((name_, doc, cls))
        return cls
    return _wrp


def opencv_setup_config(self, default_params):
    if isinstance(default_params, dict):
        default_params = list(it.chain(*default_params.values()))
    for pi in default_params:
        self.add_config_trait(pi.name, pi.name, str(pi.default), pi.doc)
        self.declare_config_using_trait(pi.name)


def tmp_smart_cast_config(self):
    # import ubelt as ub
    # import utool as ut
    config = {}
    keys = [k for k in list(self.available_config())
            if not k.startswith('_')]
    for key in keys:
        strval = self.config_value(key)
        # print('strval = {!r}'.format(strval))
        try:
            val = eval(strval, {}, {})
        except Exception:
            val = strval
        config[key] = val
    return config


@tmp_sprokit_register_process(name='gmm_motion_detector',
                              doc='preliminatry fish detection')
class GMMDetectFishProcess(KwiverProcess):
    """
    This process gets an image and detection_set as input, extracts each chip,
    does postprocessing and then sends the extracted chip to the output port.

    """
    # --------------------------------------------------------------------------
    def __init__(self, conf):
        print('conf = {!r}'.format(conf))
        logger.debug(' ----- init ' + self.__class__.__name__)
        KwiverProcess.__init__(self, conf)

        opencv_setup_config(self, ctalgo.GMMForegroundObjectDetector.default_params())

        # set up required flags
        optional = process.PortFlags()
        required = process.PortFlags()
        required.add(self.flag_required)

        #  declare our input port ( port-name,flags)
        self.declare_input_port_using_trait('image', required)

        self.declare_output_port_using_trait('detected_object_set', optional )

    # --------------------------------------------------------------------------
    def _configure(self):
        logger.debug(' ----- configure ' + self.__class__.__name__)
        config = tmp_smart_cast_config(self)
        print('detector config = {}'.format(ub.repr2(config, nl=2)))
        self.detector = ctalgo.GMMForegroundObjectDetector(**config)
        self._base_configure()

    # --------------------------------------------------------------------------
    def _dowork(self, img_container):
        """
        Helper to decouple the algorithm and pipeline logic

        CommandLine:
            xdoctest viame.processes.opencv.processes GMMDetectFishProcess._dowork

        Example:
            >>> from viame.processes.opencv.processes import *
            >>> from kwiver.vital.types import ImageContainer
            >>> import kwiver.sprokit.pipeline.config
            >>> # construct dummy process instance
            >>> conf = kwiver.sprokit.pipeline.config.empty_config()
            >>> self = GMMDetectFishProcess(conf)
            >>> self._configure()
            >>> # construct test data
            >>> from vital.util import VitalPIL
            >>> from PIL import Image as PILImage
            >>> pil_img = PILImage.open(ub.grabdata('https://i.imgur.com/Jno2da3.png'))
            >>> pil_img = PILImage.fromarray(np.zeros((512, 512, 3), dtype=np.uint8))
            >>> img_container = ImageContainer(VitalPIL.from_pil(pil_img))
            >>> # Initialize the background detector by sending 10 black frames
            >>> for i in range(10):
            >>>     empty_set = self._dowork(img_container)
            >>> # now add a white box that should be detected
            >>> np_img = np.zeros((512, 512, 3), dtype=np.uint8)
            >>> np_img[300:340, 220:380] = 255
            >>> img_container = ImageContainer.fromarray(np_img)
            >>> detection_set = self._dowork(img_container)
            >>> assert len(detection_set) == 1
            >>> obj = detection_set[0]
        """
        # This should be read as np.uint8
        np_img = img_container.asarray()

        detection_set = DetectedObjectSet()
        ct_detections = self.detector.detect(np_img)

        for detection in ct_detections:
            bbox = BoundingBoxD(*detection.bbox.coords)
            mask = detection.mask.astype(np.uint8)
            vital_mask = ImageContainer.fromarray(mask)
            dot = DetectedObjectType("Motion", 1.0)
            obj = DetectedObject(bbox, 1.0, dot, mask=vital_mask)
            detection_set.add(obj)
        return detection_set

    def _step(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' step')
        # grab image container from port using traits
        img_container = self.grab_input_using_trait('image')

        # Process image container
        detection_set = self._dowork(img_container)

        # Push the output
        self.push_to_port_using_trait('detected_object_set', detection_set)

        self._base_step()


@tmp_sprokit_register_process(name='measure_using_stereo',
                              doc='preliminatry length measurement process')
class MeasureProcess(KwiverProcess):
    """
    This process gets an image and detection_set as input, extracts each chip,
    does postprocessing and then sends the extracted chip to the output port.
    """
    # --------------------------------------------------------------------------
    def __init__(self, conf):
        logger.debug(' ----- ' + self.__class__.__name__ + ' init')

        KwiverProcess.__init__(self, conf)

        opencv_setup_config(self, ctalgo.StereoLengthMeasurments.default_params())

        self.add_config_trait('measurement_file', 'measurement_file', '',
                              'output file to write detection measurements')
        self.declare_config_using_trait('measurement_file')
        self.add_config_trait('calibration_file', 'calibration_file', 'cal_201608.mat',
                              'matlab or npz file with calibration info')
        self.declare_config_using_trait('calibration_file')

        required = process.PortFlags()
        required.add(self.flag_required)

        self.add_port_trait('detected_object_set1',
          'detected_object_set',
          'Detections from camera1')
        self.add_port_trait('detected_object_set2',
          'detected_object_set',
          'Detections from camera2')

        #  declare our input ports ( port-name,flags )
        self.declare_input_port_using_trait('detected_object_set1', required)
        self.declare_input_port_using_trait('detected_object_set2', required)

        #  declare our output ports ( port-name,flags )
        self.declare_output_port_using_trait('detected_object_set1', required)
        self.declare_output_port_using_trait('detected_object_set2', required)

    # --------------------------------------------------------------------------
    def _configure(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' configure')
        config = tmp_smart_cast_config(self)

        logger.info('triangulator config = {}'.format(ub.repr2(config, nl=2)))
        self.measurement_file = config.pop('measurement_file')
        self.calibration_file = config.pop('calibration_file')
        self.triangulator = ctalgo.StereoLengthMeasurments(**config)

        # Load camera calibration data here.
        if not os.path.exists(self.calibration_file):
            raise KeyError('must specify a valid camera calibration path')

        self.cal = ctalgo.StereoCalibration.from_file(self.calibration_file)
        logger.info('self.cal = {!r}'.format(self.cal))

        self.headers = ['current_frame', 'fishlen', 'range', 'error', 'dz',
                        'box_pts1', 'box_pts2']

        if self.measurement_file:
            self.output_file = open(self.measurement_file, 'w')
            self.output_file.write(','.join(self.headers) + '\n')
            self.output_file.close()

            self.output_file = open(self.measurement_file, 'a')

        self._base_configure()

        self.prog = ub.ProgIter(verbose=3)
        self.prog.begin()

        self.frame_id = 0

    # --------------------------------------------------------------------------
    def _step(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' step')
        self.prog.step()

        if self.cal is None:
            self.cal = True
            logger.debug(' ----- ' + self.__class__.__name__ + ' grab cam1')
            # grab camera only if we dont have one yet
            camera1 = self.grab_input_using_trait('camera' + '1')
            logger.debug(' ----- ' + self.__class__.__name__ + ' grab cam2')
            camera2 = self.grab_input_using_trait('camera' + '2')

            def _cal_from_vital(vital_camera):
                vci = vital_camera.intrinsics
                cam_dict = {
                    'extrinsic': {
                        'om': vital_camera.rotation.rodrigues().ravel(),
                        'T': vital_camera.translation.ravel(),
                    },
                    'intrinsic': {
                        'cc': vci.principle_point.ravel(),
                        'fc': [vci.focal_length,
                               vci.focal_length / vci.aspect_ratio],
                        'alpha_c': vci.skew,
                        'kc': vci.dist_coeffs.ravel(),
                    }
                }
                return cam_dict

            logger.debug(' ----- ' + self.__class__.__name__ + ' parse cameras')
            self.cal = ctalgo.StereoCalibration({
                'left': _cal_from_vital(camera1),
                'right': _cal_from_vital(camera2),
            })
            logger.debug(' ----- ' + self.__class__.__name__ + ' no more need for cameras')

        detection_set1 = self.grab_input_using_trait('detected_object_set' + '1')
        detection_set2 = self.grab_input_using_trait('detected_object_set' + '2')

        # Convert back to the format the algorithm understands
        def _detections_from_vital(detection_set):
            for vital_det in detection_set:
                bbox = vital_det.bounding_box
                coords = [bbox.min_x(), bbox.min_y(),
                          bbox.max_x(), bbox.max_y()]
                if vital_det.mask:
                    mask = vital_det.mask.asarray()
                else:
                    mask = None
                ct_bbox = ctalgo.BoundingBox(coords)

                # TODO: to measure distances between special keypoint
                # detections add an additional argument to DetectedObject
                # >>> special_keypoints = {
                # ...    'head': [x1, y1],
                # ...    'tail': [x2, y2],
                # ... }
                # >>> ct_det = ctalgo.DetectedObject(
                # ...     ct_bbox, mask, special_keypoints=special_keypoints)
                ct_det = ctalgo.DetectedObject(ct_bbox, mask)
                yield ct_det

        detections1 = list(_detections_from_vital(detection_set1))
        detections2 = list(_detections_from_vital(detection_set2))

        assignment, assign_data, cand_errors = self.triangulator.find_matches(
            self.cal, detections1, detections2)

        logger.debug(' ----- ' + self.__class__.__name__ + ' found {} matches'.format(len(assign_data)))

        # Append assignments to the measurements
        if self.measurement_file:
            def csv_repr(d):
                if isinstance(d, np.ndarray):
                    d = d.tolist()
                s = repr(d)
                return s.replace('\n', '').replace(',', ';').replace(' ', '')

            for data in assign_data:
                data['current_frame'] = self.frame_id
                self.frame_id = self.frame_id + 1
                line = ','.join([csv_repr(d) for d in ub.take(data, self.headers)])
                self.output_file.write(line + '\n')

            if assign_data:
                 self.output_file.flush()

        # Create output detection vectors
        output1 = [d for d in detection_set1]
        output2 = [d for d in detection_set2]

        # Assign all points to detections for now
        for match in assign_data:
            i1 = match["ij"][0]
            i2 = match["ij"][1]
            output1[i1].set_length(match["fishlen"])
            output2[i2].set_length(match["fishlen"])
            head, tail = detections1[i1].center_keypoints()
            output1[i1].add_keypoint('head', Point2d(head))
            output1[i1].add_keypoint('tail', Point2d(tail))
            head, tail = detections2[i2].center_keypoints()
            output2[i2].add_keypoint('head', Point2d(head))
            output2[i2].add_keypoint('tail', Point2d(tail))

        output1 = DetectedObjectSet(output1)
        output2 = DetectedObjectSet(output2)

        # Push output detections to port
        self.push_to_port_using_trait('detected_object_set1', output1)
        self.push_to_port_using_trait('detected_object_set2', output2)
        self._base_step()

@tmp_sprokit_register_process(name='add_keypoints_from_oriented_bbox',
                              doc='Add keypoints to a detection from a obbox on its mask')
class KeypointProcess(KwiverProcess):
    """
    This process gets an image and detection_set as input, extracts each chip,
    does postprocessing and then sends the extracted chip to the output port.
    """
    # --------------------------------------------------------------------------
    def __init__(self, conf):
        logger.debug(' ----- ' + self.__class__.__name__ + ' init')

        KwiverProcess.__init__(self, conf)

        required = process.PortFlags()
        required.add(self.flag_required)

        #self.add_port_trait('detected_object_set',
        #  'detected_object_set',
        #  'Detections from camera1')

        #  declare our input ports ( port-name,flags )
        self.declare_input_port_using_trait('detected_object_set', required)

        #  declare our output ports ( port-name,flags )
        self.declare_output_port_using_trait('detected_object_set', required)

    # --------------------------------------------------------------------------
    def _configure(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' configure')
        config = tmp_smart_cast_config(self)
        self._base_configure()
        self.prog = ub.ProgIter(verbose=3)
        self.prog.begin()

    # --------------------------------------------------------------------------
    def _step(self):
        logger.debug(' ----- ' + self.__class__.__name__ + ' step')
        self.prog.step()

        detection_set1 = self.grab_input_using_trait('detected_object_set')

        # Convert back to the format the algorithm understands
        def _detections_from_vital(detection_set):
            for vital_det in detection_set:
                bbox = vital_det.bounding_box
                coords = [bbox.min_x(), bbox.min_y(),
                          bbox.max_x(), bbox.max_y()]
                if vital_det.mask:
                    mask = vital_det.mask.asarray()
                else:
                    mask = None
                ct_bbox = ctalgo.BoundingBox(coords)
                ct_det = ctalgo.DetectedObject(ct_bbox, mask)
                yield ct_det

        detections1 = list(_detections_from_vital(detection_set1))

        # Create output detection vectors
        output1 = [d for d in detection_set1]

        # Assign all points to detections for now
        for i in range(len(detection_set1)):
            if not output1[i].mask:
                continue
            head, tail = detections1[i].center_keypoints()
            output1[i].add_keypoint('head', Point2d(head))
            output1[i].add_keypoint('tail', Point2d(tail))

        output1 = DetectedObjectSet(output1)

        # Push output detections to port
        self.push_to_port_using_trait('detected_object_set', output1)
        self._base_step()

def __sprokit_register__():

    from kwiver.sprokit.pipeline import process_factory

    module_name = 'python_' + __name__

    if process_factory.is_process_module_loaded(module_name):
        return

    for name, doc, cls in TMP_SPROKIT_PROCESS_REGISTRY:
        process_factory.add_process(name, doc, cls)

    process_factory.mark_process_module_as_loaded(module_name)
