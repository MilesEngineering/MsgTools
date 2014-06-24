#include "../CodeGenerator/obj/Cpp/Network.h"
#include <QObject>
#include <QIODevice>
#include "Message.h"

class MessageClient : public QObject
{
    Q_OBJECT
    public:
        MessageClient(QIODevice* ioDevice)
        : _ioDevice(*ioDevice),
          _gotHeader(false),
          _inProgressMessage(0)
        {
            connect(&_ioDevice, SIGNAL(readyRead()), this, SLOT(onDataReady()));
        }

    signals:
        void newMessageComplete(Message* msg);

    private slots:
        void onDataReady()
        {
            if(!_gotHeader && _ioDevice.bytesAvailable() >= (int)sizeof(_inProgressHeader))
            {
                int length = _ioDevice.read((char*)&_inProgressHeader, sizeof(_inProgressHeader));
                if(length == sizeof(_inProgressHeader))
                {
                    _inProgressMessage = new Message(_inProgressHeader.GetLength());
                    _gotHeader = true;
                }
            }

            if(_gotHeader)
            {
                int bytesWanted = _inProgressHeader.GetLength();

                if(_ioDevice.bytesAvailable() >= bytesWanted)
                {
                    int length = _ioDevice.read((char*)_inProgressMessage->GetDataPtr(), bytesWanted);
                    if(length == bytesWanted)
                    {
                        emit(newMessageComplete(_inProgressMessage));
                    }
                }
            }
        }
    public slots:
        bool sendMessage(Message* msg)
        {
            int count = sizeof(NetworkHeader) + msg->hdr->GetLength();
            return count == _ioDevice.write((char*)msg, count);
        }
    private:
        QIODevice& _ioDevice;
        bool _gotHeader;
        NetworkHeader _inProgressHeader;
        Message* _inProgressMessage;
};
