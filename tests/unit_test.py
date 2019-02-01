
import spi_serial
import struct
import time


def send_get_pkt_cmd(ss, chan, timeout):
    timeout = struct.pack("<I", int(timeout))
    cmd = [3, chan]
    cmd.extend(timeout)
    ss.write(cmd)


def cmd3(ss, chan, other):
    while True:
        print("Command 3: Receive")
        send_get_pkt_cmd(ss, chan, 2222)
        print("waiting for pkt")
        while ss.inWaiting() == 0:
            time.sleep(1)
        resp = ss.read(0)
        print(resp)
        if resp[2] == other:
            print("Success")
            return 0
        else:
            print("Failure")
            return 1


def cmd4(ss, chan):
    print("Command 4: Send")
    cmd = [4, chan, 0, 0, 4, 4, 4, 0]
    ss.write(cmd)
    while ss.inWaiting() == 0:
        time.sleep(1)
    resp = ss.read(0)
    print(resp)
    if resp != [0]:
        print("Failure")
        return 1
    else:
        print("Success")
        return 0


def cmd5(ss, chan, other):  # Test incomplete
    print("Command 5: Send and Listen")
    timeout = struct.pack("<I", int(2222))
    cmd = [5, chan, 0, 0, chan]
    cmd.extend([timeout, 0, 5, 5, 5, 0])
    # 255,0,5,5,5,0]
    ss.write(cmd)
    print("waiting for pkt")
    while ss.inWaiting() == 0:
        time.sleep(1)
    resp = ss.read(0)
    print(resp)
    if resp[2] == other:
        print("Success")
        return 0
    else:
        print("Failure")
        return 1


if __name__ == "__main__":
    import argparse
    import time

    parser = argparse.ArgumentParser(description='UnitTest Explorer Control')
    order = parser.add_mutually_exclusive_group()
    # possible options:
    # - receive first (-r)
    order.add_argument('-r', '--receive', action='store_true',
                       help='set device to receive test message first')

    # - transmit first (-t)
    order.add_argument('-t', '--transmit', action='store_true',
                       help='set device to transmit test message first')

    # - select channel (--c)
    parser.add_argument('--c', dest='channel', default=0, type=int,
                        help='set rx/tx channel')

    # - select number of send/receive (or recive/send) cycles
    parser.add_argument("-s", '--send_receive', type=int, default=10,
                        help='select # of send/receive cycles')

    args = parser.parse_args()
    print(args)

    ss = spi_serial.SpiSerial()
    ss.reset()

    failures = 0

    print("915MHz Explorer Board Unit Test Begin")
    print("Command 1: State")
    cmd = [1]
    ss.write(cmd)
    ss.inWaiting()
    resp = ss.read(0)
#    print(resp)
    if resp != [79, 75, 0]:
        print("Failed")
        failures += 1
    else:
        print("Success")

    print("Command 2: Version")
    cmd = [2]
    ss.write(cmd)
    ss.inWaiting()
    resp = ss.read(0)
#    print(resp)
    if resp != [115, 117, 98, 103, 95, 114, 102,
                115, 112, 121, 32, 48, 46, 56, 0]:
        print("Failed")
        failures += 1
    else:
        print("Success")

    for num in range(0, args.send_receive):
        if args.receive:
            print("Receive/Send cycle #" + str(num+1))
            result0 = cmd3(ss, args.channel, 4)
            failures += result0
            time.sleep(1)
#            result1 = cmd5(ss,args.channel,4)
#            failures += result1
            result2 = cmd4(ss, args.channel)
            failures += result2
        elif args.transmit:
            print("Send/Receive cycle #" + str(num+1))
#            result0 = cmd5(ss,args.channel,5)
#            failures += result0
            result1 = cmd4(ss, args.channel)
            failures += result1
            result2 = cmd3(ss, args.channel, 4)
            failures += result2
            time.sleep(1)
        else:
            print("No Send/Receive order argument provided. " +
                  "Skipping Commands 3,4,5. See --help for more information.")

    print("Command 6: Update Register")
    cmd = [9, 10]
    ss.write(cmd)
    while ss.inWaiting() == 0:
        time.sleep(1)
    resp = ss.read(0)
    print(resp)
    old = resp[0]
    if old == 255:
        new = old - 1
    else:
        new = old + 1
    cmd = [6, 10, new]
    ss.write(cmd)
    ss.inWaiting()
    resp = ss.read(0)
    print(resp)
    if resp != [1, 0]:
        print("Failure")
        failures += 1
    else:
        print("Success")

    print("Command 9: Read Register")
    cmd = [9, 10]
    ss.write(cmd)
    ss.inWaiting()
    resp = ss.read(0)
    if resp != [new, 0]:
        print("Failure")
        failures += 1
    else:
        print("Success")

    print("Command 7: Reset")
    cmd = [7]
    ss.write(cmd)
    time.sleep(1)
    ss.inWaiting()
    resp = ss.read(0)
    cmd = [9, 10]
    ss.write(cmd)
    ss.inWaiting()
    resp = ss.read(0)
    if resp != [old, 0]:
        print("Failure")
        failures += 1
    else:
        print("Success")

    print("Command 8: LED Control")
    cmd = [8, 0, 1]
    ss.write(cmd)
    ss.inWaiting()
    print("")

    if failures == 0:
        print("If LED0 (D3) is lit, Unit Test was succcessful!")
    else:
        print("Unit Test failed. See above for more information.")
