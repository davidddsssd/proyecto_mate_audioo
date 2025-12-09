import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sounddevice as sd
import threading
import serial
import time

class SimuladorOndasRealTime:
    def __init__(self, root):
        self.root = root
        self.root.title("Sintetizador Matemático en Tiempo Real (0 - 20kHz)")
        self.root.geometry("950x700")

        # --- VARIABLES DE ESTADO ---
        self.running = True
        self.audio_on = False
        self.sample_rate = 44100 
        self.current_phase = 0 
        self.ser = None # Inicializamos variable serial

        # --- VARIABLES DE CONTROL (SLIDERS) ---
        self.var_amplitud = tk.DoubleVar(value=1.0)
        self.var_frecuencia = tk.DoubleVar(value=440.0) 
        self.var_fase = tk.DoubleVar(value=0.0)
        
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

        self.crear_interfaz()
        #self.actualizar_grafico()

        # --- 1. CORRECCIÓN: INICIAR COMUNICACIÓN SERIAL AQUÍ ---
        # Asegúrate de cambiar 'COM3' por el puerto real que ves en Arduino IDE
        self.iniciar_comunicacion_serial('COM5') 

        # --- INICIAR EL MOTOR DE AUDIO ---
        self.stream = sd.OutputStream(
            channels=1, 
            samplerate=self.sample_rate, 
            callback=self.audio_callback,
            blocksize=1024
        )
        self.stream.start()

    def cerrar_aplicacion(self):
        self.running = False
        if self.ser: self.ser.close() # Cerrar puerto serial
        self.stream.stop()
        self.stream.close()
        self.root.destroy()

    def crear_interfaz(self):
        # (Este método queda igual que en tu código original)
        frame_controles = ttk.LabelFrame(self.root, text="Panel de Control")
        frame_controles.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        self.btn_audio = ttk.Button(frame_controles, text="🔇 Sonido APAGADO", command=self.toggle_audio)
        self.btn_audio.pack(pady=15, fill=tk.X)
        ttk.Label(frame_controles, text="⚠️ Cuidado con tus oídos\nBaja el volumen del PC", 
                 foreground="red", justify="center").pack(pady=5)
        ttk.Separator(frame_controles, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Label(frame_controles, text="Amplitud (Volumen)").pack()
        ttk.Scale(frame_controles, from_=0.0, to=1.0, 
                  variable=self.var_amplitud, command=self.actualizar_grafico).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_controles, text="Frecuencia (Hz)").pack()
        self.scale_freq = ttk.Scale(frame_controles, from_=20, to=20000, 
                                    variable=self.var_frecuencia, command=self.actualizar_grafico)
        self.scale_freq.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(frame_controles, text="Desfase (Visual)").pack()
        ttk.Scale(frame_controles, from_=-np.pi, to=np.pi, 
                  variable=self.var_fase, command=self.actualizar_grafico).pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_valor_freq = ttk.Label(frame_controles, text="Freq: 440 Hz", font=("Arial", 12, "bold"))
        self.lbl_valor_freq.pack(pady=20)
        
        frame_grafico = ttk.Frame(self.root)
        frame_grafico.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_grafico)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def set_audio_state(self, state):
        """
        Actualiza el estado de audio y el botón según lo que manda el ESP32 (state es True o False).
        """
        self.audio_on = state
        if self.audio_on:
            self.btn_audio.config(text="🔊 Sonido ENCENDIDO")
        else:
            self.btn_audio.config(text="🔇 Sonido APAGADO")

        # IMPORTANTE: También debes corregir el método toggle_audio
        # para que use esta función si haces clic manualmente.

    def toggle_audio(self):
        """
        Método llamado cuando el usuario hace clic con el ratón.
        Invierte el estado y llama a la función de actualización unificada.
        """
        new_state = not self.audio_on
        self.set_audio_state(new_state)
        # Opcional: Podrías enviar un mensaje de vuelta al ESP32 si lo necesitas

    def audio_callback(self, outdata, frames, time, status):
        if not self.running: return
        if self.audio_on:
            freq = self.var_frecuencia.get()
            amp = self.var_amplitud.get() * 0.2 
            phase_increment = 2 * np.pi * freq / self.sample_rate
            phases = self.current_phase + np.arange(frames) * phase_increment
            outdata[:] = (amp * np.sin(phases)).reshape(-1, 1)
            self.current_phase = (self.current_phase + frames * phase_increment) % (2 * np.pi)
        else:
            outdata[:] = np.zeros((frames, 1))

    def actualizar_grafico(self, event=None):
        # (Igual que tu código original)
        A = self.var_amplitud.get()
        f = self.var_frecuencia.get()
        C = self.var_fase.get()
        self.lbl_valor_freq.config(text=f"Freq: {int(f)} Hz")
        zoom = 0.02
        if f > 1000: zoom = 0.005
        if f > 5000: zoom = 0.001
        t_visual = np.linspace(0, zoom, 1000)
        B = 2 * np.pi * f
        y_visual = A * np.sin(B * t_visual + C)
        self.ax.clear()
        self.ax.plot(t_visual, y_visual, color='#007acc', linewidth=2)
        self.ax.set_title("Visualización de la Función Seno")
        self.ax.set_xlabel(f"Tiempo ({zoom} seg mostrados)")
        self.ax.set_ylabel("Amplitud")
        self.ax.grid(True, alpha=0.3)
        self.ax.set_ylim(-1.5, 1.5)
        self.canvas.draw()

    # --- CORRECCIÓN: LÓGICA DE CONEXIÓN Y LECTURA ---
    def iniciar_comunicacion_serial(self, puerto):
        try:
            self.ser = serial.Serial(puerto, 115200, timeout=1) 
            print(f"✅ Conectado a ESP32 en {puerto}")
            
            # Hilo daemon para que se cierre solo al cerrar la app
            self.serial_thread = threading.Thread(target=self.leer_datos_serial, daemon=True)
            self.serial_thread.start()
        except serial.SerialException as e:
            print(f"❌ Error al abrir puerto {puerto}: {e}")
            print("Verifica que el Monitor Serial de Arduino esté CERRADO.")

    def leer_datos_serial(self):
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    # decode('utf-8', errors='ignore') evita crasheos por bytes corruptos
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line: continue

                    # 2. CORRECCIÓN: Parsing simple para C++ que envía "F440.00"
                    if line.startswith("F"):
                        try:
                            # Quitamos la "F" y convertimos el resto a float
                            val_str = line[1:] 
                            f_nueva = float(val_str)
                            # Mandamos a actualizar la GUI
                            self.root.after(0, lambda: self.var_frecuencia.set(f_nueva))
                            self.root.after(0, self.actualizar_grafico)
                        except ValueError:
                            pass # Error de conversión, ignorar trama
                    
                    elif line.startswith("A"):
                        try:
                            val_str = line[1:]
                            a_nueva = float(val_str)
                            self.root.after(0, lambda: self.var_amplitud.set(a_nueva))
                            self.root.after(0, self.actualizar_grafico)
                        except ValueError:
                            pass

                    elif line.startswith("T"): # Toggle botón
                        if line == "T1":
                            # Llamamos a una función segura para actualizar la GUI
                            self.root.after(0, lambda: self.set_audio_state(True))
                        elif line == "T0":
                            self.root.after(0, lambda: self.set_audio_state(False))

            except Exception as e:
                print(f"Error en hilo serial: {e}")
                time.sleep(0.1)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimuladorOndasRealTime(root)
    root.mainloop()