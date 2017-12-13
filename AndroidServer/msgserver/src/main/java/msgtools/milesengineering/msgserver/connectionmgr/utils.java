package msgtools.milesengineering.msgserver.connectionmgr;

import android.net.Network;

import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.util.Enumeration;

/**
 * Utility class of useful functions.
 */

public class utils {
    /**
     * Retrieve the non-local host network interface address (e.g. Wi-Fi)
     *
     * @return InetAddress of the host.  null if no interface found
     */
    public static InetAddress getHostAddress() {
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            while( interfaces.hasMoreElements() ) {
                NetworkInterface ni = interfaces.nextElement();
                if ( ni.isLoopback() == false ) {
                    Enumeration<InetAddress> addrs = ni.getInetAddresses();
                    while(addrs.hasMoreElements()) {
                        InetAddress ia = addrs.nextElement();
                        if (ia instanceof Inet4Address) {
                            return ia;
                        }
                    }
                }
            }
        } catch (SocketException e) {
            e.printStackTrace();
        }

        return null;
    }
}
