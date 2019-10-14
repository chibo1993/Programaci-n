from intercom import Intercom
import sounddevice as sd                                                        # https://python-sounddevice.readthedocs.io
import numpy                                                                    # https://numpy.org/
import argparse                                                                 # https://docs.python.org/3/library/argparse.html
import socket
#Clases usadas para la inicialización de la prorityQueue y la excepción Emtpy, struct   # https://docs.python.org/3/library/socket.html
from queue import PriorityQueue                                                 
from queue import Empty                                                         # https://docs.python.org/3/library/queue.html
import struct

if __debug__:
    import sys

class Intercom_buffer(Intercom):

    max_packet_size = 32768 
  

    def init(self, args):
        Intercom.init(self, args)
        #Inicializo el contador. 
        self.index=0
        #Inicializo la cola de prioridad, tamaño bastante grande pero he respetado el que estaba en la clase padre. 
        self.priorityQ = PriorityQueue(maxsize=100000)

    def run(self):
        
        #SENDING #Internet, 99% de los socket
        sending_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        #Para enviar y recibir se usan lo mismo "socket.socket(socket.AF_INET,#socket.SOCK_DGRAM"
        receiving_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        listening_endpoint = ("0.0.0.0", self.listening_port)
        receiving_sock.bind(listening_endpoint)
     
        def receive_and_buffer():

             """recvfrom recibe datos en un socket nombrado por el socket
             descriptor y los almacena en un búfer.  La función recvfrom ()
             se aplica a cualquier socket de datagrama, ya sea conectado o no."""
             message, source_address = receiving_sock.recvfrom(Intercom.max_packet_size)
             #Inicializo el vector. 
             msg=[]
             """struc.unpack(formato, cadena)
            Desempaquete la cadena (presumiblemente empaquetada por ) de acuerdo con el formato dado. 
            El resultado es una tupla incluso si contiene exactamente un elemento. La cadena debe contener 
            exactamente la cantidad de datos requeridos por el formato ( debe ser igual ).pack(fmt, ...)
            len(string)calcsize(fmt)"""
            #! --> red (= big-endian); 
            #H --> enteros de 16 bits 2^16= 65536 rango maximo.
            #h --> enteros de 16 bits 2^! = 2 rango minimo. 
            #H{}h los paquetes van a respetar el rango entre el máximo y el minimo. 
             index,*msg=struct.unpack("!H{}h".format(self.samples_per_chunk*self.number_of_channels),message)
             self.priorityQ.put((index, msg))

        def record_send_and_play(indata, outdata, frames, time, status):
            
            msg=numpy.frombuffer(indata, numpy.int16)
            """struc.pack(formato, v1, v2) 
             Devuelve una cadena que contiene los valores empaquetados de acuerdo con el formato dado. 
             Los argumentos deben coincidir exactamente con los valores requeridos por el formato.v1, v2"""
            msgpack=struct.pack("!H{}h".format(self.samples_per_chunk*self.number_of_channels),self.index, *msg)
            self.index+=1
                        #sendto(bytes, flags, address)
            sending_sock.sendto(msgpack, (self.destination_IP_addr, self.destination_port))
            
            try:
                #Obtengo los datos de la priority con el indice indicado.
                index, message = self.priorityQ.get()
                #Transformo los datos obtenidos, en un array de numpy. Para evitar fallos de tipo "need object". 
                message=numpy.array(message)
                #Controlamos los mensajes en silencio 
                if len(message)==0:
                    raise ValueError
            except ValueError:
                print("error")
                #Cuando el mensaje es 0
                message = numpy.zeros((self.samples_per_chunk, self.number_of_channels), self.dtype)
            except Empty:
                #Devuelve una nueva matriz de formas y tipos dados, llenos de ceros.
                message = numpy.zeros((self.samples_per_chunk, self.number_of_channels), self.dtype)
            outdata[:] = message.reshape(self.samples_per_chunk, self.number_of_channels)      
            if __debug__:
                sys.stderr.write("."); sys.stderr.flush()

        with sd.Stream(samplerate=self.samples_per_second, blocksize=self.samples_per_chunk, dtype=self.dtype, channels=self.number_of_channels, callback=record_send_and_play):
         print('-=- Press <CTRL> + <C> to quit -=-')
         while True:
            receive_and_buffer()

if __name__ == "__main__":
    intercom = Intercom_buffer()
    parser = intercom.add_args()
    args = parser.parse_args()
    intercom.init(args)
    intercom.run()