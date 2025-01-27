#ckwg +28
# Copyright 2015 by Kitware, Inc.
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
from __future__ import print_function
from kwiver.sprokit.processes.kwiver_process import KwiverProcess
from pathlib import Path

import zipfile
import json
import ast
import sys

class OnnxConverter(KwiverProcess):
    """
    This process convert a yolo-darknet/crcnn-mmdet model to onnx in the
    config step.
    """
    # ----------------------------------------------
    def __init__(self, conf):
        KwiverProcess.__init__(self, conf)

        self.declare_configuration_key("model_path", "", "Path to the trained model: .zip if mmdet, .weights if darknet")
        self.declare_configuration_key("batch_size", "", "batch size")
        self.declare_configuration_key("onnx_model_prefix", "", "Output onnx model path prefix")

    # ----------------------------------------------
    def _configure(self):

        # Get config parameters
        model_path = self.config_value("model_path")
        batch_size = int(self.config_value("batch_size"))
        onnx_model_prefix = self.config_value("onnx_model_prefix")

        # Do conversion of the model
        if (model_path.endswith(".weights")):
            from darknet2onnx.export import export_darknet_to_onnx
            from darknet2onnx.darknet2pytorch.model import Darknet

            weights_file = Path(model_path)
            cfg_file = weights_file.with_suffix(".cfg")
            onnx_file = Path(onnx_model_prefix).with_suffix(".onnx")

            model = Darknet(cfg_file)
            model.load_weights(weights_file)
            export_darknet_to_onnx(model, batch_size, onnx_filepath=onnx_file)

            print(f"The generated onnx model was written to: {onnx_file}")

        elif (model_path.endswith(".zip")):
            net_shape = ()
            with zipfile.ZipFile(model_path, 'r') as zip_ref:
                all_files_in_zip = zip_ref.namelist()
                train_info_files = [file for file in all_files_in_zip if file.endswith("train_info.json")]
                if len(train_info_files) > 1:
                    print("The model zip file must contain one and only one train_info.zip", file=sys.stderr)
                    sys.exit(1)
                with zip_ref.open(train_info_files[0]) as file:
                    content = file.read()
                    json_content = json.loads(content.decode('utf-8'))
                    config = ast.literal_eval(json_content["extra"]["config"])
                    net_shape = (config['window_dims'][0], config['window_dims'][1], 3)

            from viame.arrows.pytorch.crcnn2onnx import crcnn2onnx
            crcnn2onnx(model_path, net_shape, batch_size, onnx_model_prefix)
            print(f'The generated onnx model was written to: {onnx_model_prefix}.onnx')

        else:
            print("No model will be generated, for now, we only support yolo-darknet and crcnn-mmdet")

        self._base_configure()

    # ----------------------------------------------
    def _step(self):
        self._base_step()

# ==================================================================
def __sprokit_register__():

    from kwiver.sprokit.pipeline import process_factory

    module_name = 'python:viame.pytorch.OnnxConverter'

    if process_factory.is_process_module_loaded(module_name):
        return

    process_factory.add_process('OnnxConverter', 'Convert a yolo/cfrcnn model to onnx', OnnxConverter)

    process_factory.mark_process_module_as_loaded(module_name)

