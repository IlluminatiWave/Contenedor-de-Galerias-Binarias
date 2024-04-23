import argparse, exifread, io, os, struct
from pathlib import Path
from typing import Dict, List

def leer_chunks_png(bytes_imagen: bytes) -> List[Dict]:
    """Lee los chunks de un archivo PNG y los devuelve como una lista de diccionarios."""
    chunks: List[dict] = []

    # Inicializar el índice de lectura
    indice: int = 8  # El primer chunk comienza después de los primeros 8 bytes del archivo PNG

    while indice < len(bytes_imagen):
        # Leer el tamaño del chunk
        longitud, = struct.unpack('>I', bytes_imagen[indice:indice+4])
        indice += 4

        # Leer el tipo del chunk
        tipo_chunk: bytes = bytes_imagen[indice:indice+4]

        # Leer los datos del chunk
        datos_chunk: bytes = bytes_imagen[indice+4:indice+4+longitud]

        # Leer el CRC
        crc, = struct.unpack('>I', bytes_imagen[indice+4+longitud:indice+4+longitud+4])
        indice += 4 + longitud + 4

        # Guardar la información del chunk en un diccionario
        info_chunk: dict[str, bytes] = {
            "Tipo de Chunk": tipo_chunk,
            "Longitud": longitud,
            "Datos del Chunk": datos_chunk,
            "CRC": crc
        }
        chunks.append(info_chunk)

    return chunks

def imprimir_chunk_IHDR(datos_chunk) -> None:
    """Imprime los datos del chunk IHDR."""
    ancho, alto, profundidad_bits, tipo_color, metodo_compresion, metodo_filtro, metodo_entrelazado = struct.unpack('>IIBBBBB', datos_chunk[:13])

    print("\033[93mDatos de IHDR:\033[0m")
    print("\t\033[94mAncho:\033[0m", f"\033[92m{ancho}\033[0m")
    print("\t\033[94mAlto:\033[0m", f"\033[92m{alto}\033[0m")
    print("\t\033[94mProfundidad de bits:\033[0m", f"\033[92m{profundidad_bits}\033[0m")
    print("\t\033[94mTipo de color:\033[0m", f"\033[92m{tipo_color}\033[0m")
    print("\t\033[94mMétodo de compresión:\033[0m", f"\033[92m{metodo_compresion}\033[0m")
    print("\t\033[94mMétodo de filtro:\033[0m", f"\033[92m{metodo_filtro}\033[0m")
    print("\t\033[94mMétodo de entrelazado:\033[0m", f"\033[92m{metodo_entrelazado}\033[0m")

def imprimir_chunk_sRGB(datos_chunk) -> None:
    """Imprime los datos del chunk sRGB."""
    correccion_gamma: bytes = datos_chunk[0]
    if correccion_gamma == 0:
        print("Sin corrección gamma (lineal)")
    elif correccion_gamma == 1:
        print("Se aplicó corrección gamma sRGB")
    else:
        print("Tipo de corrección gamma desconocido:", correccion_gamma)

def imprimir_chunk_eXIf(datos_chunk) -> None:
    """Imprime las etiquetas EXIF."""
    flujo_archivo = io.BytesIO(initial_bytes=datos_chunk)
    etiquetas_exif: Dict[str, any] = exifread.process_file(fh=flujo_archivo)
    
    print("\033[93mEtiquetas EXIF:\033[0m")
    for etiqueta, valor in etiquetas_exif.items():
        print(f"\t\033[94m{etiqueta}:\033[0m", f"\033[92m{valor}\033[0m")

def imprimir_chunk_pHYs(datos_chunk) -> None:
    """Imprime los datos del chunk pHYs."""
    if len(datos_chunk) != 9:
        print("Error: Longitud de datos de chunk pHYs inválida.")
        return
    
    pixeles_por_unidad_x: int = int.from_bytes(bytes=datos_chunk[:4], byteorder='big')
    pixeles_por_unidad_y: int = int.from_bytes(bytes=datos_chunk[4:8], byteorder='big')
    especificador_unidad: bytes = datos_chunk[8]
    
    if especificador_unidad == 0:
        unidad = "Píxeles por metro (ppm)"
        unidad_pixel = "metro"
    elif especificador_unidad == 1:
        unidad = "Píxeles por pulgada (ppi)"
        unidad_pixel = "pulgada"
    else:
        unidad = "Desconocido"

    print(f"\033[96mPíxeles por {unidad_pixel}, eje X:\033[0m", f"\033[92m{pixeles_por_unidad_x}\033[0m")
    print(f"\033[96mPíxeles por {unidad_pixel}, eje Y:\033[0m", f"\033[92m{pixeles_por_unidad_y}\033[0m")
    print("\033[96mEspecificador de unidad:\033[0m", f"\033[92m{unidad}\033[0m")

def imprimir_chunk_iTXt(datos_chunk) -> None:
    """Imprime los datos del chunk iTXt."""
    try:
        texto_decodificado = datos_chunk.decode('utf-8')
        print("\033[33mTexto Decodificado:\033[0m\n", "\033[93m" + texto_decodificado + "\033[0m")
    except UnicodeDecodeError:
        print("\033[91mError: No se puede decodificar los datos del chunk como UTF-8.\033[0m")

def imprimir_chunks(chunks) -> None:
    """Imprime todos los chunks."""
    for chunk in chunks:
        tipo_chunk: any = chunk["Tipo de Chunk"]
        print("\033[96mTipo de Chunk:\033[0m", "\033[92m" + str(object=tipo_chunk) + "\033[0m")
        print("\033[96mLongitud:\033[0m", "\033[92m" + str(object=chunk["Longitud"]) + "\033[0m")

        nombre_funcion: str = f"imprimir_chunk_{tipo_chunk.decode('ascii')}"  # Decodifica el tipo de chunk a una cadena ASCII
        if nombre_funcion in globals():
            # Llamar a la función específica si está definida
            globals()[nombre_funcion](chunk["Datos del Chunk"])
        else:
            # Si no hay una función definida para este tipo de chunk, imprimir genéricamente
            print("\033[96mDatos del Chunk (hex):\033[0m", "\n\033[92m" + (chunk["Datos del Chunk"][:256].hex() if chunk["Longitud"] > 256 else chunk["Datos del Chunk"].hex()) + "\033[0m")

        print("\033[91mCRC:\033[0m", "\033[91m" + str(object=chunk["CRC"]) + "\033[0m\n")

def validador(ruta: Path) -> bool:
    """Valida si el archivo es un PNG."""
    # Verificar si la ruta existe
    if not ruta.exists:
        print("\033[91mError: La ruta no existe.\033[0m")
        return False
    # Verificar si la ruta corresponde a un archivo
    if not ruta.is_file():
        print("\033[91mError: La ruta no corresponde a un archivo.\033[0m")
        return False

    # Leer los primeros bytes para verificar la firma de un archivo PNG
    with open(file=ruta, mode='rb') as f:
        signature: bytes = f.read(8)
        png_signature = b'\x89PNG\r\n\x1a\n'
        if signature != png_signature:
            print("\033[91mError: El archivo no es una imagen PNG.\033[0m")
            return False

    return True

def tester(ruta: Path) -> None:
    """Función de prueba que valida la ruta antes de procesarla."""
    # Validar la ruta antes de procesarla
    if not validador(ruta=ruta):
        exit()
    
    # Leer el contenido del archivo
    with open(file=ruta, mode='rb') as f:
        bytes_imagen: bytes = f.read()

    # Obtener la información de los chunks del archivo PNG
    chunks: list[dict] = leer_chunks_png(bytes_imagen=bytes_imagen)

    # Imprimir la información de los chunks
    imprimir_chunks(chunks=chunks)

if __name__ == "__main__":
    # Crear el parser de argumentos
    parser = argparse.ArgumentParser(description='Procesa un archivo PNG y muestra información de sus chunks.')
    parser.add_argument('archivo', nargs='?', help='Ruta al archivo PNG a procesar')
    args: argparse.Namespace = parser.parse_args()

    if args.archivo:
        # Si se proporciona un archivo como argumento, convertirlo en una ruta
        ruta = Path(args.archivo)
    else:
        # Si no se proporciona ningún archivo, solicitar al usuario la ruta de la imagen
        os.system(command='cls' if os.name == 'nt' else 'clear')
        ruta = Path(input("Introduce la ruta de la imagen PNG: "))

    # Llamar a la función tester con la ruta del archivo como argumento
    tester(ruta=ruta)
