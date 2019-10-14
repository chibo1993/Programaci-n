class Nodo(intercomHeredado):

    def init(self, dato=None, prox = None):
        self.dato = dato
        self.prox = prox
    def str(self):
        return str(self.dato)



