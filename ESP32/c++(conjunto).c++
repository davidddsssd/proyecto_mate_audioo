// --- INCLUDES Y DEFINICIONES ---
#include <Arduino.h>

// Pines donde conectarás los componentes
#define PIN_POT_FRECUENCIA 34 
#define PIN_POT_AMPLITUD 35
#define PIN_BOTON_REPRODUCIR 27 

// Parámetros de la onda (los que se leen y controlan el audio)
volatile float frecuencia_hz = 440.0;
volatile float amplitud = 0.5;

// Variables para control de tiempo de envío Serial
unsigned long last_serial_time = 0;
const long serial_interval = 100; // Enviar datos cada 100 milisegundos (10 veces/segundo)

// --- CONFIGURACIÓN ---
void setup() {
    // Inicializar la comunicación Serial. Ambos, ESP32 y Python, deben usar el mismo baud rate.
    Serial.begin(115200); 

    // Configuración de pines de entrada
    pinMode(PIN_BOTON_REPRODUCIR, INPUT_PULLUP);
    
    // NOTA: La lógica del DAC/I2S para generar el sonido continuaría aquí
    // (Omitida por simplicidad, pero crucial para el audio)
}

// --- BUCLE PRINCIPAL ---
void loop() {
    // 1. Lectura de Hardware (Potenciómetros)
    int valor_adc_freq = analogRead(PIN_POT_FRECUENCIA);
    int valor_adc_amp = analogRead(PIN_POT_AMPLITUD);
    
    // Mapeo Frecuencia: 20 Hz a 20000 Hz
    frecuencia_hz = map(valor_adc_freq, 0, 4095, 20, 20000); 
    
    // Mapeo Amplitud: 0.0 a 1.0 (float)
    amplitud = (float)valor_adc_amp / 4095.0;

    // 2. Control de la Tasa de Envío Serial
    // Solo envía datos si ha pasado el tiempo necesario
    if (millis() - last_serial_time >= serial_interval) {
        last_serial_time = millis();

        // 3. Formateo y Envío de Datos por Serial
        // Creamos una cadena de texto fácil de parsear
        char buffer[60];
        
        // El formato es: F=xxxx.xx,A=x.xx\n
        // Esto es robusto porque la PC sabrá exactamente dónde buscar los valores.
        // %.2f limita los floats a dos decimales.
        snprintf(buffer, sizeof(buffer), "F=%.2f,A=%.2f\n", 
                 frecuencia_hz, amplitud);

        Serial.print(buffer);
    }
    
    // NO PONER delay() si estás usando el ESP32 para generar audio. 
    // Usar 'if' condicionales como el de arriba es mejor.
}