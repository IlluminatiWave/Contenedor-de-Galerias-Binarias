import os
from pathlib import Path

# Funciones de empaquetado y desempaquetado
from Desempaquetador import desempaquetar
from Empaquetador import empaquetar

def main():
    os.system('cls')  # Limpiar la pantalla de la consola

    # Mostrar opciones al usuario
    print("¿Qué desea hacer?")
    print("1. Empaquetar un archivo")
    print("2. Desempaquetar un archivo")

    # Pedir opción al usuario
    opcion: str = input("Ingrese el número de la opción deseada: ")

    if opcion == "1":
        # Empaquetar un archivo
        archivo_a_empaquetar = Path(input("Ingrese la ruta del archivo a empaquetar: "))
        empaquetar(archivo=archivo_a_empaquetar)
    elif opcion == "2":
        # Desempaquetar un archivo
        archivo_a_desempaquetar = Path(input("Ingrese la ruta del archivo a desempaquetar: "))
        desempaquetar(archivo=archivo_a_desempaquetar)
    else:
        print("Opción no válida.")

if __name__ == "__main__":
    main()
