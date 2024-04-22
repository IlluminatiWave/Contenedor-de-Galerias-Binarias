import argparse, json, os, subprocess, filedate
from pathlib import Path
from PIL import Image
from datetime import datetime

def reconstruir_imagen(elemento: dict) -> None:
    '''
    Función en proceso, fallan los metadatos
    '''
    # Obtener los datos del elemento
    nombre_archivo: Path = elemento["name"]
    ruta_raw: Path = elemento["raw"]
    modo: str = elemento["mode"]
    dimensiones = tuple(elemento["properties"]["size"])
    creado: float = elemento["properties"]["created"]
    modificado: float = elemento["properties"]["modified"]
    metadata = elemento["properties"]["metadata"]
    
    # Abrir el archivo RAW y asignar los datos a la imagen
    with open(file=ruta_raw, mode="rb") as f:
        rawdata: bytes = f.read()
    
    # Crear una nueva imagen con los datos RAW
    img: Image.Image = Image.frombytes(mode=modo, size=dimensiones, data=rawdata)

    # Eliminar el archivo RAW
    os.remove(path=ruta_raw)
    
    # Guardar la imagen reconstruida
    img.save(fp=nombre_archivo)


    # Optimizar imagen
    subprocess.run(args=["oxipng", "-t", "1", "-o", "max", nombre_archivo])

    # Agregar metadatos EXIF si están disponibles
    if "exif" in metadata:
        exif_data: dict[str, any] = metadata["exif"]
        exif_bytes: bytes = json.dumps(obj=exif_data).encode(encoding='utf-8')  # Convertir el diccionario a bytes
        img.save(fp=nombre_archivo, exif=exif_bytes)

        # Agregar metadatos XMP si están disponibles
    if "XML:com.adobe.xmp" in elemento["properties"]["metadata"]:
        xmp_data = elemento["properties"]["metadata"]["XML:com.adobe.xmp"]
        xmp_bytes = xmp_data.encode('utf-8')  # Convertir la cadena a bytes
        with open(file=nombre_archivo, mode="rb+") as img_file:
            img_file.seek(0, os.SEEK_END)
            img_file.write(xmp_bytes)

    # Establecer la fecha de modificación del archivo
    fecha_modificacion: datetime = datetime.fromtimestamp(timestamp=modificado)
    file_obj = filedate.File(nombre_archivo)
    file_obj.modified = fecha_modificacion

    # Establecer la fecha de creación del archivo
    fecha_creacion: datetime = datetime.fromtimestamp(timestamp=creado)
    file_obj.created = fecha_creacion

def cargar_datos_desde_json(archivo_json: Path) -> dict:
    """
    Carga los datos de un archivo JSON y los devuelve como un diccionario.

    Args:
        archivo_json (Path): Ruta al archivo JSON.

    Returns:
        dict: Los datos del archivo JSON como un diccionario.
    """
    with open(archivo_json, 'r') as f:
        datos = json.load(f)
    return datos

def extraer_con_7z(archivo_comprimido: Path) -> None:
    """
    Extrae los archivos de un archivo comprimido utilizando 7-Zip.

    Args:
        archivo_comprimido (Path): Ruta al archivo comprimido.
    """
    # Ruta al ejecutable de 7-Zip
    ruta_7z = Path("C:/Program Files/7-Zip/7z.exe")

    # Carpeta de destino para la extracción
    carpeta_destino: Path = archivo_comprimido.parent / archivo_comprimido.stem
    carpeta_destino: Path = carpeta_destino.parent / carpeta_destino.stem

    # Parámetros para la extracción
    parametros: list[str] = [
        ruta_7z,
        "x",                            # Comando para extraer archivos
        str(archivo_comprimido), # Ruta al archivo comprimido
        f"-o{carpeta_destino}",         # Carpeta de destino para la extracción
        "-aoa",                         # Sobrescribir todos los archivos sin preguntar
        "-y",                           # Aceptar todo sin preguntar
    ]

    # Ejecutar el comando de 7-Zip para extraer los archivos
    subprocess.run(args=parametros, stdout=subprocess.DEVNULL)

def validador(archivo: Path) -> bool:
    """
    Valida si el archivo especificado existe, es un archivo y tiene la extensión .cgb/CGB.

    Args:
        archivo (Path): La ruta del archivo a validar.

    Returns:
        bool: True si el archivo es válido, False en caso contrario.
    """
    # Verificar la existencia del archivo
    if not archivo.exists():
        print("El archivo especificado no existe.")
        return False
    # Verificar que es un archivo
    elif not archivo.is_file():
        print("La ruta especificada no es un archivo.")
        return False
    # Verificar la extensión del archivo
    elif archivo.suffix.lower() != '.cgb':
        print("El archivo debe tener la extensión .cgb.")
        return False
    return True

def desempaquetar(archivo: Path) -> None:
    """
    Desempaqueta un archivo comprimido (.cgb) y reconstruye las imágenes.

    Args:
        archivo (Path): La ruta del archivo comprimido a desempaquetar.
    """
    # Verificar que la ruta sea valida para ser procesada
    if not validador(archivo=archivo):
        exit()

    # Extraer los archivos del archivo comprimido
    extraer_con_7z(archivo_comprimido=archivo)

    # Carpeta de trabajo
    carpeta: Path = archivo.parent / archivo.stem
    carpeta = carpeta.parent / carpeta.stem

    # Cargar datos desde el archivo JSON
    archivo_json: Path = carpeta / "images.json"
    archivo_json: dict[str, any] = cargar_datos_desde_json(archivo_json=archivo_json)

    # Convertir las claves "name" y "raw" a objetos Path
    for indice, elemento in enumerate(iterable=archivo_json):
        print(f"Procesando archivo {indice + 1} de {len(archivo_json) + 1}", end="\r")
        elemento["name"] = carpeta / elemento["name"]
        elemento["raw"] = carpeta / elemento["raw"]
        reconstruir_imagen(elemento=archivo_json[indice])

    # Eliminar el archivo JSON
    os.remove(path=carpeta / "images.json")

if __name__ == "__main__":
    os.system(command="cls")
    # Configura el parser de argumentos
    parser = argparse.ArgumentParser(description='Script para extraer archivos de un contenedor binario y reconstruir las imágenes de el.')
    parser.add_argument('archivo', nargs='?', help='Archivo comprimido (.cgb) a procesar')
    args: argparse.Namespace = parser.parse_args()

    if args.archivo:
        # Modo de argumento: se proporciona una carpeta en la línea de comandos
        archivo: Path = Path(args.archivo)
    else:
        # Modo interactivo: pedir al usuario que ingrese la carpeta
        archivo: Path = Path(input("Ingrese el archivo a desempaquetar: "))

    desempaquetar(archivo=archivo)