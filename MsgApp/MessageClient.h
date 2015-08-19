#include "Cpp/NetworkHeader.h"
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

    Q_SIGNALS:
        void newMessageComplete(Message* msg);

    private slots:
        void onDataReady()
        {
            while(1)
            {
                int bytesAvailable = _ioDevice.bytesAvailable();
                if(!_gotHeader)
                {
                    if(bytesAvailable >= (int)sizeof(_inProgressHeader))
                    {
                        int length = _ioDevice.read((char*)&_inProgressHeader, sizeof(_inProgressHeader));
                        if(length == sizeof(_inProgressHeader))
                        {
                            _inProgressMessage = new Message(_inProgressHeader.GetLength());
                            *_inProgressMessage->hdr = _inProgressHeader;
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
                    int bytesWanted = _inProgressHeader.GetLength();
                    bytesAvailable = _ioDevice.bytesAvailable();
                    if(bytesAvailable >= bytesWanted)
                    {
                        int length = _ioDevice.read((char*)_inProgressMessage->GetDataPtr(), bytesWanted);
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
            int count = sizeof(NetworkHeader) + msg->hdr->GetLength();
            return count == _ioDevice.write((char*)msg->hdr, count);
        }
    private:
        QIODevice& _ioDevice;
        bool _gotHeader;
        NetworkHeader _inProgressHeader;
        Message* _inProgressMessage;
};
