import argparse, hashlib, json, os, re, subprocess
from pathlib import Path
from PIL import ExifTags, Image
from typing import List, Dict, Any


def comprimir_con_7z(elementos: List[Path]) -> None:
	"""
	Comprime los elementos utilizando 7-Zip.

	Args:
		elementos (List[Path]): Lista de rutas de archivos a comprimir.
	"""
	# Ruta al ejecutable de 7-Zip
	ruta_7z = Path("C:/Program Files/7-Zip/7z.exe")

	# Ruta para el archivo comprimido
	ruta_comprimido = elementos[0].parent / f"{elementos[0].parent.name}.7z.cgb"

	# Parámetros para la compresión
	parametros: List[str] = [
		str(object=ruta_7z),
		"a",							# Comando para añadir archivos a un archivo comprimido
		str(object=ruta_comprimido),	# Ruta al archivo comprimido de salida
	]

	# Agrega las rutas de los elementos a comprimir a los parámetros
	for elemento in elementos:
		parametros.append(str(object=elemento.resolve()))

	# Agrega los parámetros adicionales
	parametros.extend([
		"-t7z",							# Formato de archivo 7z
		"-mx9",							# Nivel de compresión máximo (Ultra)
		"-m0=lzma2",					# Modo LZMA2
		"-mfb=273",						# Tamaño de palabra
		"-md=1536m",					# Diccionario de 1536 MB
		"-ms=on",						# Tamaño de bloque sólido (compacto)
		"-mtm=off",						# No guardar las fechas de los archivos
		"-mta=off",						# No guardar las propiedades NTFS
		"-sdel",						# Eliminar archivos después de la compresión
	])

	# Ejecutar el comando de 7-Zip
	subprocess.run(args=parametros)

def procesar_imagen(imagen: Path, Raw: Path) -> Dict[str, Any]:
	"""
	Procesa una imagen dada y guarda el contenido de rawdata en un archivo RAW especificado.

	Args:
		imagen (Path): La ruta de la imagen a procesar.
		Raw (Path): La ruta donde se guardará el archivo RAW.

	Returns:
		dict: Un diccionario que contiene todas las propiedades de la imagen procesada.
	"""
	propiedades: dict = {}

	# Abre la imagen y extrae el rawdata
	with Image.open(fp=imagen) as img:
		rawdata: bytes = img.tobytes()

		# Guarda el contenido de rawdata en el archivo RAW
		with open(file=Raw, mode='wb') as f:
			f.write(rawdata)

		# Obtiene las propiedades de la imagen
		propiedades["name"] = imagen.name
		propiedades["mode"] = img.mode
		propiedades["raw"] = Raw.name
		propiedades["properties"] = {
			"created": imagen.stat().st_birthtime,
			"modified": imagen.stat().st_mtime,
			"hash_pixel": hashlib.sha256(rawdata).hexdigest(),
			"size": img.size,
			"metadata": img.info
		}

		# Verifica si los datos EXIF están en formato bytes
		exif_bytes: Any = propiedades["properties"]["metadata"].get("exif", b"")
		if isinstance(exif_bytes, bytes):
			# Decodifica los bytes de los metadatos EXIF y convierte los IFDRational a cadenas
			exif_info: dict = img._getexif()  # Obtiene los metadatos EXIF
			exif_data: dict = {}

			if exif_info:
				# Inicializa un diccionario para almacenar los metadatos EXIF decodificados
				exif_data: dict = {}
				for tag, value in exif_info.items():
					# Decodifica el nombre del tag utilizando los TAGS de PIL.ExifTags
					tag_name: str = ExifTags.TAGS.get(tag, tag)
					# Si el valor es un identificador de EXIF codificado en bytes, lo decodifica a UTF-8
					if isinstance(value, bytes):
						try:
							value: str = value.decode(encoding="utf-8")  # Intenta decodificar a UTF-8
						except UnicodeDecodeError:
							pass  # Si la decodificación falla, deja el valor como está
					elif isinstance(value, tuple) and len(value) == 2:
						# Si el valor es un IFDRational, conviértelo a una cadena
						value = f"{value[0]}/{value[1]}"
					# Agrega el tag y su valor decodificado al diccionario de metadatos EXIF
					exif_data[tag_name] = value
					if "XResolution" in exif_data:
						# Convierte XResolution a una cadena
						exif_data["XResolution"] = str(exif_data["XResolution"])
					if "YResolution" in exif_data:
						# Convierte YResolution a una cadena
						exif_data["YResolution"] = str(exif_data["YResolution"])
			else:
				exif_data: dict = {}

			# Actualiza los metadatos EXIF en el diccionario de propiedades
			propiedades["properties"]["metadata"]["exif"] = exif_data
			
	return propiedades

def guardar_propiedades_imagenes(lista_imagenes: List[Path]) -> List[Path]:
	"""
	Guarda las propiedades de las imágenes en un archivo JSON y retorna una lista de rutas de archivos RAW.

	Args:
		lista_imagenes (List[Path]): Lista de rutas de archivos de imagen.

	Returns:
		List[Path]: Lista de rutas de archivos RAW generados.
	"""
	# Crea una lista para contener las propiedades de todas las imágenes
	imagenes_propiedades: List[Dict[str, Any]] = []
	imagenjson: Path = lista_imagenes[0].parent / 'images.json'
	lista_rutas_raw: List[Path] = [imagenjson]

	# Itera sobre la lista de imágenes
	for i, imagen in enumerate(iterable=lista_imagenes):
		print(f"procesando imagen {i + 1} de {len(lista_imagenes) + 1}", end ="\r")
		# Genera el nombre del archivo RAW basado en el índice
		ruta_raw: Path = imagen.parent / f"{i+1}.raw"
		lista_rutas_raw.append(ruta_raw)

		# Procesa la imagen y guarda sus propiedades
		propiedades: Dict[str, Any] = procesar_imagen(imagen=imagen, Raw=ruta_raw)

		# Agrega las propiedades a la lista
		imagenes_propiedades.append(propiedades)

	# Guarda la lista de propiedades en un archivo JSON
	with open(file=imagenjson, mode='w') as fp:
		json.dump(obj=imagenes_propiedades, fp=fp, indent=4)

	return lista_rutas_raw

def escanear_carpeta(carpeta: Path) -> List[Path]:
	"""
	Escanea una carpeta en busca de archivos de imagen.

	Args:
		carpeta (Path): La ruta de la carpeta a escanear.

	Returns:
		List[Path]: Una lista de rutas de archivos de imagen encontrados en la carpeta.
	"""
	lista_imagenes: List[Path] = []
	
	# Escanea la carpeta y filtra solo los archivos de imagen
	for archivo in carpeta.glob(pattern='*'):
		if archivo.is_file() and archivo.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
			lista_imagenes.append(archivo)

	# Ordenamos la lista de archivos como lo haría Windows
	lista_imagenes.sort(key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(pattern=r'(\d+)', string=x.stem)])
	
	return lista_imagenes

def validador(carpeta: Path) -> bool:
	"""
	Valida si la carpeta especificada existe y es una carpeta válida.

	Args:
		carpeta (Path): La ruta de la carpeta a validar.

	Returns:
		bool: True si la carpeta es válida, False de lo contrario.
	"""
	if not carpeta.exists():
		print("La carpeta especificada no existe.")
		return False
	if not carpeta.is_dir():
		print("La ruta especificada no es una carpeta.")
		return False
	return True

def empaquetar(carpeta: Path) -> None:
	"""
	Empaqueta los archivos de imagen en la carpeta especificada.

	Args:
		carpeta (Path): La ruta de la carpeta que contiene los archivos de imagen a empaquetar.
	"""
	# Verificar que la ruta sea valida para ser procesada
	if not validador(carpeta=carpeta):
		exit()

	# Escanea la carpeta y obtiene la lista de imágenes
	lista_imagenes: List[Path] = escanear_carpeta(carpeta=carpeta)

	# Guarda las propiedades de las imágenes en images.json
	lista_archivos_a_comprimir: List[Path] = guardar_propiedades_imagenes(lista_imagenes=lista_imagenes)

	# Comprime los archivos utilizando 7-Zip
	comprimir_con_7z(elementos=lista_archivos_a_comprimir)

if __name__ == "__main__":
	os.system(command="cls")
    # Configura el parser de argumentos
	parser = argparse.ArgumentParser(description='Script para escanear una carpeta, guardar propiedades de imágenes y comprimir archivos.')
	parser.add_argument('carpeta', nargs='?', help='Carpeta a escanear')
	args: argparse.Namespace = parser.parse_args()

	if args.carpeta:
		# Modo de argumento: se proporciona una carpeta en la línea de comandos
		carpeta = Path(args.carpeta)
	else:
		# Modo interactivo: pedir al usuario que ingrese la carpeta
		carpeta = Path(input("Ingrese la carpeta a escanear: "))
	
	empaquetar(carpeta=carpeta)