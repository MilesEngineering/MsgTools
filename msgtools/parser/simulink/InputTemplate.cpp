#define S_FUNCTION_NAME MsgInput<MSGNAME> /* Defines and Includes */
#define S_FUNCTION_LEVEL 2

#include "simstruc.h"

#define MDL_START
extern "C" static void mdlStart(SimStruct *S)
{
    // Do we need to make sure that calling Subscribe multiple times
    // doesn't create multiple subscriptions?
    Subscribe(<MSGNAME>Message::MSG_ID);
}

extern "C" static void mdlInitializeSizes(SimStruct *S)
{
    // Maybe use block parameters to add additional source/destination/deviceID
    // to distinguish betweem multiple identical devices (like 3 reaction wheels)
    ssSetNumSFcnParams(S, 0);
    if (ssGetNumSFcnParams(S) != ssGetSFcnParamsCount(S)) {
        return; /* Parameter mismatch reported by the Simulink engine*/
    }

    // for input blocks (receiving a message), NumInputPorts=0
    if (!ssSetNumInputPorts(S, 0)) return;

    // for input blocks (receiving a message), NumOutputPorts=<NUMBER_OF_SUBFIELDS>
    if (!ssSetNumOutputPorts(S,<NUMBER_OF_SUBFIELDS>)) return;
    <FOREACHSUBFIELD(ssSetOutputPortWidth(S, <FIELDNUMBER>, <FIELDCOUNT>);)>
    ssSetNumSampleTimes(S, 1);

    /* Take care when specifying exception free code - see sfuntmpl.doc */
    ssSetOptions(S, SS_OPTION_EXCEPTION_FREE_CODE);
}

extern "C" static void mdlInitializeSampleTimes(SimStruct *S)
{
    ssSetSampleTime(S, 0, INHERITED_SAMPLE_TIME);
    ssSetOffsetTime(S, 0, 0.0);
}

#define MDL_OUTPUT
#if defined(MDL_OUTPUT) && defined(MATLAB_MEX_FILE) 
extern "C" static void mdlOutputs(SimStruct *S, int_T tid)
{
    // for receiving messages
    //# used stored copy of latest message input<MSGNAME> declared and read from queue elsewhere
    <FOREACHSUBFIELD({real_T *output = ssGetOutputPortRealSignal(S,<FIELDNUMBER>); for (int_T i=0; i < <FIELDCOUNT>; i++) {output[i] = input<MSGNAME>.Get<FIELDNAME>(i);}})>
}
#endif

#define MDL_UPDATE 
#if defined(MDL_UPDATE) && defined(MATLAB_MEX_FILE) 
static void mdlUpdate(SimStruct *S, int_T tid)
{
} 
#endif 

extern "C" static void mdlTerminate(SimStruct *S){}

#ifdef MATLAB_MEX_FILE /* Is this file being compiled as a MEX-file? */
#include "simulink.c" /* MEX-file interface mechanism */
#else
#include "cg_sfun.h" /* Code generation registration function */
#endif
