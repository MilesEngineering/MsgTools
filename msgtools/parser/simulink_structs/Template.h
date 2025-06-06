/*
    Created from:
        Messages = <INPUTFILENAME>
        Template = <TEMPLATEFILENAME>
        Language = <LANGUAGEFILENAME>

                     AUTOGENERATED FILE, DO NOT EDIT

*/
#ifndef <MSGFULLNAME>Unpacked_H__
#define <MSGFULLNAME>Unpacked_H__

#include <stdint.h>

// This is for creating structs that correspond to messages,
// copying messages into and out of structs.

<ENUMERATIONS>


typedef struct
{
    <DECLARATIONS>
} <MSGFULLNAME>Unpacked;

#ifdef __cplusplus
extern "C" {
#endif

void <MSGFULLNAME>Send(const <MSGFULLNAME>Unpacked* unpackedMsg, int src, int dst);
void <MSGFULLNAME>Receive(<MSGFULLNAME>Unpacked* unpackedMsg, int src, int dst);

#ifdef __cplusplus
}
#endif

<ONCE>#define <ESCAPED_INPUT_FILENAME>_FILE_HASH <INPUT_FILE_HASH_BYTES>

#endif
