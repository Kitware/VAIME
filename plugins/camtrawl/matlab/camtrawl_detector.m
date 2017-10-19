%
% Camtrawl object detector
%
% This file is loaded into a matlab instance for execution. Functions are called
% by the algorithm driver to pass images and retrieve detections.
%
% The whole detector is a collection of functions that are called by the main C++
% algorithm implementation. These functions can communicate via GLOBAL variables or
% other means. Global variables are used in this example.
%
% The matlab detector control flow is as follows:
%

% 1) The file specified in the pipeline config is loaded into the
%    Matlab engine. A typical configuration for a matlab detector is
%    as follows.
%
% # ================================================================
% process detector
%  :: image_object_detector
%   :detector:type   matlab
%   :detector:matlab:program_file     example_detector/example_matlab_detector.m
%   # Specify initial config for the detector
%   # The following line is presented to the matlab script as "a=1;"
%   :detector:matlab:config:a_var          1
%   :detector:matlab:config:border         2
%   :detector:matlab:config:saving         false
%

% 2) The config values are set into the Matlab engine.
%

% 3) The "detector_initialize()" function is called to enable the
%    detector to perform ant initialization after the configuration is
%    set.
%

% 4) The "check_configuration()" function is called to verify the
%    configuration. This call is part of the C++ algorithm pattern,
%    but may not have much value in matlab.
%

% 5) The "detect(image)" function is called with an image. This
%    function does the actual image processing and object
%    detection. Refer to the sample detect() function for the output
%    format and protocol.
%

clear all; clc; close all;

global detected_object_set;
global detected_object_classification;
global detected_object_chips;
                                % Set configurable values

global min_aspect
global max_aspect
global min_size
global ROI
global factor
global num_frames
global init_var
