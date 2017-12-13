
package msgtools;

public class FieldAccess {
    public static int toUnsignedInt(byte b) {
        return 0x000000FF & b;        
    }

    public static int toUnsignedInt(short s) {
        return 0x0000FFFF & s;
    }

    public static long toUnsignedLong(int i) {
        return 0x00000000FFFFFFFFL & i;
    }

}