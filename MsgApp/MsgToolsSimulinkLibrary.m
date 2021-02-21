classdef MsgToolsSimulinkLibrary < handle
    properties
        position = [10 10];
    end
    properties (Constant)
        header_params = ["Destination", "Source"];
        min_x_position = 10;
   end

    methods
        function obj = MsgToolsSimulinkLibrary(simulink_block_library_name, msgdir)
            fprintf("Creating Simulink block library %s\n", simulink_block_library_name);
            if(nargin < 2)
                msgdir = '../../obj/CodeGenerator/Simulink/';
                fprintf('msgdir: %s\n', msgdir);
            end
            
            % create the library
            new_system(simulink_block_library_name, "Library");
            open_system(simulink_block_library_name);

            %execute all the generated matlab files that create simulink blocks!
            addpath(MsgToolsSimulinkLibrary.AbsPath(msgdir));
            obj.ProcessDir(simulink_block_library_name, msgdir, msgdir);

            % save the model
            save_system(simulink_block_library_name);
        end

        function ProcessDir(obj, simulink_block_library_name, basedir, dirname)
            fprintf('Processing %s\n', dirname);

            % loop over filenames in dir
            filenames = dir(strcat(dirname,'/*.m'));
            for f = 1:numel(filenames)
                [~, functionname,~] = fileparts(filenames(f).name);
                subdir = strrep(dirname, basedir, '');
                functionname = strcat(strrep(strrep(subdir, '/', '.'), '+', ''), '.', functionname);
                % if functionname starts with ., remove it
                if ~isempty(functionname) && extract(functionname,1) == '.'
                    functionname = extractAfter(functionname, 1);
                end
                %fprintf('function or class %s\n', functionname);

                filename = filenames(f).name;
                path = fullfile(dirname, filename);
                fprintf("Running %s\n", path)
                [inputblk, outputblk] = feval(functionname, simulink_block_library_name, MsgToolsSimulinkLibrary.header_params);
                set_param(inputblk,'Position',obj.next_position());
                set_param(outputblk,'Position',obj.next_position());
            end

            % Get a list of all files and folders in this folder.
            d = dir(dirname);
            isub = [d(:).isdir]; % returns logical vector
            subFolders = {d(isub).name}';
            subFolders(ismember(subFolders,{'.','..','+headers'})) = [];
            % Print folder names to command window.
            for k = 1 : length(subFolders)
                obj.ProcessDir(simulink_block_library_name, basedir, char(strcat(dirname,'/',subFolders(k))));
            end
        end
        function p = next_position(obj)
            p = [obj.position(1), obj.position(2), obj.position(1)+150, obj.position(2)+150];
            obj.position(1) = obj.position(1) + 175;
            if(obj.position(1) > 600)
                obj.position(1) = obj.min_x_position;
                obj.position(2) = obj.position(2) + 175;
            end
        end
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
    end
end
