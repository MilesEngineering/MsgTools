/*
    <OUTPUTFILENAME>
    Created <DATE> from:
        Messages = <INPUTFILENAME>
        Template = <TEMPLATEFILENAME>
        Language = <LANGUAGEFILENAME>

                     AUTOGENERATED FILE, DO NOT EDIT

*/
<ONCE>import 'dart:typed_data';

<ENUMERATIONS>

class <MSGNAME>
{
    static const int SIZE = <MSGSIZE>;
    ByteData _data;
    <MSGNAME>()
    {
        _data = new ByteData(SIZE);
        Init();
    }
    <MSGNAME>.fromBuffer(ByteBuffer buffer)
    {
        _data = new ByteData.view(buffer);
    }
    void Init()
    {
        <INIT_CODE>
    }
    <FIELDINFOS>
    void SetMessageID(int input)
    {
        int id = input;
        <SETMSGID>;
    }
    int GetMessageID()
    {
        return <GETMSGID>;
    }
    <ACCESSORS>
/*
    static MsgInfo* ReflectionInfo()
    {
        static bool firstTime = true;
        static MsgInfo msgInfo(-1, "<MSGNAME>", "<MSGDESCRIPTION>", SIZE);
        if(firstTime)
        {
            firstTime = false;
            msgInfo.AddField(new <REFLECTION>);
        }
        return &msgInfo;
    }
*/
}
