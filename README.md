# openvpn-tester
Python scripts to test OpenVPN server endpoints via OpenVPN and SSL/TLS handshakes

## Usage
~~~
> python openvpn-proto-test.py <OpenVPN server hostname or IP> <OpenVPN server port>
~~~

## Background
I started exploring the low-level details of VPN connections back in 2020.  Our team relied on OpenVPN for connecting video cameras out in the field to our backend platform, and I was looking for a way to programmatically test the public endpoints of our OpenVPN servers.  Ultimately, I was able to achieve my goals by creating some monitoring code that validated our public OpenVPN servers by completing the first step in an OpenVPN protocol handshake.  At the time, I wanted to go further and build my own lightweight OpenVPN client that could fully connect to our backend.  The biggest challenge I faced was in navigating the way that the OpenVPN protocol intergrates the TLS handshake process into it's own communications.  While I have yet to tweak my scripts to complete the TLS handshake, I did discover a side benefit of my investigations.  My handshake scripts could not only be used to validate an OpenVPN server endpoint, but also could be used to read and validate the server's certificate.  When integrated within a monitoring application, this certificate validity check could be extermely useful in tracking certificate experations!

I owe much of my knowledge on the OpenVPN protocol (and a portion of the code) to Tomas Novickis, who researched and built an OpenVPN test harness as part of a master thesis (see [
Protocol state fuzzing of an OpenVPN](https://www.ru.nl/publish/pages/769526/tomas_novickis.pdf)).

## Deeper Dive
Before I dig into the code, here is a quick primer on using certificates and on the SSL/TLS handshake process.  In a nutshell, communications between two parties over the Internet are secured with certificates.  Often, a client (either a user's web browser or one of our cameras calling home) will attempt to establish a communication channel with a server using the TLS protocol.  This method provides a way to authenticate that both parties are who they say they are and it establishes a secure channel for communications.  The initial step for establishing this channel is the handshake - here is an illustration of these client/server back and forth communications: 
![SSL/TLS Handshake](/SSLTLS_handshake.png "SSL/TLS Handshake")

### An Example TLS Handshake Script
For my purposes, I wanted to send a properly formatted message to the server to initiate the handshake (client hello), then receive and interpret the response from the server (server hello) to extract the server certificate (and read the expiration date).  As it so happens, there are plenty of ways to do this in the code; the method I chose was using a Python library called Scapy - this is a powerful tool for manipulating network communications down to the packet level.  Scapy also contains higher-level methods for constructing the TLS handshake and interpeting the results.  Pulling pieces from example methods, I put together my own example script that sends the client hello and interprets the server response (get_server_hello.py).  

I ran this script against "https://www.alarm.com" and managed to pull our the server certificate from the response (snippet below):

~~~
   |      |         |   |  not_before= <ASN1_UTC_TIME['190312000000Z']>
   |      |         |   |  not_after = <ASN1_UTC_TIME['210316120000Z']>
   |      |         |   |  \subject   \
   |      |         |   |   |###[ X509RDN ]###
   |      |         |   |   |  oid       = <ASN1_OID['.2.5.4.6']>
   |      |         |   |   |  value     = <ASN1_PRINTABLE_STRING['US']>
   |      |         |   |   |###[ X509RDN ]###
   |      |         |   |   |  oid       = <ASN1_OID['.2.5.4.8']>
   |      |         |   |   |  value     = <ASN1_PRINTABLE_STRING['VA']>
   |      |         |   |   |###[ X509RDN ]###
   |      |         |   |   |  oid       = <ASN1_OID['.2.5.4.7']>
   |      |         |   |   |  value     = <ASN1_PRINTABLE_STRING['Mc Lean']>
   |      |         |   |   |###[ X509RDN ]###
   |      |         |   |   |  oid       = <ASN1_OID['.2.5.4.10']>
   |      |         |   |   |  value     = <ASN1_PRINTABLE_STRING['Alarm.com Incorporated']>
   |      |         |   |   |###[ X509RDN ]###
   |      |         |   |   |  oid       = <ASN1_OID['.2.5.4.11']>
   |      |         |   |   |  value     = <ASN1_PRINTABLE_STRING['Cloud']>
   |      |         |   |   |###[ X509RDN ]###
   |      |         |   |   |  oid       = <ASN1_OID['.2.5.4.3']>
   |      |         |   |   |  value     = <ASN1_BADTAG[<ASN1_DECODING_ERROR['\x0c\x0b*.alarm.com']{{Codec <ASN1Codec BER[1]> not found for tag <ASN1Tag UTF8_STRING[12]>}}>]>
~~~   
   
This is good!  I could use this to verify the expiration date (here, I see it is Mar 16th, 2021).   

### SSL/TLS with OpenVPN?

Much of the above can be achieved with existing libraries in any language (I think we could easily recreate this in .NET with just the libraries we have).  What if this could be extended to pull the server certificate from our OpenVPN servers?  The challenges here are much greater:

 - Instead of the connection-oriented protocol that browsers use to communication with websites (TCP), OpenVPN connections operate over UDP, which is essentially the client and server broadcasting their messages at each other without an established connection or error-checking.
 - OpenVPN connections make use of their own custom protocol to ensure the reliability of the messages.  The entire TLS handshake process is encapsulated within custom OpenVPN packets, which themselves obey their own handshake process between OpenVPN client and server

While the OpenVPN code is open-source, the details of the custom protocol are difficult to parse out just by reading the code.  I was fortunate to discover a handful of online projects that outlined this in detail.  In fact, one research project had taken the first steps toward recreating the OpenVPN client requests using Scapy in Python - this was the impetus for me choosing to work within the Scapy tools.

### Simulating an OpenVPN Client in Python
I heavily reworked an example script from Tomas' research project into the final script (openvpn-proto-test.py).  Recreating the TLS handshake inside the OpenVPN protocol goes as follows:
 
 1) Client sends a "client hard reset" packet to server, requesting a new session by sending initial client keys
 2) Server responds with a "server hard reset" packet, sending the initial server keys
 3) Client sends an acknowledgement that it received the server packet (ACK packet)
 4) Client then sends a "control packet" that contains the initial "client hello" of a TLS handshake
 5) Server responds with an acknowedgment and with its own "control packet" containing the "server hello" portion of the TLS handshake
 
Contained inside the server's control packet in step 5 is the server's certificate.  The script I wrote attempts to send the correct client packets in steps 1,3,4 and parse the server packet from step 5 to extract the server certificate (and then the expiration date).  Here is the output from the script attempting to communicate with our OpenVPN servers:

~~~
[root@bvktest325 bvkoch]# python openvpn-proto-test.py videovpn.devicetask.com 1294
WARNING: No route found for IPv6 destination :: (no default route?)
Connected to server: ('videovpn.devicetask.com', 1294)
OpenVPN packet created
###[ P_CONTROL_HARD_RESET_CLIENT_V2 ]###
  opcode    = 0x38
  Session_ID= 14031645777635506632L
  Message_Packet_ID_Array_Length= 0x0
  Message_Packet_ID= 1
Sending through TLSSocket...

RAW: @E▒v▒쓠▒ºk}▒▒▒
RAW HEX: 4045d276a3ec93a0ea0100000001c2ba6b7dee12f9c800000000
Opcode (hex): 40
Server SID (hex): 45d276a3ec93a0ea
Packet-ID (hex): 0100000001
Client SID (hex): c2ba6b7dee12f9c8
**********************************************************
Server SID: 5031214180147110122

###[ P_ACK_V1 ]###
  opcode    = 0x28
  Session_ID= 14031645777635506632L
  Message_Packet_ID_Array_Length= 0x1
  Message_Packet_ID= 2
  Remote_Session_ID= 5031214180147110122
Sending through TLSSocket...

~~~

The script sends the first hard reset packet (P_CONTROL_HARD_RESET_CLIENT_V2) using a random number for the session ID.  I get a response from the server, and when I parse that response, I see that it is in the expected format (opcode 0x40, which is P_CONTROL_HARD_RESET_SERVER_V2 (0x8) along with a keyID of 0) and I can also extract my session ID from the response.  In the next step, I send the ACK to the server, then attempt to wrap the TLS Handshake into the control packet (P_CONTROL_V1) to send to the server.  Unfortunately, I'm unable to parse the response from the server.  If I point my script at my own OpenVPN server and look at the server logs, I find that the server doesn't recognize my message as a valid TLS handshake attempt.  Almost there, but not quite reaching my goal.


## Future Ideas

The next step I'd like to take with this project is to fix the incorrect control packet in an attempt to get the OpenVPN server to send me the expected response.  I think the setup for the TLS handshake isn't quite correct; I might not be sending the TLS client key in my request, so the server isn't recognizing it.  Another thing I might try is to create the TLS client hello then break it up into a multipart request (each one encapsulated in an OpenVPN control packet).  When I look at a packet capture of the OpenVPN handshake, I can see multiple control packets coming from a successful camera VPN connection; the research project I found also mentions this, but I haven't yet found the correct way to create that.

When I'm able to get the correct server response from OpenVPN, I would then add some code to parse the certificate info in a readable way.  I would also like to try to recreate this in C#.  There's nothing particularly special about the Scapy packet library; the special sauce here is what I've learned about the OpenVPN packet structure and protcol - those could be recreated within a flexible SSL/TLS structure in C#.

There could be many uses for a tool like this.  I could start to automate the process of checking large numbers of certificates to alerting me well before any expire.  Performing such a check would also help keep track of the certificate versions and ciphers used, which could be useful in the event of newly discovered security vulnerabilities.  Thinking even more broadly, this tool could potentially be expanded to be a full-fledged simulation of an OpenVPN client in C#.  I could see something like this used to quickly and automatically verify new VPN servers during deployment. 
