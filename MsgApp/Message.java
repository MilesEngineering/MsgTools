import java.nio.ByteBuffer;

class Message
{
    Message(int datalen)
    {
        ByteBuffer buffer = ByteBuffer.allocate(NetworkHeader.SIZE+datalen);
        hdr = new NetworkHeader(buffer);
        m_data = buffer.slice();
        m_data.position(NetworkHeader.SIZE);
    }
    Message(ByteBuffer buffer)
    {
        hdr = new NetworkHeader(buffer);
        m_data = buffer.slice();
        m_data.position(NetworkHeader.SIZE);
    }
    void SetMessageID(long id){ hdr.SetID(id); }
    long GetMessageID() { return hdr.GetID(); }
    void InitializeTime()
    {
        /** \todo How to set 32-bit rolling ms counter? */
        hdr.SetTime(0);
    }

    protected NetworkHeader hdr;
    protected ByteBuffer m_data;
};
