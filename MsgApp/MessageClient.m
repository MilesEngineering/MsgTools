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
            connectMsg = Messages.Network.Connect;
            connectMsg.Name(1:10) = uint8('Matlab 1.0');
            obj.SendMsg(connectMsg);
            % note: We need to send a SubscriptionList/MaskedSubscription
            % message to receive *any* messages!
            % commented-out code below subscribes to all IDs (because Mask
            % defaults to zero)
            % subMsg = Messages.Network.MaskedSubscription;
            % obj.SendMsg(subMsg);
        end
        function delete(~)
            clear obj.clientSocket;
        end
        function ret = GetMsg(obj)
            %fprintf('Waiting for %d header bytes\n', obj.hdrObj.SIZE);
            hdrData = read(obj.clientSocket, obj.hdrObj.SIZE);
            if(length(hdrData) ~= obj.hdrObj.SIZE)
                fprintf('\nERROR!  Read %d/%d bytes from socket\n', length(hdrData), obj.hdrObj.SIZE);
            end
            hdr = feval(obj.hdrClass.Name, hdrData);
            %fprintf('Waiting for %d body bytes\n', hdr.DataLength);
            bodyData = read(obj.clientSocket, hdr.DataLength);
            if isKey(obj.msgTools.msgClassnameFromID, hdr.MessageID)
                msg = obj.msgTools.ConstructMsg(hdr.MessageID, bodyData);
                ret = msg;
            else
                fprintf('Did not find definition for message %d (0x%X)\n', hdr.MessageID, hdr.MessageID);
                ret = [];
            end
        end
        function SendMsg(obj, msg, length)
            hdr = feval(obj.hdrClass.Name);
            hdr.MessageID = msg.MSG_ID;
            if(nargin > 2)
                hdr.DataLength = length;
            else
                hdr.DataLength = msg.MSG_SIZE;
            end
            % hdr.DataLength = length(msg.m_data);
            write(obj.clientSocket, hdr.m_data);
            if(hdr.DataLength > 0)
                write(obj.clientSocket, msg.m_data);
            end
        end
        function SubscribeToMessage(obj,id,mask)
            subMsg = Messages.Network.MaskedSubscription;
            if(nargin > 2)
                subMsg.Mask = mask;
            elseif(nargin > 1)
                subMsg.Mask = bitcmp(0);
            end
            subMsg.Value = id;
            obj.SendMsg(subMsg);
        end
        function ret = WaitForMsg(obj, id)
            while(1)
                msg = obj.GetMsg();
                %fprintf('Got message with ID 0x%X', msg.MSG_ID);
                if(msg.MSG_ID == id)
                    %fprintf('Got matching message! returning!');
                    ret = msg;
                    break;
                end
            end
        end
        function PrintMessages(obj, id, mask)
            obj.SubscribeToMessage(id,mask);
            while(1)
                msg = obj.GetMsg()
                if isempty(msg)
                    break;
                end
            end
        end
    end
end
