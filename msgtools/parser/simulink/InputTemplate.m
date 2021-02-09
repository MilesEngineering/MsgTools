% how do i create the gcb?
% how do i set the C s-function name, so my C code gets executed for the block?
maskObj<MSGNAME> = Simulink.Mask.create(gcb);

disp('MsgInput<MSGNAME>');
<FOREACHSUBFIELD(port_label("output", <FIELDNUMBER>, '<FIELDNAME>');)>
