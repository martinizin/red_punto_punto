import numpy as np
import math
from gnpy.core.info import create_input_spectral_information
from gnpy.core.elements import Fiber, Transceiver
from gnpy.core.utils import watt2dbm, db2lin, dbm2watt
import matplotlib.pyplot as plt

fiber_length = float(input("Introduce la longitud de la fibra en km: "))

# Parámetros de la simulación
f_min = 191.4e12  # Frecuencia mínima 
f_max = 195.1e12  # Frecuencia máxima 
spacing = 50e9    # Espaciado entre canales 
roll_off = 0.15   # Roll-off del filtro
tx_osnr = 40      # OSNR del transmisor (dB)
tx_power = 6      # Potencia del transmisor (dBm)
baud_rate = 32e9  # Tasa de baudios 
delta_pdb = 0     # Delta de potencia (dB)
slot_width = spacing  # Ancho de slot 

# Crear el objeto SpectralInformation
si = create_input_spectral_information(f_min, f_max, roll_off, baud_rate, spacing, tx_osnr, tx_power, slot_width)
si.signal = si.signal.astype(np.float64)

# Calcular número de canales
num_channels = int(np.floor((f_max - f_min) / spacing))
print(f"Frecuencia mínima: {f_min/1e12:.2f} THz")
print(f"Número de canales: {num_channels}")

# Mostrar potencia por canal en mW
power_chanel = 10**(tx_power/10)
print(f"Power de canal (mW): {power_chanel}")

# Calcular potencia total de entrada
total_input_power_w = num_channels*power_chanel
total_input_power_dbm = watt2dbm(total_input_power_w/1000)
print(f"Power total (w): {total_input_power_w}")
print(f"Power total (dBm): {total_input_power_dbm}")

# Parámetros de la fibra
fiber_params = {
    'length': fiber_length,         # Longitud de la fibra en km
    'loss_coef': 0.2,     # Coeficiente de pérdida en dB/km
    'length_units': 'km', # Unidades de longitud
    'att_in': 0,          # Atenuación en la entrada (dB)
    'con_in': 0.25,       # Conector de entrada (dB)
    'con_out': 0.30,      # Conector de salida (dB)
    'pmd_coef': 0.1,      # PMD 
    'dispersion': 16.5,   # Dispersión cromática 
    'gamma': 1.2,         # Coeficiente no lineal 
    'effective_area': 80e-12,  # Área efectiva
    'core_radius': 4.2e-6,     # Radio del núcleo en m
    'n1': 1.468,               # Índice de refracción del núcleo
    'n2': 2.6e-20              # Coeficiente no lineal
}

# Crear una fibra óptica
fiber = Fiber(uid="Fiber1", params=fiber_params)

# Calcular y mostrar la potencia antes de la fibra
power_before_fiber = watt2dbm(np.sum(si.signal/1000))

# IMPORTANTE: Establecer la potencia de referencia en la fibra
fiber.ref_pch_in_dbm = power_before_fiber

# Propagar la señal a través de la fibra
si_after_fiber = fiber(si)

# Calcular la potencia después de la fibra
power_after_fiber = watt2dbm(np.sum(si_after_fiber.signal/1000))

# Crear un receptor
trx = Transceiver(uid="Receiver")
si_received = trx(si_after_fiber)

# Calcular la potencia de la señal recibida en dBm
signal_power_watts = np.sum(si_received.signal/1000)
signal_power_dbm = watt2dbm(signal_power_watts)

# Calcular la atenuación total esperada
expec = total_input_power_dbm
fiber_att = fiber_params['loss_coef'] * fiber_params['length'] + fiber_params['con_in'] + fiber_params['con_out']
expected_power_after_fiber = expec - fiber_att

print("\nResultados:")
print(f"Potencia de la señal antes de la fibra (dBm): {power_before_fiber:.4f}")
print(f"Potencia de la señal después de la fibra (dBm): {power_after_fiber:.2f}")
print(f"Potencia de la señal recibida (dBm): {signal_power_dbm:.2f}")
print(f"\nPotencia esperada antes de la fibra (dBm): {expec:.2f}")
print(f"Atenuación esperada (dB): {fiber_att:.2f}")
print(f"Potencia esperada después de la fibra (dBm): {expected_power_after_fiber:.2f}")


# Calcular el OSNR en diferentes puntos del sistema
def calculate_osnr(signal_info):
    """Calcula el OSNR basado en la información espectral"""
    # Obtener potencia de señal y ruido en watts
    signal_power_total = np.sum(signal_info.signal)/1000  # mW a W
    noise_power_total = np.sum(signal_info.nli + signal_info.ase)/1000  # mW a W
    
    if noise_power_total == 0:
        return tx_osnr 
    
    # Calcular OSNR en dB
    osnr_db = 10 * np.log10(signal_power_total / noise_power_total)
    return osnr_db

# Inicializar valores de OSNR
osnr_values = []

# OSNR en el transmisor
osnr_tx = tx_osnr 
osnr_values.append(osnr_tx)

# OSNR antes de la fibra (igual al del transmisor)
osnr_before_fiber = osnr_tx
osnr_values.append(osnr_before_fiber)

# OSNR después de la fibra
osnr_after_fiber = calculate_osnr(si_after_fiber)
osnr_values.append(osnr_after_fiber)

# OSNR en el receptor
osnr_rx = calculate_osnr(si_received)
osnr_values.append(osnr_rx)

# Mostrar resultados de OSNR
print("\nResultados de OSNR:")
print(f"OSNR en el transmisor (dB): {osnr_tx:.2f}")
print(f"OSNR antes de la fibra (dB): {osnr_before_fiber:.2f}")
print(f"OSNR después de la fibra (dB): {osnr_after_fiber:.2f}")
print(f"OSNR en el receptor (dB): {osnr_rx:.2f}")