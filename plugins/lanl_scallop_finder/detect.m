% ckwg +29
% Copyright 2016 by Kitware, Inc.
% All rights reserved.
%
% Redistribution and use in source and binary forms, with or without
% modification, are permitted provided that the following conditions are met:
%
%  * Redistributions of source code must retain the above copyright notice,
%    this list of conditions and the following disclaimer.
%
%  * Redistributions in binary form must reproduce the above copyright notice,
%    this list of conditions and the following disclaimer in the documentation
%    and/or other materials provided with the distribution.
%
%  * Neither name of Kitware, Inc. nor the names of any contributors may be used
%    to endorse or promote products derived from this software without specific
%    prior written permission.
%
% THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
% AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
% IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
% ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
% ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
% DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
% SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
% CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
% OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
% OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
%

function detect( in_image )

global detected_object_set;
global detected_object_classification;
global detected_object_chips;

[detected_object_set,detected_object_classification] = ...
ScallopFinder_proc( in_image );
size(detected_object_set)
% This function is called to perform the detection operation on the
% supplied image.

% Need a format for returning the detections.
%
% Data needed to create a detection object:
% - bounding box for detection in pixel coords
% - Confidence value 0.0 - 1.0
% - Optional list of classification names and scores
%
% detected_object = [ ul_x, ul_y, lr_x, lr_y, confidence ]
% detected_object_set = [ detected_object; detected_object; ... ]
%
% for i = mum_detections
  % for j = num_classes-for detections(i)
% detected_object_classification(i,j).name = 'class';
% detected_object_classification(i,j).score = 0.23;
%

  % for example
  % 3 detections on this object
  % Box coordinates are tl-x, tl-y, lr-x, lr-y
%   detected_object_set = [ 100 120 220 220 .56; % box and confidence for detection
%                           550 550 860 860 .77;
%                           900 500 1040 1040 .54];

  % Classification of the detections are optional, but if there are any
  % they must be represented in the following structure.
  % There *must* be the same number of rows in the classification array as there are detections.
  % 2 possible classifications for object 1
%   detected_object_classification(1,1).name='scallop';
%   detected_object_classification(1,1).score=.56;
%   detected_object_classification(1,2).name='rock';
%   detected_object_classification(1,2).score=.3;
% 
%   detected_object_classification(2,1).name='scallop';
%   detected_object_classification(2,1).score=.56;
% 
%   detected_object_classification(3,2).name='rock-lobster';
%   detected_object_classification(3,2).score=.3;
% disp('ran OK');
%   image( in_image );  % TEMP
end
