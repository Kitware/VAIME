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

from kwiver.vital.algo import (
    DetectedObjectSetOutput,
    ImageObjectDetector,
    TrainDetector
)

# from distutils.util import strtobool

# import numpy as np
# import torch
import os
import shutil
import signal
import sys
import subprocess
import threading
import time
# import math

from .netharn_utils import recurse_copy
from .kwcoco_train_detector import KWCocoTrainDetector
from .kwcoco_train_detector import KWCocoTrainDetectorConfig
from ._utils import vital_config_update

import scriptconfig as scfg
import ubelt as ub


class MITYoloConfig(KWCocoTrainDetectorConfig):
    """
    The configuration for :class:`MITYoloTrainer`.
    """
    identifier = "viame-mit-yolo-detector"
    train_directory = "deep_training"
    output_directory = "category_models"
    seed_model = ""
    gpu_count = -1
    tmp_training_file = "training_truth.json"
    tmp_validation_file = "validation_truth.json"
    device = scfg.Value("cuda", help=ub.paragraph(
        '''
        The device to run SAM2 prediction on.
        '''))
    out_path = scfg.Value('allow', help=ub.paragraph(
        '''
        Where to save results
        '''))

    categories = []

    max_epochs = scfg.Value(500, help='Maximum number of epochs to train for')
    batch_size = scfg.Value(4, help='Number of chips per batch.')
    learning_rate = scfg.Value(3e-4, help='Learning rate for gradient update steps.')

    pipeline_template = ""

    def __post_init__(self):
        super().__post_init__()


class MITYoloTrainer( KWCocoTrainDetector ):
    """
    Implementation of TrainDetector class
    """
    def __init__( self ):
        TrainDetector.__init__( self )
        self._config = MITYoloConfig()

    def get_configuration(self):
        # Inherit from the base class
        print('[MITYoloTrainer] get_configuration')
        cfg = super().get_configuration()
        for key, value in self._config.items():
            cfg.set_value(key, str(value))
        return cfg

    def set_configuration(self, cfg_in):
        print('[MITYoloTrainer] set_configuration')
        cfg = self.get_configuration()
        vital_config_update(cfg, cfg_in)
        for key in self._config.keys():
            self._config[key] = str(cfg.get_value(key))
        self._config.__post_init__()

        # Hack in the previous style configuration as class variables prefixed
        # with an underscore. Ideally we would just access these via the config
        # object as a single source of truth
        for key, value in self._config.items():
            setattr(self, "_" + key, value)

        self._post_config_set()
        return True

    def _post_config_set(self):
        print('[MITYoloTrainer] _post_config_set')
        assert self._config['mode'] == "detector"

        # Make required directories and file streams
        if self._train_directory is not None:
            if not os.path.exists( self._train_directory ):
                os.mkdir( self._train_directory )
            self._training_file = os.path.join(
                self._train_directory, self._tmp_training_file )
            self._validation_file = os.path.join(
                self._train_directory, self._tmp_validation_file )
            self._chip_directory = os.path.join(
                self._train_directory, "image_chips" )
        else:
            self._training_file = self._tmp_training_file
            self._validation_file = self._tmp_validation_file

        if self._output_directory is not None:
            if not os.path.exists( self._output_directory ):
                os.mkdir( self._output_directory )

        from kwiver.vital.modules import load_known_modules
        load_known_modules()

        if not self._no_format:
            self._training_writer = DetectedObjectSetOutput.create( "coco" )
            self._validation_writer = DetectedObjectSetOutput.create( "coco" )

            writer_conf = self._training_writer.get_configuration()
            # writer_conf.set_value( "aux_image_labels", self._aux_image_labels )
            # writer_conf.set_value( "aux_image_extensions", self._aux_image_extensions )
            self._training_writer.set_configuration( writer_conf )

            writer_conf = self._validation_writer.get_configuration()
            # writer_conf.set_value( "aux_image_labels", self._aux_image_labels )
            # writer_conf.set_value( "aux_image_extensions", self._aux_image_extensions )
            self._validation_writer.set_configuration( writer_conf )

            self._training_writer.open( self._training_file )
            self._validation_writer.open( self._validation_file )

        if self._mode == "detection_refiner" and not os.path.exists( self._chip_directory ):
            os.mkdir( self._chip_directory )

        # Load object detector if enabled
        if self._detector_model:
            self._detector = ImageObjectDetector.create( "yolo" )
            detector_config = self._detector.get_configuration()
            detector_config.set_value( "deployed", self._detector_model )
            if not self._detector.set_configuration( detector_config ):
                print( "Unable to configure detector" )
                return False

        # QUESTION: Do we need to handle "scale type file"?

        # Other misc setting adjustments
        if self._chip_extension and self._chip_extension[0] != '.':
            self._chip_extension = '.' + self._chip_extension

        if int( self._chip_height ) <= 0:
            self._chip_height = self._chip_width
        if int( self._chip_width ) <= 0:
            self._chip_width = self._chip_height

        # Initialize persistent variables
        self._training_data = []
        self._validation_data = []
        self._sample_count = 0

    def _ensure_format_writers(self):
        if not self._no_format:
            self._training_writer.complete()
            self._validation_writer.complete()

            # hack, need to fixup the writers
            import kwcoco
            paths_to_fix = [self._training_file, self._validation_file]
            for fpath in paths_to_fix:
                fpath = ub.Path(fpath)
                if fpath.exists():
                    dset = kwcoco.CocoDataset(fpath)
                    dset.conform()
                    dset.dump()

    def check_configuration( self, cfg ):
        if not cfg.has_value( "identifier" ) or len( cfg.get_value( "identifier") ) == 0:
            print( "A model identifier must be specified!" )
            return False
        return True

    def update_model( self ):
        self._ensure_format_writers()

        # We may be forced to write to the config directory where the code
        # lives due to hydra. It would be nice to find a way around this.
        import yolo.config
        import json
        # yolo_modpath = ub.Path(yolo.__file__).parent

        config_dpath = (ub.Path(yolo.config.__file__).parent / 'dataset')

        # Prepare the dataset config for hydra
        dataset_config = {}
        dataset_config['path'] = os.fspath('.')
        dataset_config['train'] = os.fspath(self._training_file)
        # FIXME: not sure why validation file not written
        if self._validation_file:
            dataset_config['validation'] = os.fspath(self._validation_file)
        else:
            dataset_config['validation'] = None
        dataset_config['class_list'] = self._categories
        dataset_config['class_num'] = len(self._categories)
        cfgid = ub.hash_data(dataset_config, base='hex')[0:16]
        dataset_config_name = f'dataset_config_{cfgid}'
        dataset_config_fpath = config_dpath / f'{dataset_config_name}.yaml'
        dataset_config_fpath.write_text(json.dumps(dataset_config))

        cmd = [ "python.exe" if os.name == 'nt' else "python", "-m" ]

        self._accelerator = 'auto'
        cmd += [
            "yolo.lazy",
            "task=train",
            "use_wandb=False",
            "cpu_num=4",
            f"name={self._identifier}",
            f"dataset={dataset_config_name}",
            f"out_path={self._train_directory}",
            f"accelerator={self._accelerator}",
            f"task.data.batch_size={self._batch_size}",
            f"task.optimizer.args.lr={self._learning_rate}",
            f"task.epoch={self._max_epochs}",
        ]

        self.proc = subprocess.Popen( cmd )
        self.proc.wait()

        if len( self._seed_model ) > 0:
            cmd.append( 'weight="{self._seed_model}"' )

        if threading.current_thread().__class__.__name__ == '_MainThread':
            signal.signal( signal.SIGINT, lambda signal, frame: self.interupt_handler() )
            signal.signal( signal.SIGTERM, lambda signal, frame: self.interupt_handler() )

        self.proc = subprocess.Popen( cmd )
        self.proc.wait()

        self.save_final_model()

        print( "\nModel training complete!\n" )

    def interupt_handler( self ):
        self.proc.send_signal( signal.SIGINT )
        timeout = 0
        while self.proc.poll() is None:
            time.sleep( 0.1 )
            timeout += 0.1
            if timeout > 5:
                self.proc.kill()
                break
        self.save_final_model()
        sys.exit( 0 )

    def save_final_model( self ):
        if len( self._pipeline_template ) > 0:

            # Copy model file to final directory
            output_model_name = "trained_mit_yolo_checkpoint.ckpt"

            train_dpath = ub.Path(self._train_directory)
            output_dpath = ub.Path(self._output_directory)
            checkpoint_dpath = train_dpath / 'train' / self._identifier / 'checkpoints'
            candiate_checkpoints = sorted(checkpoint_dpath.glob('*'))
            if len(candiate_checkpoints) == 0:
                raise Exception('no checkpoints found')
            final_ckpt_fpath = candiate_checkpoints[-1]

            output_model = output_dpath / output_model_name

            if not final_ckpt_fpath.exists():
                print( "\nModel failed to finsh training\n" )
                sys.exit( 0 )

            final_ckpt_fpath.copy( output_model )

            # Copy pipeline file
            fin = open( self._pipeline_template )
            fout = open( self._output_directory / "detector.pipe", 'w' )
            all_lines = []
            for s in list( fin ):
                all_lines.append( s )
            for i, line in enumerate( all_lines ):
                line = line.replace( "[-MODEL-FILE-]", output_model_name )
                all_lines[i] = line.replace( "[-WINDOW-OPTION-]", self._resize_option )
            for s in all_lines:
                fout.write( s )
            fout.close()
            fin.close()

            # Output additional completion text
            print( "\nWrote finalized model to " + output_model )

            print( "\nThe " + self._train_directory + " directory can now be deleted, "
                   "unless you want to review training metrics or generated plots in "
                   "there first." )


def __vital_algorithm_register__():
    from kwiver.vital.algo import algorithm_factory

    # Register Algorithm
    implementation_name = "mit_yolo"

    if algorithm_factory.has_algorithm_impl_name( MITYoloTrainer.static_type_name(), implementation_name ):
        return

    algorithm_factory.add_algorithm( implementation_name, "PyTorch MIT YOLO detection training routine", MITYoloTrainer )

    algorithm_factory.mark_algorithm_as_loaded( implementation_name )
