classdef MessageClient
    properties
        msgTools;
        hdrObj;
        hdrClass;
        clientSocket;
    end
    methods
        function obj = MessageClient(msgTools, headerObject, server, port)
            obj.msgTools = msgTools;
            obj.hdrObj = headerObject;
            obj.hdrClass = metaclass(headerObject);
            if(nargin<3)
                server = '127.0.0.1';
            end
            if(nargin<4)
                port=5678;
            end
            obj.clientSocket = tcpclient(server, port);
        end
        function ret = GetMsg(obj)
            fprintf('Waiting for %d header bytes\n', obj.hdrObj.SIZE);
            hdrData = read(obj.clientSocket, obj.hdrObj.SIZE);
            hdr = feval(obj.hdrClass.Name, hdrData);
            fprintf('Waiting for %d body bytes\n', hdr.DataLength);
            bodyData = read(obj.clientSocket, hdr.DataLength);
            msg = obj.msgTools.ConstructMsg(hdr.MessageID, bodyData);
            ret = msg;
        end
        function SendMsg(obj, msg)
            hdr = feval(obj.hdrClass.Name);
            hdr.MessageID = msg.MSG_ID;
            hdr.DataLength = msg.MSG_SIZE;
            % hdr.DataLength = length(msg.m_data);
            write(obj.clientSocket, hdr.m_data);
            write(obj.clientSocket, msg.m_data);
        end
    end
end
