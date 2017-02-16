package MsgApp;

import java.nio.ByteBuffer;

import Messages.NetworkHeader;

public class Message
{
    public Message(int datalen)
    {
        ByteBuffer buffer = ByteBuffer.allocate(NetworkHeader.SIZE+datalen);
        hdr = new NetworkHeader(buffer);
        m_data = buffer.slice();
        m_data.position(NetworkHeader.SIZE);
    }
    public Message(ByteBuffer buffer)
    {
        hdr = new NetworkHeader(buffer);
        m_data = buffer.slice();
        m_data.position(NetworkHeader.SIZE);
    }
    public void SetMessageID(int id){ hdr.SetMessageID(id); }
    public long GetMessageID() { return hdr.GetMessageID(); }
    /*void InitializeTime()
    {
        // \todo How to set 32-bit rolling ms counter?
        hdr.SetTime(0);
    }*/

    protected NetworkHeader hdr;
    protected ByteBuffer m_data;
};
