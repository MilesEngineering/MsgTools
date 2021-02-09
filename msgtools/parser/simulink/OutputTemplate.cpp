#define S_FUNCTION_NAME MsgOutput<MSGNAME> /* Defines and Includes */
#define S_FUNCTION_LEVEL 2

#include "simstruc.h"

#define MDL_START
extern "C" static void mdlStart(SimStruct *S)
{
}

extern "C" static void mdlInitializeSizes(SimStruct *S)
{
    // Maybe use block parameters to add additional source/destination/deviceID
    // to distinguish betweem multiple identical devices (like 3 reaction wheels)
    ssSetNumSFcnParams(S, 0);
    if (ssGetNumSFcnParams(S) != ssGetSFcnParamsCount(S)) {
        return; /* Parameter mismatch reported by the Simulink engine*/
    }

    // for output blocks (sending a message), NumInputPorts=<NUMBER_OF_SUBFIELDS>.
    if (!ssSetNumInputPorts(S, <NUMBER_OF_SUBFIELDS>)) return;
    <FOREACHSUBFIELD(ssSetInputPortWidth(S, <FIELDNUMBER>, <FIELDCOUNT>);)>

    // for output blocks (sending a message), NumOutputPorts=0.
    if (!ssSetNumOutputPorts(S,0)) return;

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
}
#endif

#define MDL_UPDATE 
#if defined(MDL_UPDATE) && defined(MATLAB_MEX_FILE) 
static void mdlUpdate(SimStruct *S, int_T tid)
{
    // for sending messages
    <MSGNAME>Message msg;
    <FOREACHSUBFIELD({InputRealPtrsType input = ssGetInputPortRealSignalPtrs(S,<FIELDNUMBER>); for (int_T i=0; i < <FIELDCOUNT>; i++) {msg.Set<FIELDNAME>(*(*input[i]), i);}})>
    SendMessage(msg);
} 
#endif 

extern "C" static void mdlTerminate(SimStruct *S){}

#ifdef MATLAB_MEX_FILE /* Is this file being compiled as a MEX-file? */
#include "simulink.c" /* MEX-file interface mechanism */
#else
#include "cg_sfun.h" /* Code generation registration function */
#endif
