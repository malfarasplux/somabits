# SOMA Server
SOMA Server is a server-side application which can automatically discover all the SOMA devices in a network. After discovering, SOMA Server can route sensors and actuators values to respective devices based on the user-supplied routing information using OSC protocol.

## Usage
![picture](interface1.png)

Press the Discover button to discover all the SOMA devices in a network.

![picture](interface2.png)

Click on the name of the device to check the attached sensors and actuators 

![picture](interface3.png)

## For Developers
SOMA Server is developed on top of Visual Studio 2017 using .Net Framework.
 
SOMA Server uses Mono.Zeroconf for the discovery of devices which is a Zero Configuration Networking library for .NET

The easiest way to get started is to use the NuGet package.

> Install-Package [Mono.Zeroconf](https://www.nuget.org/packages/Mono.Zeroconf/)


More detailed documentation will come shortly