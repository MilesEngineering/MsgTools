% not sure where this functionality should live.
% Creating the library ought to happen once after the code generator creates
% all the .m and .cpp files are generated, and a user wants to use the
% new blocks in simulink.


% Below taken from https://www.goddardconsulting.ca/simulink-creating-custom-libraries.html

function blkStruct = slblocks
% Function to add a specific custom library to the Library Browser

% Author: Phil Goddard (phil@goddardconsulting.ca)

% Define how the custom library is displayed in the Library Browser
Browser.Library = 'customlib'; % Name of the .mdl file
Browser.Name    = 'My Custom Library';
Browser.IsFlat  = 1; % Is this library "flat" (i.e. no subsystems)?

% Define how the custom library is displayed in the older style
% "Blocksets and Toolboxes" view.
blkStruct.Name = ['My Custom' sprintf('\n') 'Library'];
blkStruct.OpenFcn = 'customlib'; % Name of the .mdl file
blkStruct.MaskDisplay = '';

% Output the required structure
blkStruct.Browser = Browser;
