import threading
import socket
import time
import sys


# a = 0
# b = 1
# c = 2
# d = 3
# e = 4
# 99 = infinity

inPort = [44000, 44100, 44200, 44300, 44400]
outPort = [55000, 55100, 55200, 55300, 55400]
mainInPort = 44500
mainOutPort = 55500
ascii = 'ascii'
num_of_nodes = 5

ip = '127.0.0.1'
node_names = ['A', 'B', 'C', 'D', 'E']


def dv(node_number, table, update):
    new_table = [0,0,0,0,0]
    updated = False
    for i in range(num_of_nodes):
        if i != node_number:
            new_table[i] = min(table[i], update[i] + update[node_number])
            if new_table[i] != table[i]:
                updated = True

    return new_table, updated


def node(nodeNumber, table):
    inSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    inSocket.bind((ip, inPort[nodeNumber]))
    controller = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    controller.bind((ip, mainInPort + nodeNumber + 1))
    controller.connect((ip, mainInPort))

    old_table = [x for x in table]

    for i in range (num_of_nodes):
        if i == nodeNumber:
            pass
        elif table[i] == 0:
            table[i] = 99

    my_turn = False
    stop = False
    updated = True
    count = 0
    # while not stop:
    while not stop:
        if my_turn:
            if not updated:
                print("Updated from last DV matrix or the same? The same")
                controller.send(bytes('stale'.encode(ascii)))

            else:
                print("Updated from last DV matrix or the same? Updated")
                for i in range(num_of_nodes):
                    if 0 < table[i] < 99:
                        print()
                        print("Sending DV to node", node_names[i])

                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.bind((ip, outPort[nodeNumber] + i + (10 * count)))
                        s.connect((ip, inPort[i]))
                        s.send(bytes(table))
                        time.sleep(1)

                controller.send(bytes('done'.encode(ascii)))
                count += 1
            my_turn = False
            updated = False

        inSocket.listen(5)
        connection, (sender, port) = inSocket.accept()
        message = connection.recv(50)
        sender = int(str(port)[2])

        if sender == 5:
            message = message.decode(ascii)

            if message == 'go':
                print("Current DV matrix =", table)
                print("Last DV matrix =", old_table)
                my_turn = True

            elif message == 'stop':
                print("Node {0} DV = {1}".format(node_names[nodeNumber], table))
                stop = True

        else:
            print('node {0} received DV from {1}'.format(node_names[nodeNumber], node_names[sender]))
            old_table = [x for x in table]
            table, updated = dv(nodeNumber, table, message)

            if not updated:
                print("No change in DV at node", node_names[nodeNumber])

            else:
                print("Updating DV matrix at node", node_names[nodeNumber])
                print("New DV matrix at node {0} = {1}".format(node_names[nodeNumber], table))


    inSocket.close()
    controller.close()

    return


def network_init():

    if len(sys.argv) != 2:
        print("Incorrect number of parameters. Please run again using \"my-dvr.py [filename]\"")
        return
    # read the initial nodes table
    initial = []
    with open(sys.argv[1]) as f:
        for line in f:
            initial.append([int(x) for x in line.split()])

    # create server socket
    inSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    inSocket.bind((ip, mainInPort))

    # initiating the nodes
    nodes = [] # the threads
    stales = [] # to see if the nodes are stale
    connections = [] # server connections with every nodes
    for i in range(num_of_nodes):
        nodes.append(threading.Thread(target=node, args=(i, initial[i])))
        stales.append(False)
        connections.append(None)

    round_number = 1
    count = 0
    last_updated_round = 0
    try:
        # run the nodes
        for x in nodes:
            x.start()

        # establish connection with all the nodes
        for i in range(num_of_nodes):
            inSocket.listen(5)
            connection, (sender, port) = inSocket.accept()
            connections[(port-1) % num_of_nodes] = connection

        # go through the nodes until they're all stale
        stop = False
        while not stop:
            # count the number of stale nodes.
            num_of_stales = 0
            for i in stales:
                if i:
                    num_of_stales += 1
            if num_of_stales != num_of_nodes:
                for i in range(num_of_nodes):
                    print("-------")
                    print("Round {0}: {1}".format(round_number, node_names[i]))

                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.bind((ip, mainOutPort + i + (10 * count)))
                    s.connect((ip, inPort[i]))
                    s.send(bytes('go'.encode(ascii)))
                    s.close()

                    message = connections[i].recv(50).decode(ascii)

                    if message == 'done':
                        stales[i] = False
                        last_updated_round += 1

                    elif message == 'stale':
                        stales[i] = True

                    round_number += 1

            # if all nodes are stale, exit the loop
            else:
                stop = True

            count += 1

        print("-------")
        print("Final output:")
        # tell the nodes to stop
        for i in range(num_of_nodes):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((ip, mainOutPort + i + (10 * count)))
            s.connect((ip, inPort[i]))
            s.send(bytes('stop'.encode(ascii)))
            s.close()
            time.sleep(1)

        print("Number of rounds till convergence =", last_updated_round)
        print("-------")

    except KeyboardInterrupt:
        for x in nodes:
            x.join()
        inSocket.close()


network_init()
