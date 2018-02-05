#ifndef MESSAGE_CLIENT_H
#define MESSAGE_CLIENT_H

#include "MsgApp/FieldInfo.h"
#include "MsgApp/MsgInfo.h"
#include "Message.h"
#include "Cpp/headers/NetworkHeader.h"
#include <QObject>
#include <QIODevice>

class MessageClient : public QObject
{
    Q_OBJECT
    public:
        MessageClient(QIODevice* ioDevice)
        : _ioDevice(ioDevice),
          _gotHeader(false),
          _inProgressMessage(0)
        {
            connect(_ioDevice, &QIODevice::readyRead, this, &MessageClient::onDataReady);
        }

    Q_SIGNALS:
        void newMessageComplete(Message* msg);

    private slots:
        void onDataReady()
        {
            while(1)
            {
                int bytesAvailable = _ioDevice->bytesAvailable();
                if(!_gotHeader)
                {
                    if(bytesAvailable >= (int)sizeof(_inProgressHeader))
                    {
                        int length = _ioDevice->read((char*)&_inProgressHeader, sizeof(_inProgressHeader));
                        if(length == sizeof(_inProgressHeader))
                        {
                            _inProgressMessage = new Message(_inProgressHeader.GetDataLength());
                            memcpy(&_inProgressMessage->hdr, &_inProgressHeader, sizeof(_inProgressHeader));
                            _gotHeader = true;
                        }
                    }
                    else
                    {
                        break;
                    }
                }

                if(_gotHeader)
                {
                    int bytesWanted = _inProgressHeader.GetDataLength();
                    bytesAvailable = _ioDevice->bytesAvailable();
                    if(bytesAvailable >= bytesWanted)
                    {
                        int length = _ioDevice->read((char*)_inProgressMessage->GetDataPtr(), bytesWanted);
                        if(length == bytesWanted)
                        {
                            _gotHeader = false;
                            emit(newMessageComplete(_inProgressMessage));
                        }
                    }
                    else
                    {
                        break;
                    }
                }
            }
        }
    public slots:
        bool sendMessage(Message* msg)
        {
            int count = sizeof(NetworkHeader) + msg->hdr.GetDataLength();
            int txCount = _ioDevice->write((char*)&(msg->hdr), sizeof(msg->hdr));
            txCount += _ioDevice->write((char*)msg->GetDataPtr(), msg->hdr.GetDataLength());
            return count == txCount;
        }
    private:
        QIODevice* _ioDevice;
        bool _gotHeader;
        NetworkHeader _inProgressHeader;
        Message* _inProgressMessage;
};
#endif
