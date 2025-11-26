# ... (dentro de tu clase SimuladorOndasRealTime) ...
import serial
import time
import re # Para expresiones regulares, facilita el parsing

def iniciar_comunicacion_serial(self):
    # Configurar la conexión Serial
    # IMPORTANTE: Reemplaza 'COM3' por el puerto de tu ESP32 (ej. '/dev/ttyUSB0' en Linux)
    # El baud rate debe coincidir con el del ESP32 (115200)
    try:
        self.ser = serial.Serial('COM3', 115200, timeout=1) 
        print("Conexión Serial con ESP32 iniciada.")
        
        # Iniciar el hilo de lectura
        self.serial_thread = threading.Thread(target=self.leer_datos_serial)
        self.serial_thread.daemon = True # El hilo muere cuando la app principal muere
        self.serial_thread.start()
    except serial.SerialException as e:
        print(f"Error al abrir el puerto Serial: {e}")
        self.ser = None

def leer_datos_serial(self):
    if not self.ser: return

    while self.running:
        try:
            # Leer una línea completa terminada por '\n'
            line = self.ser.readline().decode('utf-8').strip() 
            
            if line:
                # Usar expresiones regulares para extraer F y A
                # Patrón: F=float,A=float
                match = re.search(r"F=(\d+\.?\d*),A=(\d+\.?\d*)", line)
                
                if match:
                    # El ESP32 es el que manda, así que actualizamos las variables
                    f_nueva = float(match.group(1))
                    a_nueva = float(match.group(2))
                    
                    # Actualizar las variables de control de Tkinter
                    # Esto debe hacerse de forma segura en el hilo principal de Tkinter:
                    self.root.after(0, self.actualizar_variables_tk, f_nueva, a_nueva)
                # else: print(f"Línea no parseada: {line}") # Para depuración

        except Exception as e:
            # print(f"Error en lectura Serial: {e}")
            time.sleep(0.1) # Esperar un poco antes de reintentar

def actualizar_variables_tk(self, f, a):
    # Función llamada en el hilo principal de Tkinter
    self.var_frecuencia.set(f)
    self.var_amplitud.set(a)
    self.actualizar_grafico() # Redibujar la onda con los nuevos valores