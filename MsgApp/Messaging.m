% ideas taken from:
% http://www.mathworks.com/help/techdoc/ref/meta.class.html
% http://www.mathworks.com/help/techdoc/matlab_oop/br8du8u.html

classdef Messaging
    properties
        msgClassFromID;
        msgSizeFromID;
    end
    methods (Static)
        function abspath = AbsPath(relpath,debug)
            if(nargin < 2)
                debug = 0;
            end
            [~,b] = fileattrib(relpath);
            abspath = b.Name;
            if(debug)
                fprintf('relpath=%s, abspath=%s\n', relpath, abspath);
            end
        end
        function ret = SwapBytes(newSwapBytes)
            persistent swapBytes;
            if(isempty(swapBytes))
                swapBytes = 1;
            end
            if(nargin > 0)
                swapBytes = newSwapBytes;
            end
            if nargout > 0
                ret = swapBytes;
            end
        end
        function ret = PerhapsSwapBytes(bytes)
            if(Messaging.SwapBytes())
                ret = swapbytes(bytes);
            else
                ret = bytes;
            end
        end
    end
    methods
        function obj = Messaging(msgdir)
            if(nargin == 0)
                msgdir = '../../obj/CodeGenerator/Matlab/';
                fprintf('msgdir: %s\n', msgdir);
            end
            obj.msgClassFromID = containers.Map(uint32(0),metaclass(msgdir));
            obj.msgClassFromID.remove(uint32(0));
            obj.msgSizeFromID = containers.Map(uint32(0),metaclass(msgdir));
            obj.msgSizeFromID.remove(uint32(0));
            obj.ProcessDir(msgdir);
        end
        function ret = ProcessDir(obj, dirname)
            fprintf('Processing %s\n', dirname);
            addpath(Messaging.AbsPath(dirname));

            % loop over filenames in dir
            filenames = dir(strcat(dirname,'/*.m'));
            for f = 1:numel(filenames)
                [~, classname,~] = fileparts(filenames(f).name);
                fprintf('classname = %s\n', classname);
                mc = meta.class.fromName(classname);
                if ~isempty(mc)
                    idIdx = strcmp({mc.PropertyList.Name}, 'MSG_ID')==1;
                    sizeIdx = strcmp({mc.PropertyList.Name}, 'MSG_SIZE')==1;
                    id = mc.PropertyList(idIdx).DefaultValue;
                    size = mc.PropertyList(sizeIdx).DefaultValue;
                    obj.msgClassFromID(id) = mc;
                    obj.msgSizeFromID(id) = size;
                    %for p = 1:numel(mc.PropertyList)
                    %    if mc.PropertyList(p).HasDefault
                    %        fprintf('%s = %d\n', mc.PropertyList(p).Name, mc.PropertyList(p).DefaultValue);
                    %    end
                    %end
                end
            end

            % Get a list of all files and folders in this folder.
            d = dir(dirname);
            isub = [d(:).isdir]; %# returns logical vector
            subFolders = {d(isub).name}';
            subFolders(ismember(subFolders,{'.','..'})) = [];
            % Print folder names to command window.
            for k = 1 : length(subFolders)
                obj.ProcessDir(char(strcat(dirname,'/',subFolders(k))));
            end
        end
        % http://stackoverflow.com/questions/7102828/instantiate-class-from-name-in-matlab
        function ret = ConstructMsg(obj, msgid, inputMsgBuffer)
            if(nargin < 3)
                inputMsgBuffer = [];
            end
            myClass = obj.msgClassFromID(msgid);
            ctorMethod = findobj(myClass.MethodList, 'Access','public', 'Name',myClass.Name);

            % get number of contructor arguments
            %numArgs = numel(ctorMethod.InputNames);

            %# create object
            try
                if(nargin < 3)
                    ret = feval(ctorMethod.Name);
                else
                    ret = feval(ctorMethod.Name,inputMsgBuffer);
                end
            catch ME
                warning(ME.identifier, ME.message)
                ret = [];
            end
        end
    end

end