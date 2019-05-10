import os
from sys import argv
import socket
import binascii
from time import sleep

def decimaltohex(integer):
    """take decimal integer string as
    parameter return hex string"""
    return str(hex(integer))[2::]

def decimaltobinary(integer):
    """take decimal integer string as
    parameter return binary string"""
    return str(bin(integer))[2:]

def binarytohex(binary):
    """take binary string as parameter
    return hex string"""
    return str(hex(int(binary, 2)))[2:]

def chartohex(char):
    """take char as parameter return
    hex string"""
    return format(ord(char), "x")

def hextodecimal(string):
    """take hex string as parameter
    return decimal string"""
    return str(int(string,16))

def hextobinary(string):
    """take hex string as parameter
    return binary string with 4 bits"""
    return str(bin(int(string))[2:].zfill(4))

def send_query(message):
    """create socket to send query message"""

    ServerAddress = ("8.8.8.8", 53)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(3):
        try:
            print("DNS response received (attempt " + str(i+1) + " of 3)")
            sock.sendto(binascii.unhexlify(message), ServerAddress)
            sleep(5)
            data, _ = sock.recvfrom(4096)
            if data:
                print("Processing DNS response..")
                break
            elif not data and i == 3:
                print("Error: timeout.")
        finally:
            sock.close()
    return binascii.hexlify(data).decode("utf-8")

def main():
    if len(argv) != 2:
        print("usage: python3 my-dns-client.py <hostname>")
        return 1
    print("Preparing DNS query..")
    print("Contacting DNS server..")
    print("Sending DNS query..")

    """query question section"""
    QnameQuestion = ""
    QtypeQuestion = ""
    QclassQuestion = ""
    for i in range(0, 16, 4):
        QtypeQuestion += binarytohex((decimaltobinary(1).zfill(16))[i:i+4])
        QclassQuestion += binarytohex((decimaltobinary(1).zfill(16))[i:i+4])
    HostName = argv[1]
    if(HostName.find("www") != -1):
        HostName = HostName[4::]
    QnameSection1 = (HostName.split('.'))[0]
    QnameSection2 = (HostName.split('.'))[1]
    LengthQnameSection1 = len(QnameSection1)
    LengthQnameSection2 = "0" + str(len(QnameSection2))
    if LengthQnameSection1 < 10:
        LengthQnameSection1 = "0" + str(LengthQnameSection1)
    else:
        LengthQnameSection1 = str(LengthQnameSection1)

    QnameQuestion += LengthQnameSection1
    for c in QnameSection1:
        QnameQuestion += str(chartohex(c))
    QnameQuestion += LengthQnameSection2
    for c in QnameSection2:
        QnameQuestion += str(chartohex(c))
    QuestionSection = QnameQuestion + "00" +  QtypeQuestion + QclassQuestion

    """query header section"""
    IdHeader = decimaltohex(os.getpid()).zfill(4)
    QrHeader = decimaltobinary(0)
    OpcodeHeader = decimaltobinary(0).zfill(4)
    AaHeader = decimaltobinary(0)
    TcHeader = decimaltobinary(0)
    RdHeader = decimaltobinary(1)
    RaHeader = decimaltobinary(0)
    ZHeader = decimaltobinary(0).zfill(3)
    RcodeHeader = decimaltobinary(0).zfill(4)
    Line2Binary = QrHeader + OpcodeHeader + AaHeader + TcHeader + RdHeader + RaHeader + ZHeader + RcodeHeader
    Line2Header = ""
    QdcountHeader = ""
    AncountHeader = ""
    NscountHeader = ""
    ArcountHeader = ""
    for i in range(0, 16, 4):
        Line2Header += binarytohex(Line2Binary[i:i+4])
        QdcountHeader += binarytohex((decimaltobinary(1).zfill(16))[i:i+4])
        AncountHeader += binarytohex((decimaltobinary(0).zfill(16))[i:i+4])
        NscountHeader += binarytohex((decimaltobinary(0).zfill(16))[i:i+4])
        ArcountHeader += binarytohex((decimaltobinary(0).zfill(16))[i:i+4])
    HeaderSection = IdHeader + Line2Header + QdcountHeader + AncountHeader + NscountHeader + ArcountHeader

    """query message section"""
    QueryMessage = HeaderSection + QuestionSection

    """response section"""
    response = send_query(QueryMessage)
    ResponseHeader = response[:24]
    ResponseQuestion = response[24:(response.find("0000010001"))+10]
    ResponseAnswer = response[(response.find("0000010001"))+10::]

    """response header section"""
    IdResponse = ResponseHeader[0:4]
    Line2Binary = ""
    for i in ResponseHeader[4:8]:
        Line2Binary += hextobinary(i)
    QrResponse = Line2Binary[0:1]
    OpcodeResponse = Line2Binary[1:5]
    AaResponse = Line2Binary[5:6]
    TcResponse = Line2Binary[6:7]
    RdResponse = Line2Binary[7:8]
    RaResponse = Line2Binary[8:9]
    ZResponse = Line2Binary[9:12]
    RcodeResponse = Line2Binary[12:16]
    QdcountResponse = ResponseHeader[8:12]
    AncountResponse = ResponseHeader[12:16]
    NscountResponse = ResponseHeader[16:20]
    ArcountResponse = ResponseHeader[20:24]
    print("----------------------------------------------------------------------------")
    print("header.ID = " + hextodecimal(IdResponse))
    print("header.QR = " + hextodecimal(QrResponse))
    print("header.OPCODE = " + hextodecimal(OpcodeResponse))
    print("header.AA = " + hextodecimal(AaResponse))
    print("header.TC = " + hextodecimal(TcResponse))
    print("header.RD = " + hextodecimal(RdResponse))
    print("header.RA = " + hextodecimal(RaResponse))
    print("header.Z = " + hextodecimal(ZResponse))
    print("header.RCODE = " + hextodecimal(RcodeResponse))
    print("header.QDCOUNT = " + hextodecimal(QdcountResponse))
    print("header.ANCOUNT = " + hextodecimal(AncountResponse))
    print("header.NSCOUNT = " + hextodecimal(NscountResponse))
    print("header.ARCOUNT = " + hextodecimal(ArcountResponse))

    """answer question section"""
    QnameResponse = ResponseQuestion[0:ResponseQuestion.find("00010001")][0:-2]
    QtypeResponse = ResponseQuestion[ResponseQuestion.find("00010001"):ResponseQuestion.find("00010001")+4]
    QclassResponse = ResponseQuestion[ResponseQuestion.find("00010001")+4::]
    QnameStr = ""
    QnameChr = ''
    for i in range(0, len(QnameResponse), 2):
        if(QnameResponse[i:i+2][0] != str(0)):
            QnameChr = chr(int(hextodecimal(QnameResponse[i:i+2])))
        else:
            QnameChr = '.'
        QnameStr += str(QnameChr)
    if(argv[1].find("www") != -1):
        QnameStr = "www" + QnameStr
    else:
        QnameStr = QnameStr[1:len(QnameStr)]
    print("question.QNAME = " + QnameStr)
    print("question.QTYPE = " + hextodecimal(QtypeResponse))
    print("question.QCLASS = " + hextodecimal(QclassResponse))

    """answer section"""
    NameAnswer = ResponseAnswer[0:4]
    Name = 0
    for i in NameAnswer:
        Name += str(bin(int(i, 16))[2:].zfill(4)).count('0')
    TypeAnswer = ResponseAnswer[4:8]
    ClassAnswer = ResponseAnswer[8:12]
    TtlAnswer = ResponseAnswer[12:20]
    RdlengthAnswer = ResponseAnswer[20:24]
    RdataAnswer = ResponseAnswer[24::]
    if hextodecimal(AncountResponse) != "1":
        RdataAnswer = RdataAnswer[0:16]
    IpAddress = ""
    for i in range(0, len(RdataAnswer), 2):
        sub = RdataAnswer[i:i+2]
        IpAddress += (hextodecimal(sub) + ".")
    IpAddress = IpAddress[0:-1]
    print("answer.NAME = " + str(Name))
    print("answer.TYPE = " + hextodecimal(TypeAnswer))
    print("answer.CLASS = " + hextodecimal(ClassAnswer))
    print("answer.TTL = " + hextodecimal(TtlAnswer))
    print("answer.RDLENGTH = " + hextodecimal(RdlengthAnswer))
    print("answer.RDATA = " + IpAddress)
    print("----------------------------------------------------------------------------")


if __name__ == "__main__":
  main()
