import argparse, exifread, io, os, struct, zlib
from pathlib import Path
from typing import Dict, List

def colorHEX(hex_color: str) -> str:
	"""Devuelve un color de consola al recibir una secuencia RGB."""
	# Convertir el código hexadecimal a RGB
	r = int(hex_color[0:2], 16)
	g = int(hex_color[2:4], 16)
	b = int(hex_color[4:6], 16)
	bg_index: int
	
	# Verificar si la distancia entre los componentes es menor a 32
	if abs(r - g) <= 32 and abs(g - b) <= 32 and abs(r - b) <= 32:
		# Calcular la media de los componentes RGB
		avg_rgb: int = (r + g + b) // 3
		
		# Asignar un color de fondo
		if avg_rgb == 0:									# Si el color es negro puro
			bg_index = 232									# Fondo negro
		elif avg_rgb > 0 and avg_rgb < 241:					# Si el color es una escala de grises
			bg_index = int((avg_rgb / 255) * 24) + 232	# Escalar la media al rango de 232 a 255
		else:												# Si el color es blanco puro o más allá
			bg_index = 231									# Fondo blanco  
	else:													# Devolver el color RGB representativo
		bg_index = 16 + (36 * (r // 51)) + (6 * (g // 51)) + (b // 51)

	return f"\033[48;5;{bg_index}m"

def colorizar(valor: any) -> str:
	"""Colorea el texto de verde si está presente, rojo si no."""
	if valor:
		return "\033[1;32m" + str(valor) + "\033[0m"  # Verde si está presente
	else:
		return "\033[1;31m(No presente)\033[0m"  # Rojo si no está presente

def imprimir_chunk_iCCP(datos_chunk) -> None:
	"""Imprime los datos del chunk iCCP."""
	# Separar los campos utilizando el byte nulo como separador
	campos: list = datos_chunk.split(b'\x00')
	
	# Decodificar los campos y asignar a variables
	keyword: str = campos[0].decode('utf-8')
	compression_method: str = campos[1].decode('utf-8')
	compressed_text: bytes = campos[2]
	
	# Imprimir los campos con colores
	print("\t\033[33mKeyword:\033[0m", "\033[1;33m" + keyword + "\033[0m")
	print("\t\033[33mCompression Method:\033[0m", colorizar(valor=compression_method))
	print(f"\t\033[33mCompressed Text:\033[0m\n{colorizar(valor=compressed_text.hex())}")

def imprimir_chunk_acTL(datos_chunk) -> None:
	"""Imprime los datos del chunk fcTL."""
	# Verificar la longitud de los datos del chunk
	if len(datos_chunk) != 8:
		print("Longitud de datos de chunk acTL no válida.")
		return
	
	# Decodificar los datos del chunk
	numero_fotogramas, numero_repeticiones = struct.unpack('>II', datos_chunk)
	
	# Imprimir los datos decodificados
	print("\033[93mDatos de acTL:\033[0m")
	print("\t\033[94mNúmero de fotogramas:\033[0m", f"\033[92m{numero_fotogramas}\033[0m")
	print("\t\033[94mNúmero de repeticiones:\033[0m", f"\033[92m{numero_repeticiones}\033[0m")

def imprimir_chunk_fcTL(chunk_data) -> None:
	"""Imprime los datos del chunk fcTL."""
	# Verificar la longitud del chunk
	if len(chunk_data) != 26:
		print("\033[91mError: Longitud de datos de chunk fcTL no válida.\033[0m")
		return

	# Imprimir los datos del chunk fcTL
	print("\033[93mDatos del fotograma:\033[0m")
	print("\t\033[94mNúmero de secuencia:\033[0m", f"\033[92m{int.from_bytes(bytes=chunk_data[0:4], byteorder='big')}\033[0m")
	print("\t\033[94mAncho:\033[0m", f"\033[92m{int.from_bytes(bytes=chunk_data[4:8], byteorder='big')}\033[0m")
	print("\t\033[94mAlto:\033[0m", f"\033[92m{int.from_bytes(bytes=chunk_data[8:12], byteorder='big')}\033[0m")
	print("\t\033[94mDesplazamiento X:\033[0m", f"\033[92m{int.from_bytes(bytes=chunk_data[12:16], byteorder='big')}\033[0m")
	print("\t\033[94mDesplazamiento Y:\033[0m", f"\033[92m{int.from_bytes(bytes=chunk_data[16:20], byteorder='big')}\033[0m")
	print("\t\033[94mDivisor de retardo:\033[0m", f"\033[92m{int.from_bytes(bytes=chunk_data[20:22], byteorder='big')}/{int.from_bytes(bytes=chunk_data[22:24], byteorder='big')}\033[0m")
	print("\t\033[94mOperación de eliminación:\033[0m", f"\033[92m{chunk_data[24]}\033[0m")
	print("\t\033[94mOperación de fusión:\033[0m", f"\033[92m{chunk_data[25]}\033[0m")

def imprimir_chunk_PLTE(datos_chunk) -> None:
	"""Imprime los datos del chunk PLTE."""
	# Verificar si la longitud de los datos es correcta
	if len(datos_chunk) % 3 != 0:
		print("\033[91mError: Longitud de datos de chunk PLTE inválida.\033[0m")
		return
	
	# Dividir los datos en grupos de tres bytes (RGB)
	colores: List[str] = [datos_chunk[i:i+3].hex().upper() for i in range(0, len(datos_chunk), 3)]
	
	print("\033[93mPaleta de Colores (PLTE):\033[0m")
	for i, color in enumerate(colores, start=1):
		print(f"\t\033[94mColor {i}\033[0m","\033[97m\033[1m:\033[0m", f"{colorHEX(hex_color=color)}# {color} \033[0m")

def imprimir_chunk_zTXt(datos_chunk) -> None:
	"""Imprime los datos del chunk zTXt."""
	# Separar los campos utilizando el byte nulo como separador
	campos: list = datos_chunk.split(b'\x00')
	
	# Decodificar los campos y asignar a variables
	keyword: str = campos[0].decode('utf-8')
	compression_method: str = campos[1].decode('utf-8')
	compressed_text = campos[2]
	
	# Imprimir los campos con colores
	print("\t\033[33mKeyword:\033[0m", "\033[1;33m" + keyword + "\033[0m")
	print("\t\033[33mCompression Method:\033[0m", colorizar(valor=compression_method))
	print(f"\t\033[33mCompressed Text:\033[0m\n{colorizar(valor=compressed_text.hex())}")

def imprimir_chunk_iTXt(datos_chunk) -> None:
	"""Imprime los datos del chunk iTXt."""
	# Separar los campos utilizando el byte nulo como separador
	campos: list = datos_chunk.split(b'\x00')
	
	# Decodificar los campos y asignar a variables
	keyword: str = campos[0].decode('utf-8')
	compression_flag: str = campos[1].decode('utf-8')
	compression_method: str = campos[2].decode('utf-8')
	language_tag: str = campos[3].decode('utf-8')
	translated_keyword: str = campos[4].decode('utf-8')
	texto: str = campos[5].decode('utf-8')

	# Imprimir los campos con colores
	print("\t\033[33mKeyword:\033[0m", "\033[1;33m" + keyword + "\033[0m")
	print("\t\033[33mCompression Flag:\033[0m", colorizar(valor=compression_flag))
	print("\t\033[33mCompression Method:\033[0m", colorizar(valor=compression_method))
	print("\t\033[33mLanguage Tag:\033[0m", colorizar(valor=language_tag))
	print("\t\033[33mTranslated Keyword:\033[0m", colorizar(valor=translated_keyword))
	print(f"\t\033[33mText:\033[0m\n{colorizar(valor=texto)}")

def imprimir_chunk_tEXt(datos_chunk) -> None:
	"""Imprime los datos del chunk tEXt."""
	# Decodificar los datos del chunk
	datos_decodificados = datos_chunk.decode('utf-8')
	
	# Buscar el índice del primer byte nulo (separador)
	separador_idx = datos_decodificados.find('\x00')
	
	if separador_idx != -1:
		# Extraer la keyword y el texto
		keyword = datos_decodificados[:separador_idx]
		texto = datos_decodificados[separador_idx + 1:]
		
		# Imprimir la clave y el texto con formato de color
		print("\t\033[33m" + keyword + "\033[0m", "\033[97m\033[1m:\033[0m", "\033[32m" + texto + "\033[0m")  # Clave en amarillo, ":" en negrita blanco, y valor en verde
	else:
		print("\t\033[91mError:\033[0m No se encontró el separador nulo en los datos del chunk.")

def imprimir_chunk_cHRM(datos_chunk) -> None:
	"""Imprime los datos del chunk cHRM."""
	if len(datos_chunk) != 32:
		print("\033[91mError: Longitud de datos de chunk cHRM inválida.\033[0m")
		return
	
	# Extraer los datos y convertirlos a valores flotantes
	valores: tuple[any, ...] = struct.unpack('>IIIIIIII', datos_chunk)
	valores_float: list = [val / 100000 for val in valores]

	print("\033[93mCoordenadas Cromáticas Blancas y Puntos de Referencia RGB Primarios (cHRM):\033[0m")
	print("\t\033[97mPunto Blanco x:\033[0m", f"\033[93m{valores_float[0]}\033[0m")
	print("\t\033[97mPunto Blanco y:\033[0m", f"\033[93m{valores_float[1]}\033[0m")
	print("\t\033[91mRojo x:\033[0m", f"\033[93m{valores_float[2]}\033[0m")
	print("\t\033[91mRojo y:\033[0m", f"\033[93m{valores_float[3]}\033[0m")
	print("\t\033[92mVerde x:\033[0m", f"\033[93m{valores_float[4]}\033[0m")
	print("\t\033[92mVerde y:\033[0m", f"\033[93m{valores_float[5]}\033[0m")
	print("\t\033[94mAzul x:\033[0m", f"\033[93m{valores_float[6]}\033[0m")
	print("\t\033[94mAzul y:\033[0m", f"\033[93m{valores_float[7]}\033[0m")

def imprimir_chunk_gAMA(datos_chunk) -> None:
	"""Imprime los datos del chunk gAMA."""
	if len(datos_chunk) != 4:
		print("Error: Longitud de datos de chunk gAMA inválida.")
		return
	
	gamma = int.from_bytes(datos_chunk, byteorder='big') / 100000

	print("\033[93mValor de Gamma:\033[0m", f"\033[92m{gamma}\033[0m")

def imprimir_chunk_bKGD(datos_chunk) -> None:
	"""Imprime los datos del chunk bKGD."""
	if len(datos_chunk) != 6:
		print("Error: Longitud de datos de chunk bKGD inválida.")
		return
	
	componente_rojo: bytes = datos_chunk[0:2]
	componente_verde: bytes = datos_chunk[2:4]
	componente_azul: bytes = datos_chunk[4:6]

	print("\033[93mColor de fondo (bKGD):\033[0m")
	print("\t\033[94mComponente Rojo:\033[0m", f"\033[92m{componente_rojo.hex()}\033[0m")
	print("\t\033[94mComponente Verde:\033[0m", f"\033[92m{componente_verde.hex()}\033[0m")
	print("\t\033[94mComponente Azul:\033[0m", f"\033[92m{componente_azul.hex()}\033[0m")

def imprimir_chunk_tIME(datos_chunk) -> None:
	"""Imprime los datos del chunk tIME."""
	año, mes, día, hora, minuto, segundo = struct.unpack('>HBBBBB', datos_chunk)

	print("\033[93mÚltima modificación:\033[0m")
	print("\t\033[94mAño:\033[0m", f"\033[92m{año}\033[0m")
	print("\t\033[94mMes:\033[0m", f"\033[92m{mes}\033[0m")
	print("\t\033[94mDía:\033[0m", f"\033[92m{día}\033[0m")
	print("\t\033[94mHora:\033[0m", f"\033[92m{hora}\033[0m")
	print("\t\033[94mMinuto:\033[0m", f"\033[92m{minuto}\033[0m")
	print("\t\033[94mSegundo:\033[0m", f"\033[92m{segundo}\033[0m")

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
			print("\033[96mDatos del Chunk (hex):\033[0m", "\n\033[92m" + (chunk["Datos del Chunk"][:128].hex() if chunk["Longitud"] > 128 else chunk["Datos del Chunk"].hex()) + "\033[0m")

		print("\033[91mCRC:\033[0m", "\033[91m" + str(object=chunk["CRC"]) + "\033[0m\n")

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

		# print(repr(info_chunk))
		chunks.append(info_chunk)

	return chunks

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
		png_signature: bytes = b'\x89PNG\r\n\x1a\n'
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
		ruta: Path = Path(args.archivo)
	else:
		# Si no se proporciona ningún archivo, solicitar al usuario la ruta de la imagen
		os.system(command='cls' if os.name == 'nt' else 'clear')
		ruta: Path = Path(input("Introduce la ruta de la imagen PNG: ").strip().strip("\'\´\`\""))

	# Llamar a la función tester con la ruta del archivo como argumento
	tester(ruta=ruta)
	input()
