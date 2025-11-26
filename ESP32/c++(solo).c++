// --- 1. INCLUDES Y DEFINICIONES ---
#include <Arduino.h>
#include <driver/dac.h> // O <driver/i2s.h> si usas un chip de audio I2S

// Pines donde conectarás los componentes
#define PIN_POT_FRECUENCIA 34 // ADC1_CH6
#define PIN_POT_AMPLITUD 35 // ADC1_CH7
#define PIN_BOTON_REPRODUCIR 27 // GPIO para el botón

// Parámetros de la onda
volatile float frecuencia_hz = 440.0;
volatile float amplitud = 0.5;
volatile bool reproduciendo = false;
volatile float fase_actual = 0.0;

// Parámetros de audio
const int SAMPLE_RATE = 44100;
const float DOS_PI = 6.283185307;

// --- 2. GENERADOR DE ONDA EN TIEMPO REAL (ISR o Tarea I2S/Timer) ---
// *Dependiendo del método (DAC simple o I2S), esta función es un poco diferente.*
// Usaremos un timer o una interrupción para asegurar el ritmo.
void generar_audio_muestra() {
    // 1. Calcular el incremento de fase
    float phase_increment = DOS_PI * frecuencia_hz / SAMPLE_RATE;

    // 2. Generar la muestra (Función Seno)
    // Se usa 'sinf' para float en lugar de 'sin' para double
    float sample_float = amplitud * sinf(fase_actual);

    // 3. Mapear a un valor de 8 bits (0-255) para el DAC interno
    // El DAC del ESP32 solo tiene 8 bits. Si usas I2S, usas 16 bits.
    int sample_dac = (int)((sample_float + 1.0) * 127.5);

    // 4. Escribir la muestra (Si el botón está presionado)
    if (reproduciendo) {
        // Ejemplo para el DAC del ESP32, pin GPIO 25 o 26
        dac_output_voltage(DAC_CHANNEL_1, sample_dac);
    } else {
        // Silencio
        dac_output_voltage(DAC_CHANNEL_1, 127); // 127 es el punto medio (cero)
    }
    
    // 5. Actualizar la fase
    fase_actual += phase_increment;
    if (fase_actual >= DOS_PI) {
        fase_actual -= DOS_PI;
    }
}


// --- 3. FUNCIÓN DE CONFIGURACIÓN (SETUP) ---
void setup() {
    Serial.begin(115200);

    // Configuración de pines de entrada (Potenciómetros y botón)
    pinMode(PIN_BOTON_REPRODUCIR, INPUT_PULLUP);

    // Configuración del DAC interno del ESP32 (Simple)
    dac_output_enable(DAC_CHANNEL_1); 
    
    // Configurar un Timer para llamar a generar_audio_muestra() 44100 veces por segundo
    // (Esto es el 'corazón' del audio en tiempo real)
    // ... Código para configurar el Timer ...
    // El timer llamará periódicamente a 'generar_audio_muestra'
}


// --- 4. BUCLE PRINCIPAL (LOOP) ---
void loop() {
    // 1. Leer Potenciómetros (ADC)
    int valor_adc_freq = analogRead(PIN_POT_FRECUENCIA);
    int valor_adc_amp = analogRead(PIN_POT_AMPLITUD);

    // 2. Mapear ADC (0-4095) a Frecuencia y Amplitud
    // Mapeo Frecuencia: 20 Hz a 20000 Hz
    frecuencia_hz = map(valor_adc_freq, 0, 4095, 20, 20000); 
    
    // Mapeo Amplitud: 0.0 a 1.0 (float)
    amplitud = (float)valor_adc_amp / 4095.0;

    // 3. Leer Botón
    if (digitalRead(PIN_BOTON_REPRODUCIR) == LOW) { // LOW si se usa INPUT_PULLUP
        reproduciendo = true;
    } else {
        reproduciendo = false;
    }

    // Opcional: Mostrar valores por serial para depuración
    // Serial.printf("F: %f Hz | A: %f\n", frecuencia_hz, amplitud);

    delay(10); // Pausa para no saturar el loop de lectura
}