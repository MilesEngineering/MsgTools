classdef <MSGNAME>
    methods
        function obj = <MSGNAME>(libname)
            fprintf("Not doing anything for header <MSGNAME>\n");
        end
    end
    methods (Static)
        function AddHeaderParams<MSGNAME>(ss)
            <FOREACHSUBFIELD(
            s = ss.addSymbol("<FIELDNAME>");
            s.Scope = "Parameter";
            s.Type = "<FIELDTYPE>";
            )>
        end
    end
end