import scapy
from scapy_ssl_tls.ssl_tls import *
import socket

def tls_client(ip):
    # create socket, TLSSocket, and connect
    dasock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tlssock = TLSSocket(client=True, sock=dasock) 
    tlssock.connect(ip)

    # Set up version, ciphers, extensions
    version = TLSVersion.TLS_1_2
    #ciphers = [TLSCipherSuite.ECDHE_RSA_WITH_AES_128_GCM_SHA256] ### Doesn't work with alarm.com, but works with google.com ?
    ciphers = [TLSCipherSuite.RSA_WITH_AES_128_CBC_SHA]
    extensions = [TLSExtension() / TLSExtECPointsFormat(),
                  TLSExtension() / TLSExtSupportedGroups()]

    # Create "client hello" packet
    p = TLSRecord(version=version) / TLSHandshakes(handshakes=[TLSHandshake() /
                                    TLSClientHello(version=version,
                                                    compression_methods=list(range(0xff))[::-1],
                                                    cipher_suites=ciphers,
						    extensions=extensions)])
    # Send packet through the socket
    dasock.sendall(str(p))
    # Decrease the timeout (2 seconds is too long?)
    dasock.settimeout(0.5)
    # Keep receiving data until we have collected the entire response
    resp = []
    while True:
       try:
          data = dasock.recv(8192)
          if not data:
             break
          resp.append(data)
       except socket.timeout:
          break

    # Convert response string to a TLS object
    tls_resp = TLS("".join(resp))
    # Display the server response in its entirety
    tls_resp.show()

if __name__ == "__main__":
    if len(sys.argv) > 2:
        server = (sys.argv[1], int(sys.argv[2]))
        tls_client(server)
    else:
        print "Please enter host and IP to test SSL"
    
