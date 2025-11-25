import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sounddevice as sd
import threading

class SimuladorOndasRealTime:
    def __init__(self, root):
        self.root = root
        self.root.title("Sintetizador Matemático en Tiempo Real (0 - 20kHz)")
        self.root.geometry("950x700")

        # --- VARIABLES DE ESTADO ---
        self.running = True
        self.audio_on = False
        self.sample_rate = 44100  # Muestras por segundo
        self.current_phase = 0    # Para mantener la continuidad de la onda

        # --- VARIABLES DE CONTROL (SLIDERS) ---
        self.var_amplitud = tk.DoubleVar(value=1.0)
        self.var_frecuencia = tk.DoubleVar(value=440.0) 
        self.var_fase = tk.DoubleVar(value=0.0)
        
        # Configuramos el cierre seguro
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

        # Iniciar Interfaz
        self.crear_interfaz()
        self.actualizar_grafico()

        # --- INICIAR EL MOTOR DE AUDIO ---
        # Iniciamos el stream en un hilo separado para no congelar la interfaz
        self.stream = sd.OutputStream(
            channels=1, 
            samplerate=self.sample_rate, 
            callback=self.audio_callback,
            blocksize=1024
        )
        self.stream.start()

    def cerrar_aplicacion(self):
        self.running = False
        self.stream.stop()
        self.stream.close()
        self.root.destroy()

    def crear_interfaz(self):
        # Panel Izquierdo
        frame_controles = ttk.LabelFrame(self.root, text="Panel de Control")
        frame_controles.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # --- CONTROL DE SONIDO ---
        self.btn_audio = ttk.Button(frame_controles, text="🔇 Sonido APAGADO", command=self.toggle_audio)
        self.btn_audio.pack(pady=15, fill=tk.X)
        ttk.Label(frame_controles, text="⚠️ Cuidado con tus oídos\nBaja el volumen del PC", 
                 foreground="red", justify="center").pack(pady=5)

        ttk.Separator(frame_controles, orient='horizontal').pack(fill='x', pady=10)

        # --- SLIDER AMPLITUD ---
        ttk.Label(frame_controles, text="Amplitud (Volumen)").pack()
        ttk.Scale(frame_controles, from_=0.0, to=1.0, 
                  variable=self.var_amplitud, command=self.actualizar_grafico).pack(fill=tk.X, padx=10, pady=5)

        # --- SLIDER FRECUENCIA (Ahora hasta 20,000 Hz) ---
        ttk.Label(frame_controles, text="Frecuencia (Hz)").pack()
        # Usamos un Scale logarítmico "falso" visualmente o simplemente lineal largo
        # Para simplificar el código, usaremos lineal, pero hasta 20k es muy sensible.
        self.scale_freq = ttk.Scale(frame_controles, from_=20, to=20000, 
                                    variable=self.var_frecuencia, command=self.actualizar_grafico)
        self.scale_freq.pack(fill=tk.X, padx=10, pady=5)

        # --- SLIDER FASE ---
        ttk.Label(frame_controles, text="Desfase (Visual)").pack()
        ttk.Scale(frame_controles, from_=-np.pi, to=np.pi, 
                  variable=self.var_fase, command=self.actualizar_grafico).pack(fill=tk.X, padx=10, pady=5)

        # Etiqueta de valor exacto
        self.lbl_valor_freq = ttk.Label(frame_controles, text="Freq: 440 Hz", font=("Arial", 12, "bold"))
        self.lbl_valor_freq.pack(pady=20)

        # Panel Derecho (Gráfico)
        frame_grafico = ttk.Frame(self.root)
        frame_grafico.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_grafico)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def toggle_audio(self):
        self.audio_on = not self.audio_on
        if self.audio_on:
            self.btn_audio.config(text="🔊 Sonido ENCENDIDO")
        else:
            self.btn_audio.config(text="🔇 Sonido APAGADO")

    def audio_callback(self, outdata, frames, time, status):
        """
        Esta función es llamada automáticamente por la tarjeta de sonido
        cientos de veces por segundo para pedir más datos.
        """
        if not self.running: return

        if self.audio_on:
            # 1. Obtenemos valores actuales de los sliders
            freq = self.var_frecuencia.get()
            amp = self.var_amplitud.get() * 0.2  # Factor 0.2 para proteger parlantes

            # 2. Generamos el vector de tiempo para este pequeño fragmento (chunk)
            # Calculamos cuánto avanza la fase en cada muestra
            # formula: 2 * pi * f / FrecuenciaMuestreo
            phase_increment = 2 * np.pi * freq / self.sample_rate
            
            # 3. Creamos el vector de fases para este bloque usando álgebra lineal
            # np.arange crea [0, 1, 2, ... frames]
            phases = self.current_phase + np.arange(frames) * phase_increment
            
            # 4. Calculamos el Seno
            outdata[:] = (amp * np.sin(phases)).reshape(-1, 1)
            
            # 5. Guardamos la última fase para que el siguiente bloque continúe suavemente
            # El operador % (módulo) mantiene el número pequeño
            self.current_phase = (self.current_phase + frames * phase_increment) % (2 * np.pi)
        else:
            # Si el audio está apagado, enviamos silencio (ceros)
            outdata[:] = np.zeros((frames, 1))

    def actualizar_grafico(self, event=None):
        # Valores para el gráfico
        A = self.var_amplitud.get()
        f = self.var_frecuencia.get()
        C = self.var_fase.get()
        
        # Actualizar etiqueta de texto
        self.lbl_valor_freq.config(text=f"Freq: {int(f)} Hz")

        # Vector de tiempo para visualización (Hacemos zoom automático)
        # Si la frecuencia es muy alta, mostramos menos tiempo para ver la onda
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

if __name__ == "__main__":
    root = tk.Tk()
    app = SimuladorOndasRealTime(root)
    root.mainloop()