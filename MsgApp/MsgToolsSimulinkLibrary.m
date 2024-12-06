classdef MsgToolsSimulinkLibrary < handle
    properties
        position = [10 10];
        header_file_contents = [];
    end
    properties (Constant)
        header_params = ["Destination", "Source"];
        min_x_position = 10;
   end

    methods
        function obj = MsgToolsSimulinkLibrary(simulink_block_library_name, basedir)
            fprintf("Creating Simulink block library %s\n", simulink_block_library_name);
            if(nargin < 2)
                basedir = '../../obj/CodeGenerator';
                fprintf('basedir: %s\n', basedir);
            end
            cdir = basedir + '/C';
            msgdir = basedir + '/Simulink';
            obj.header_file_contents = [
                "#include <stdint.h>"
                "#include ""CFieldAccess.h"""
                "#include ""simulink_message_interface.h"""
            ];
            
            % create the library
            lib = new_system(simulink_block_library_name, "Library");
            open_system(simulink_block_library_name);
            set_param(lib, "SimTargetLang", "C++");
            %set_param(lib, "SimUseLocalCustomCode", "on"); % defaults to 'on'
            %set_param(lib, "SimCustomSourceCode", "");%Simulation Custom Code/Insert custom C code in generated: Source file
            set_param(lib, "SimCustomHeaderCode", '#include "Simulink/msgtools.h"');%Simulation Custom Code/Insert custom C code in generated: Header file
            %set_param(lib, "SimCustomInitializer", "");%Simulation Custom Code/Insert custom C code in generated: Initialize function
            %set_param(lib, "SimCustomTerminator", "");%Simulation Custom Code/Insert custom C code in generated: Terminate function
            set_param(lib, "SimUserIncludeDirs", "../obj/CodeGenerator");%Simulation Custom Code/Additional build information: Include directories
            %set_param(lib, "SimUserSources", "");%Simulation Custom Code/Additional build information: Source Files
            set_param(lib, "SimUserLibraries", "../obj/msgblocks/msgblocks.a");%Simulation Custom Code/Additional build information: Libraries
            %set_param(lib, "SimUserDefines", "");%Simulation Custom Code/Additional build information: Defines

            set_param(lib, "RTWUseSimCustomCode", "on"); % Code Generation Custom Code / Use the same custom code settings as Simulation Target
            % RTWUseLocalCustomCode: 'on'/'off' Use local custom code settings(do not inherit from main model)
            % below params aren't needed if RTWUseSimCustomCode is 'on'
            %Configuration Parameters / Code Generation Custom Code
            %  CustomSourceCode: Insert custom C code in generated: Source file
            %  CustomHeaderCode: Insert custom C code in generated: Header file
            % CustomInitializer: Insert custom C code in generated: Initialize function
            %  CustomTerminator: Insert custom C code in generated: Terminate function
            %     CustomInclude: Additional build information: Include directories
            %      CustomSource: Additional build information: Source files
            %     CustomLibrary: Additional build information: Libraries
            %      CustomDefine: Additional build information: Defines



            %execute all the generated matlab files that create simulink blocks!
            addpath(MsgToolsSimulinkLibrary.AbsPath(msgdir));
            obj.ProcessDir(simulink_block_library_name, msgdir, msgdir);
            obj.ProcessHeaderDir(basedir, cdir);

            % save the model
            save_system(simulink_block_library_name);
            
            % write the header file
            h_filename = strcat(msgdir,'/msgtools.h');
            fprintf("Creating %s\n", h_filename); 
            fileID = fopen(h_filename,'w');
            fprintf(fileID, '%s\n',obj.header_file_contents{:});
            fclose(fileID);
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
                fprintf("Running %s\n", path);
                [inputblk, outputblk] = feval(functionname, simulink_block_library_name, MsgToolsSimulinkLibrary.header_params);
                set_param(inputblk,'Position',obj.next_position());
                set_param(outputblk,'Position',obj.next_position());
            end

            % Get a list of all files and folders in this folder.
            d = dir(dirname);
            isub = [d(:).isdir]; % returns logical vector
            subFolders = {d(isub).name}';
            % exclude . and .., and also +headers and +Network.
            subFolders(ismember(subFolders,{'.','..','+headers','+Network'})) = [];
            % recurse into subdir.
            for k = 1 : length(subFolders)
                obj.ProcessDir(simulink_block_library_name, basedir, char(strcat(dirname,'/',subFolders(k))));
            end
        end
        function ProcessHeaderDir(obj, basedir, dirname)
            fprintf('Processing %s\n', dirname);
            filenames = dir(strcat(dirname,'/*.h'));
            % loop over filenames in dir
            for f = 1:numel(filenames)
                filename = filenames(f).name;
                obj.header_file_contents(end+1) = "#include """ + strrep(dirname, basedir+'/', '') + "/" + filename + """";
            end
            % Get a list of all files and folders in this folder.
            d = dir(dirname);
            isub = [d(:).isdir]; % returns logical vector
            subFolders = {d(isub).name}';
            subFolders(ismember(subFolders,{'.','..'})) = [];
            % recurse into subdir.
            for k = 1 : length(subFolders)
                obj.ProcessHeaderDir(basedir, char(strcat(dirname,'/',subFolders(k))));
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
