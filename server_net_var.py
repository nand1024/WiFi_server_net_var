import socket
import os.path
import datetime

debug_info_enable = False
set_only_local = True



def log_update(log_message):
    max_records = 100
    log_file = "./log.txt"
    list_records = list()
    buff = ""
    if log_message is None or log_message == "":
        return
    log_message = log_message.replace("\n", " ")
    if os.path.exists(log_file):
        try:
            with open("log.txt", "rt") as f:
                for rec in f:
                    list_records.append(rec)
        except Exception as e:
            return
    if len(list_records) > max_records:
        list_records = list_records[-max_records:]
    now = datetime.datetime.now()
    buff = f"{now.day}:{now.month}:{now.year} {now.hour}:{now.minute}:{now.second} {log_message}\n"
    buff = f"{now.day:02d}:{now.month:02d}:{now.year:04d} {now.hour:02d}:{now.minute:02d}:{now.second:02d} {log_message}\n"
    list_records.append(buff)
    try:
        with open("log.txt", "wt") as f:
            for rec in list_records:
                f.write(f"{rec}")
    except Exception as e:
        return



def debug_info(debug_data):
    if debug_info_enable:
        print(debug_data)



def get_var_and_value(raw_data):
    res = []
    shablon = ["var=", "#", "val=", "$"]
    len_shablon_tegs = [len(shablon[0]), len(shablon[1]), len(shablon[2]), len(shablon[3]), ]
    len_raw_data = len(raw_data)
    index_start = 0
    while index_start < len_raw_data:
        index_var = raw_data.find(shablon[0], index_start)
        index_separate = raw_data.find(shablon[1], index_start)
        index_value = raw_data.find(shablon[2], index_start)
        index_end = raw_data.find(shablon[3], index_start)
        #if index_end < 0:
            #index_end = len_raw_data
        if not (index_var < index_separate < index_value < index_end): #перевірка порядку слідування 1)var 2)# 3)val 4)$
            return []
        if  index_separate - (index_var + len_shablon_tegs[0]) == 0 or index_end - (index_value + len_shablon_tegs[2]) == 0: # перевірка чи пусте значення поля var і поля val
            return []
        var = raw_data[index_var + len_shablon_tegs[0]:index_separate]
        val = raw_data[index_value + len_shablon_tegs[2]:index_end]
        res.append([var, val])
        index_start = index_end + 1
    return res



def update_data_record(list_records, var, value):
    id_message = 0
    record = {}
    if var in list_records.keys():
        id_message = list_records[var]['id_message']
        id_message += 1
        if id_message >= 256:
            id_message = 0
    record['value'] = value
    record['id_message'] = id_message
    list_records[var] = record



def server_proc():
    shared_data = {}
    #server_ip = '127.0.0.1' #for test
    #server_ip = '192.168.1.2' #for test
    server_ip = '192.168.1.13'
    server_port = 7890
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        if server_socket is None:
            debug_info("Server: error create socket")
            return
        try:
            server_socket.bind((server_ip, server_port))
            server_socket.listen(1)
            log_update("start server")
        except Exception as e:
            log_update(f"error create general socket {e}")
            return
        while True:
            client_socket, client_address = server_socket.accept()
            if client_socket is None:
                log_update("error client socket is None")
                continue
            client_socket.settimeout(5.0)
            with client_socket:
                if set_only_local is True and not (str(client_address[0]).find('192.168.1') == 0 or str(client_address[0]) == '127.0.0.1'):
                    continue
                try:
                    data = client_socket.recv(1024)
                    recieve_message = get_var_and_value(str(data.decode()))
                    if len(recieve_message) == 0:
                        continue
                    send_buff = ""
                    for i in recieve_message:
                        var, val = i
                        if val != "?":
                            update_data_record(shared_data, var, val)
                        else:
                            if var in shared_data.keys():
                                send_buff += f"var={var}#val={shared_data[var]['value']}#id={shared_data[var]['id_message']}$"
                                #send_buff += f"var={var}#val={shared_data[var]['value']}$" #for test
                            else:
                                send_buff += f"var={var}#val=_$"
                    if not send_buff == "":
                        client_socket.send(send_buff.encode('ascii'))
                except Exception as e:
                    log_update(f"error client socket {e}")
server_proc()

