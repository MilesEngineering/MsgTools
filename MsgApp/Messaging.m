% ideas taken from:
% http://www.mathworks.com/help/techdoc/ref/meta.class.html
% http://www.mathworks.com/help/techdoc/matlab_oop/br8du8u.html

classdef Messaging
    properties
        msgClassnameFromID;
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
            obj.msgClassnameFromID = containers.Map(uint32(0),'classname');
            obj.msgClassnameFromID.remove(uint32(0));
            obj.msgSizeFromID = containers.Map(uint32(0),metaclass(msgdir));
            obj.msgSizeFromID.remove(uint32(0));
            addpath(Messaging.AbsPath(msgdir));
            obj.ProcessDir(msgdir, msgdir);
        end
        function ProcessDir(obj, basedir, dirname)
            fprintf('Processing %s\n', dirname);

            % loop over filenames in dir
            filenames = dir(strcat(dirname,'/*.m'));
            for f = 1:numel(filenames)
                [~, classname,~] = fileparts(filenames(f).name);
                subdir = strrep(dirname, basedir, '');
                classname = strcat(strrep(strrep(subdir, '/', '.'), '+', ''), '.', classname);
                % if classname starts with ., remove it
                if ~isempty(classname) && classname(1) == '.'
                    classname = classname(2:end);
                end
                %fprintf('class %s\n', classname);
                mc = meta.class.fromName(classname);
                if ~isempty(mc)
                    idIdx = strcmp({mc.PropertyList.Name}, 'MSG_ID')==1;
                    if any(idIdx)
                        id = mc.PropertyList(idIdx).DefaultValue;
                        if id > 0
                            fprintf('class %s, ID %d=0x%s\n', classname, id, dec2hex(id));
                            sizeIdx = strcmp({mc.PropertyList.Name}, 'MSG_SIZE')==1;
                            size = mc.PropertyList(sizeIdx).DefaultValue;
                            obj.msgClassnameFromID(id) = classname;
                            obj.msgSizeFromID(id) = size;
                        else
                            fprintf('ignoring class %s, invalid ID %d\n', classname, id);
                        end
                    else
                        fprintf('ignoring class %s, no ID\n', classname);
                    end
                    %for p = 1:numel(mc.PropertyList)
                    %    if mc.PropertyList(p).HasDefault
                    %        fprintf('%s = %d\n', mc.PropertyList(p).Name, mc.PropertyList(p).DefaultValue);
                    %    end
                    %end
                end
            end

            % Get a list of all files and folders in this folder.
            d = dir(dirname);
            isub = [d(:).isdir]; % returns logical vector
            subFolders = {d(isub).name}';
            subFolders(ismember(subFolders,{'.','..'})) = [];
            % Print folder names to command window.
            for k = 1 : length(subFolders)
                obj.ProcessDir(basedir, char(strcat(dirname,'/',subFolders(k))));
            end
        end
        % http://stackoverflow.com/questions/7102828/instantiate-class-from-name-in-matlab
        function ret = ConstructMsg(obj, msgid, inputMsgBuffer)
            if(nargin < 3)
                inputMsgBuffer = [];
            end
            myClassname = obj.msgClassnameFromID(msgid);
            % fprintf('myClass is %s\n', myClassname);
            ctorMethodName = myClassname; %findobj(myClass.MethodList, 'Access','public', 'Name',myClass.Name);

            % get number of contructor arguments
            %numArgs = numel(ctorMethod.InputNames);

            % create object
            try
                if(nargin < 3)
                    ret = feval(ctorMethodName);
                else
                    ret = feval(ctorMethodName,inputMsgBuffer);
                end
            catch ME
                warning(ME.identifier, ME.message)
                ret = [];
            end
        end
    end

end