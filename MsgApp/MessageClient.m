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
            connectMsg = Network.Connect;
            connectMsg.Name(1:10) = uint8('Matlab 1.0');
            obj.SendMsg(connectMsg);
            % note: We need to send a SubscriptionList/MaskedSubscription
            % message to receive *any* messages!
            % commented-out code below subscribes to all IDs (because Mask
            % defaults to zero)
            % subMsg = Network.MaskedSubscription;
            % obj.SendMsg(subMsg);
        end
        function ret = GetMsg(obj)
            %fprintf('Waiting for %d header bytes\n', obj.hdrObj.SIZE);
            hdrData = read(obj.clientSocket, obj.hdrObj.SIZE);
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
        function SendMsg(obj, msg)
            hdr = feval(obj.hdrClass.Name);
            hdr.MessageID = msg.MSG_ID;
            hdr.DataLength = msg.MSG_SIZE;
            % hdr.DataLength = length(msg.m_data);
            write(obj.clientSocket, hdr.m_data);
            write(obj.clientSocket, msg.m_data);
        end
        function PrintMessages(obj, id, mask)
            if(nargin > 2)
                subMsg = Network.MaskedSubscription;
                subMsg.Mask = mask;
                subMsg.Value = id;
                obj.SendMsg(subMsg);
            elseif(nargin > 1)
                subMsg = Network.MaskedSubscription;
                subMsg.Value = id;
                subMsg.Mask = bitcmp(0);
                obj.SendMsg(subMsg);
            end
            while(1)
                msg = obj.GetMsg()
                if isempty(msg)
                    break;
                end
            end
        end
    end
end
