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


## Future Ideas
