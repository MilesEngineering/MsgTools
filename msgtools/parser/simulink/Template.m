function [inputblk, outputblk] = <MSGNAME>(libname, header_params)
    % create c function block for message input
    inputblk = add_block("simulink/User-Defined Functions/C Function", libname+"/<MSGDESCRIPTOR>.Input");

    recv_code =[
        "// set block outputs based on last received message."
        "<GETFIELDS>"
    ];
    % Set code blocks
    set_param(inputblk, "OutputCode", sprintf('%s\n',recv_code{:}));
    set_param(inputblk, "StartCode", "// put your start code here");
    set_param(inputblk, "TerminateCode", "// put your terminate code here");

    % Note that ss is a handle to the blocks SymbolSpec and not a copy,
    % Changes made to ss immediately update the block w/o a set_param.
    ss = get_param(inputblk, "SymbolSpec");

    % Add symbols for all fields of the message.
    <FOREACHSUBFIELD(
    sym = ss.addSymbol("<FIELDNAME>");
    sym.Scope = "Output";
    sym.Type = "<FIELDTYPE>";
    sym.Size = "<FIELDCOUNT>"; % bizarre, but size needs to be a string also
    )>

    % add symbols for header parameters
    for header_param = 1:length(header_params)
        s = ss.addSymbol(header_params{header_param});
        s.Scope = "Parameter";
        s.Type = "int";
    end

    % create c function block for message output
    outputblk = add_block("simulink/User-Defined Functions/C Function", libname+"/<MSGDESCRIPTOR>.Output");

    % for sending messages
    send_code = ["<MSGNAME>Message msg;"];
    for header_param = 1:length(header_params)
        send_code(end+1) = "msg.Set"+header_params{header_param}+"("+header_params{header_param}+");";
    end
    more_send_code = [...
        "<SETFIELDS>",...
        "SendMessage(msg);"...
    ];
    send_code = [send_code more_send_code];

    % Set code blocks
    set_param(outputblk, "OutputCode", sprintf('%s\n',send_code{:}));
    set_param(outputblk, "StartCode", "// put your start code here");
    set_param(outputblk, "TerminateCode", "// put your terminate code here");

    % Note that ss is a handle to the blocks SymbolSpec and not a copy,
    % Changes made to ss immediately update the block w/o a set_param.
    ss = get_param(outputblk, "SymbolSpec");
    <FOREACHSUBFIELD(
    sym = ss.addSymbol("<FIELDNAME>");
    sym.Scope = "Input";
    sym.Type = "<FIELDTYPE>";
    sym.Size = "<FIELDCOUNT>"; % bizarre, but size needs to be a string also
    )>

    % add symbols for header parameters
    for header_param = 1:length(header_params)
        s = ss.addSymbol(header_params{header_param});
        s.Scope = "Parameter";
        s.Type = "int";
    end
end
