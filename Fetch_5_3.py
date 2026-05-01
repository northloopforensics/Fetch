#Python3

# fixed an issue with cell site maps not showing correct options

import simplekml #the library used to map longitudes and latitudes on google earth
import pandas #used to read spreadsheet data
import re
# import operator
import streamlit as st
import chardet      #   used to check file encodings
import os
import tempfile

# leafmap writes temp HTML files relative to cwd; ensure cwd is always writable
os.chdir(tempfile.gettempdir())

# ── Language Support ───────────────────────────────────────────────────────────
TRANSLATIONS = {
    "en": {
        "tab_review_ingest": "Review Ingest Data",
        "tab_time_filter": "Time Filter",
        "tab_declutter": "Declutter",
        "tab_timezone": "Timezone Conversion",
        "tab_geofence": "Create Geofence",
        "tab_ip_mapping": "IP Address Mapping",
        "tab_preview_kml": "Preview/KML Map",
        "tab_analysis_maps": "Analysis Maps",
        "tab_create_geofence": "Create Geofence",
        "tab_advanced_analysis": "Advanced Analysis",
        "tab_stop_dwell": "Stop/Dwell Detection",
        "tab_colocation": "Co-Location Analysis",
        "tab_coord_tools": "Coordinate Tools",
        "tab_single_conv": "Single Conversion",
        "tab_utm_conv": "UTM Converter",
        "map_clustered": "Clustered Markers",
        "map_points_trails": "Points & Trails",
        "map_hotspots": "Hotspots",
        "map_heatmap": "Heatmap",
        "map_cell_sites": "Cell Sites",
        "mode_markers": "Markers",
        "mode_progression": "Show Point Progression",
        "mode_vapor": "Vapour Trail",
        "lbl_select_map_type": "Select Map Type",
        "lbl_select_map_activity": "Select map activity",
        "lbl_time_interval": "Time Interval to Display",
        "lbl_conversion_method": "Conversion Method",
        "lbl_output_format": "Output Format",
        "lbl_hemisphere": "Hemisphere",
        "lbl_datetime_column": "Date / Time Column",
        "lbl_weight_column": "Weight Column",
        "lbl_time_column": "Time Column",
        "lbl_icon_style": "Select Map Point Icon Style",
        "lbl_icon_labels": "Map Icon Labels",
        "lbl_sector_color": "Sector Color",
        "lbl_sector_footprint": "Sector Footprint Size",
        "lbl_sector_azimuth": "Sector Azimuth",
        "lbl_beam_width": "Sector Beam Width",
        "lbl_radius_meters": "Radius/Footprint in Meters",
        "lbl_radius_distance": "Radius/Distance-from-Point in Meters",
        "lbl_tour_altitude": "Tour Altitude (Meters)",
        "lbl_linger_time": "Tour Linger Time (Seconds)",
        "lbl_tour_tilt": "Tour Tilt",
        "lbl_camera_fly": "Camera Fly Mode",
        "lbl_remove_rows": "Number of Rows to Remove from Start",
        "lbl_radius_m": "Radius (m)",
        "lbl_max_hotspots": "Max Hotspots",
        "lbl_source_tz": "Source Timezone",
        "lbl_target_tz": "Target Timezone",
        "interval_daily": "Daily",
        "interval_hourly": "Hourly",
        "interval_10min": "10 Minutes",
        "interval_1min": "1 Minute",
        "conv_timezone": "Timezone Conversion",
        "conv_offset": "Hourly Offset",
        "northern": "Northern",
        "southern": "Southern",
        "fmt_kml": "KML",
        "fmt_kmz": "KMZ",
        "btn_search": "Search",
        "btn_run_hotspot": "Run Hotspot Analysis",
        "btn_clear_hotspots": "Clear Hotspots",
        "btn_generate_kml": "Generate KML",
        "btn_detect_stops": "Detect Stops",
        "btn_run_colocation": "Run Co-Location Analysis",
        "btn_convert_utm": "Convert UTM",
        "btn_apply_time_filter": "Apply Multi-Source Time Filter",
        "btn_preview_conversion": "Preview Conversion",
        "btn_apply_conversion": "Apply Conversion",
        "chk_advanced": "Advanced",
        "chk_trim_chaining": "Trim Chaining (enforce radius)",
        "chk_accuracy_radius": "Data has Accuracy or Radius Information",
        "chk_enable_time_filter": "Enable Time Filtering",
        "chk_per_source": "Analyze each source file separately",
        "chk_show_points": "Show Individual Points",
        "chk_show_col_info": "Show Column Information",
        "chk_footprint": "Data set includes radius/area information",
        "chk_path_line": "Include travel path line",
        "chk_kml_tour": "Include KML Tour",
        "chk_has_dates": "Data set includes date/time information",
        "chk_use_weight": "Use Weight Column",
        "chk_declutter": "Enable Declutter",
        "hdr_advanced_analysis": "Advanced Analysis",
        "hdr_stop_dwell": "Stop / Dwell Detection",
        "hdr_colocation": "Co-Location / Proximity Analysis",
        "hdr_coord_converter": "Coordinate Format Converter",
        "hdr_hotspot_summary": "Hotspot Summary",
        "hdr_hotspot_clocks": "Hotspot Tactical Clocks",
        "hdr_design_kml": "Design Your KML Map",
        "hdr_tour_settings": "Design Tour Settings",
        "hdr_filter_results": "Filter Results",
        "hdr_declutter": "\U0001f3af Declutter Settings",
        "hdr_header_cleaning": "Header Cleaning",
        "hdr_data_preview": "Data Preview",
        "hdr_datetime_filter": "Date/Time Filtering",
        "hdr_data_declutter": "Data Decluttering",
        "hdr_timezone": "Timezone Conversion",
        "hdr_stop_map": "Stop Locations Map",
        "hdr_coloc_map": "Co-Location Map",
        "hdr_custom_date": "Custom Date Range",
        "msg_manage_data": "Manage Ingested Data",
        "msg_import_photos": "Import Photo Locations (EXIF GPS)",
        "msg_drawing_hint": "Draw a shape (polygon/rectangle) to see coordinates below the map instantly.",
        "msg_tips_hotspot": "**Tips:** Increase radius if visits are a few dozen meters apart; decrease radius for tighter grouping.",
        "msg_coloc_requires": "Co-location analysis requires **2 or more source files** loaded simultaneously. Upload multiple files to use this feature.",
        "msg_convert_single": "Convert a single coordinate value between formats.",
        "msg_convert_utm": "Convert UTM coordinates to latitude/longitude.",
        "msg_stops_no_time": "No date/time columns detected. Stop/Dwell detection requires time data.",
        "msg_coloc_no_time": "No date/time columns detected. Co-location analysis requires time data.",
        "msg_no_valid_records": "No valid records with coordinates.",
        "msg_map_name_required": "Provide map name above",
        "msg_check_lat_lon": "Check that your data has Latitude and Longitude columns",
        "msg_photo_success": "Extracted GPS data from {} photo(s)",
        "msg_no_gps_photos": "No GPS data could be extracted from the uploaded photos.",
        "hdr_multisource_time": "Multi-Source Time Configuration",
        "hdr_sample_filtered": "Sample of Filtered Data",
        "hdr_time_filter": "Time Filter",
        "hdr_time_range_info": "Data Time Range Information",
        "hdr_quick_filters": "Quick Filters",
        "hdr_review_data": "Review Ingested Data",
        "hdr_apply_time_filter": "Apply Time Filter",
        "hdr_coord_diag": "Loaded Data Coordinate Diagnostics",
        "btn_download_csv": "Download Filtered Data as CSV",
        "msg_params_changed": "Parameters changed — press 'Run Hotspot Analysis' to recompute.",
        "qf_all_data": "All Data",
        "qf_24h": "Last 24 Hours",
        "qf_week": "Last Week",
        "qf_month": "Last Month",
        "qf_custom": "Custom Range",
        "lbl_quick_filter": "Choose a preset or custom range:",
        "lbl_choose_files": "Choose files to analyze",
        "lbl_search_addr_ip": "Search (Address/IP)",
        "lbl_place_name": "Place Name or Address",
        "lbl_enter_coord": "Enter coordinate (DMS, DDM, or Decimal)",
        "lbl_time_col_optional": "Time Column (optional -select for tactical clock)",
        "lbl_proximity_radius": "Proximity Radius (m)",
        "lbl_time_window": "Time Window (min)",
        "lbl_min_duration": "Min Duration (min)",
        "lbl_zone_number": "Zone Number",
        "lbl_zone_letter": "Zone Letter",
        "lbl_easting": "Easting (m)",
        "lbl_northing": "Northing (m)",
        "lbl_date_time_col": "Date/Time Column",
        "lbl_radius_col_meters": "Radius Column (meters)",
        "msg_privacy": "Privacy Statement and API Use",
    },
    "es": {
        "tab_review_ingest": "Revisar Datos",
        "tab_time_filter": "Filtro de Tiempo",
        "tab_declutter": "Simplificar",
        "tab_timezone": "Conversión de Zona Horaria",
        "tab_geofence": "Crear Geocerca",
        "tab_ip_mapping": "Mapeo de Dirección IP",
        "tab_preview_kml": "Vista Previa/Mapa KML",
        "tab_analysis_maps": "Mapas de Análisis",
        "tab_create_geofence": "Crear Geocerca",
        "tab_advanced_analysis": "Análisis Avanzado",
        "tab_stop_dwell": "Detección de Paradas",
        "tab_colocation": "Análisis de Co-ubicación",
        "tab_coord_tools": "Herramientas de Coordenadas",
        "tab_single_conv": "Conversión Individual",
        "tab_utm_conv": "Convertidor UTM",
        "map_clustered": "Marcadores Agrupados",
        "map_points_trails": "Puntos y Trayectorias",
        "map_hotspots": "Zonas de Concentración",
        "map_heatmap": "Mapa de Calor",
        "map_cell_sites": "Torres Celulares",
        "mode_markers": "Marcadores",
        "mode_progression": "Mostrar Progresión de Puntos",
        "mode_vapor": "Rastro de Vapor",
        "lbl_select_map_type": "Seleccionar Tipo de Mapa",
        "lbl_select_map_activity": "Seleccionar actividad del mapa",
        "lbl_time_interval": "Intervalo de Tiempo a Mostrar",
        "lbl_conversion_method": "Método de Conversión",
        "lbl_output_format": "Formato de Salida",
        "lbl_hemisphere": "Hemisferio",
        "lbl_datetime_column": "Columna de Fecha / Hora",
        "lbl_weight_column": "Columna de Peso",
        "lbl_time_column": "Columna de Tiempo",
        "lbl_icon_style": "Seleccionar Estilo de Icono del Mapa",
        "lbl_icon_labels": "Etiquetas de Iconos del Mapa",
        "lbl_sector_color": "Color del Sector",
        "lbl_sector_footprint": "Tamaño del Sector",
        "lbl_sector_azimuth": "Azimut del Sector",
        "lbl_beam_width": "Ancho del Haz del Sector",
        "lbl_radius_meters": "Radio/Huella en Metros",
        "lbl_radius_distance": "Radio/Distancia desde el Punto en Metros",
        "lbl_tour_altitude": "Altitud del Tour (Metros)",
        "lbl_linger_time": "Tiempo de Espera del Tour (Segundos)",
        "lbl_tour_tilt": "Inclinación del Tour",
        "lbl_camera_fly": "Modo de Vuelo de Cámara",
        "lbl_remove_rows": "Número de Filas a Eliminar del Inicio",
        "lbl_radius_m": "Radio (m)",
        "lbl_max_hotspots": "Máximo de Zonas",
        "lbl_source_tz": "Zona Horaria de Origen",
        "lbl_target_tz": "Zona Horaria de Destino",
        "interval_daily": "Diario",
        "interval_hourly": "Por Hora",
        "interval_10min": "10 Minutos",
        "interval_1min": "1 Minuto",
        "conv_timezone": "Conversión de Zona Horaria",
        "conv_offset": "Desplazamiento por Horas",
        "northern": "Norte",
        "southern": "Sur",
        "fmt_kml": "KML",
        "fmt_kmz": "KMZ",
        "btn_search": "Buscar",
        "btn_run_hotspot": "Ejecutar Análisis de Zonas",
        "btn_clear_hotspots": "Limpiar Zonas",
        "btn_generate_kml": "Generar KML",
        "btn_detect_stops": "Detectar Paradas",
        "btn_run_colocation": "Ejecutar Análisis de Co-ubicación",
        "btn_convert_utm": "Convertir UTM",
        "btn_apply_time_filter": "Aplicar Filtro de Tiempo",
        "btn_preview_conversion": "Vista Previa de Conversión",
        "btn_apply_conversion": "Aplicar Conversión",
        "chk_advanced": "Avanzado",
        "chk_trim_chaining": "Recortar Encadenamiento (aplicar radio)",
        "chk_accuracy_radius": "El conjunto de datos incluye información de precisión o radio",
        "chk_enable_time_filter": "Habilitar Filtro de Tiempo",
        "chk_per_source": "Analizar cada archivo fuente por separado",
        "chk_show_points": "Mostrar Puntos Individuales",
        "chk_show_col_info": "Mostrar Información de Columnas",
        "chk_footprint": "El conjunto de datos incluye información de radio/área",
        "chk_path_line": "Incluir línea de trayectoria de viaje",
        "chk_kml_tour": "Incluir Tour KML",
        "chk_has_dates": "El conjunto de datos incluye información de fecha/hora",
        "chk_use_weight": "Usar Columna de Peso",
        "chk_declutter": "Habilitar Simplificación",
        "hdr_advanced_analysis": "Análisis Avanzado",
        "hdr_stop_dwell": "Detección de Paradas",
        "hdr_colocation": "Análisis de Co-ubicación / Proximidad",
        "hdr_coord_converter": "Convertidor de Formato de Coordenadas",
        "hdr_hotspot_summary": "Resumen de Zonas de Concentración",
        "hdr_hotspot_clocks": "Relojes Tácticos de Zonas",
        "hdr_design_kml": "Diseña tu Mapa KML",
        "hdr_tour_settings": "Configuración del Tour",
        "hdr_filter_results": "Filtrar Resultados",
        "hdr_declutter": "\U0001f3af Configuración de Simplificación",
        "hdr_header_cleaning": "Limpieza de Encabezados",
        "hdr_data_preview": "Vista Previa de Datos",
        "hdr_datetime_filter": "Filtrado de Fecha/Hora",
        "hdr_data_declutter": "Simplificación de Datos",
        "hdr_timezone": "Conversión de Zona Horaria",
        "hdr_stop_map": "Mapa de Ubicaciones de Paradas",
        "hdr_coloc_map": "Mapa de Co-ubicación",
        "hdr_custom_date": "Rango de Fechas Personalizado",
        "msg_manage_data": "Gestionar Datos Importados",
        "msg_import_photos": "Importar Ubicaciones de Fotos (EXIF GPS)",
        "msg_drawing_hint": "Dibuja una forma (polígono/rectángulo) para ver las coordenadas debajo del mapa al instante.",
        "msg_tips_hotspot": "**Consejos:** Aumenta el radio si las visitas están separadas varias decenas de metros; disminúyelo para agrupaciones más precisas.",
        "msg_coloc_requires": "El análisis de co-ubicación requiere **2 o más archivos fuente** cargados simultáneamente.",
        "msg_convert_single": "Convierte un valor de coordenada entre formatos.",
        "msg_convert_utm": "Convierte coordenadas UTM a latitud/longitud.",
        "msg_stops_no_time": "No se detectaron columnas de fecha/hora. La detección de paradas requiere datos de tiempo.",
        "msg_coloc_no_time": "No se detectaron columnas de fecha/hora. El análisis de co-ubicación requiere datos de tiempo.",
        "msg_no_valid_records": "No hay registros válidos con coordenadas.",
        "msg_map_name_required": "Proporciona el nombre del mapa arriba",
        "msg_check_lat_lon": "Comprueba que tus datos tienen columnas de Latitud y Longitud",
        "msg_photo_success": "Datos GPS extraídos de {} foto(s)",
        "msg_no_gps_photos": "No se pudieron extraer datos GPS de las fotos cargadas.",
        "hdr_multisource_time": "Configuración de Tiempo Multi-Fuente",
        "hdr_sample_filtered": "Muestra de Datos Filtrados",
        "hdr_time_filter": "Filtro de Tiempo",
        "hdr_time_range_info": "Información del Rango de Tiempo de Datos",
        "hdr_quick_filters": "Filtros Rápidos",
        "hdr_review_data": "Revisar Datos Importados",
        "hdr_apply_time_filter": "Aplicar Filtro de Tiempo",
        "hdr_coord_diag": "Diagnóstico de Coordenadas de Datos Cargados",
        "btn_download_csv": "Descargar Datos Filtrados como CSV",
        "msg_params_changed": "Parámetros cambiados — presiona 'Ejecutar Análisis de Zonas' para recalcular.",
        "qf_all_data": "Todos los Datos",
        "qf_24h": "Últimas 24 Horas",
        "qf_week": "Última Semana",
        "qf_month": "Último Mes",
        "qf_custom": "Rango Personalizado",
        "lbl_quick_filter": "Elige un rango preestablecido o personalizado:",
        "lbl_choose_files": "Elegir archivos para analizar",
        "lbl_search_addr_ip": "Buscar (Dirección/IP)",
        "lbl_place_name": "Nombre de Lugar o Dirección",
        "lbl_enter_coord": "Ingresar coordenada (GMS, GMD o Decimal)",
        "lbl_time_col_optional": "Columna de Tiempo (opcional - para reloj táctico)",
        "lbl_proximity_radius": "Radio de Proximidad (m)",
        "lbl_time_window": "Ventana de Tiempo (min)",
        "lbl_min_duration": "Duración Mínima (min)",
        "lbl_zone_number": "Número de Zona",
        "lbl_zone_letter": "Letra de Zona",
        "lbl_easting": "Este (m)",
        "lbl_northing": "Norte (m)",
        "lbl_date_time_col": "Columna de Fecha/Hora",
        "lbl_radius_col_meters": "Columna de Radio (metros)",
        "msg_privacy": "Declaración de Privacidad y Uso de API",
    },
    "pt": {
        "tab_review_ingest": "Revisar Dados",
        "tab_time_filter": "Filtro de Tempo",
        "tab_declutter": "Simplificar",
        "tab_timezone": "Conversão de Fuso Horário",
        "tab_geofence": "Criar Geocerca",
        "tab_ip_mapping": "Mapeamento de IP",
        "tab_preview_kml": "Pré-visualização/Mapa KML",
        "tab_analysis_maps": "Mapas de Análise",
        "tab_create_geofence": "Criar Geocerca",
        "tab_advanced_analysis": "Análise Avançada",
        "tab_stop_dwell": "Detecção de Paradas",
        "tab_colocation": "Análise de Co-localização",
        "tab_coord_tools": "Ferramentas de Coordenadas",
        "tab_single_conv": "Conversão Individual",
        "tab_utm_conv": "Conversor UTM",
        "map_clustered": "Marcadores Agrupados",
        "map_points_trails": "Pontos e Trilhas",
        "map_hotspots": "Pontos de Concentração",
        "map_heatmap": "Mapa de Calor",
        "map_cell_sites": "Torres de Celular",
        "mode_markers": "Marcadores",
        "mode_progression": "Mostrar Progressão de Pontos",
        "mode_vapor": "Rastro de Vapor",
        "lbl_select_map_type": "Selecionar Tipo de Mapa",
        "lbl_select_map_activity": "Selecionar atividade do mapa",
        "lbl_time_interval": "Intervalo de Tempo a Exibir",
        "lbl_conversion_method": "Método de Conversão",
        "lbl_output_format": "Formato de Saída",
        "lbl_hemisphere": "Hemisfério",
        "lbl_datetime_column": "Coluna de Data / Hora",
        "lbl_weight_column": "Coluna de Peso",
        "lbl_time_column": "Coluna de Tempo",
        "lbl_icon_style": "Selecionar Estilo de Ícone do Mapa",
        "lbl_icon_labels": "Rótulos de Ícones do Mapa",
        "lbl_sector_color": "Cor do Setor",
        "lbl_sector_footprint": "Tamanho do Setor",
        "lbl_sector_azimuth": "Azimute do Setor",
        "lbl_beam_width": "Largura do Feixe do Setor",
        "lbl_radius_meters": "Raio/Área em Metros",
        "lbl_radius_distance": "Raio/Distância do Ponto em Metros",
        "lbl_tour_altitude": "Altitude do Tour (Metros)",
        "lbl_linger_time": "Tempo de Espera do Tour (Segundos)",
        "lbl_tour_tilt": "Inclinação do Tour",
        "lbl_camera_fly": "Modo de Voo da Câmera",
        "lbl_remove_rows": "Número de Linhas a Remover do Início",
        "lbl_radius_m": "Raio (m)",
        "lbl_max_hotspots": "Máximo de Hotspots",
        "lbl_source_tz": "Fuso Horário de Origem",
        "lbl_target_tz": "Fuso Horário de Destino",
        "interval_daily": "Diário",
        "interval_hourly": "Por Hora",
        "interval_10min": "10 Minutos",
        "interval_1min": "1 Minuto",
        "conv_timezone": "Conversão de Fuso Horário",
        "conv_offset": "Deslocamento por Horas",
        "northern": "Norte",
        "southern": "Sul",
        "fmt_kml": "KML",
        "fmt_kmz": "KMZ",
        "btn_search": "Buscar",
        "btn_run_hotspot": "Executar Análise de Hotspots",
        "btn_clear_hotspots": "Limpar Hotspots",
        "btn_generate_kml": "Gerar KML",
        "btn_detect_stops": "Detectar Paradas",
        "btn_run_colocation": "Executar Análise de Co-localização",
        "btn_convert_utm": "Converter UTM",
        "btn_apply_time_filter": "Aplicar Filtro de Tempo",
        "btn_preview_conversion": "Pré-visualizar Conversão",
        "btn_apply_conversion": "Aplicar Conversão",
        "chk_advanced": "Avançado",
        "chk_trim_chaining": "Limitar Encadeamento (aplicar raio)",
        "chk_accuracy_radius": "O conjunto de dados inclui informações de precisão ou raio",
        "chk_enable_time_filter": "Habilitar Filtro de Tempo",
        "chk_per_source": "Analisar cada arquivo-fonte separadamente",
        "chk_show_points": "Mostrar Pontos Individuais",
        "chk_show_col_info": "Mostrar Informações de Colunas",
        "chk_footprint": "O conjunto de dados inclui informações de raio/área",
        "chk_path_line": "Incluir linha de trajetória de viagem",
        "chk_kml_tour": "Incluir Tour KML",
        "chk_has_dates": "O conjunto de dados inclui informações de data/hora",
        "chk_use_weight": "Usar Coluna de Peso",
        "chk_declutter": "Habilitar Simplificação",
        "hdr_advanced_analysis": "Análise Avançada",
        "hdr_stop_dwell": "Detecção de Paradas",
        "hdr_colocation": "Análise de Co-localização / Proximidade",
        "hdr_coord_converter": "Conversor de Formato de Coordenadas",
        "hdr_hotspot_summary": "Resumo de Pontos de Concentração",
        "hdr_hotspot_clocks": "Relógios Táticos de Hotspots",
        "hdr_design_kml": "Projete seu Mapa KML",
        "hdr_tour_settings": "Configurações do Tour",
        "hdr_filter_results": "Filtrar Resultados",
        "hdr_declutter": "\U0001f3af Configurações de Simplificação",
        "hdr_header_cleaning": "Limpeza de Cabeçalhos",
        "hdr_data_preview": "Pré-visualização de Dados",
        "hdr_datetime_filter": "Filtragem de Data/Hora",
        "hdr_data_declutter": "Simplificação de Dados",
        "hdr_timezone": "Conversão de Fuso Horário",
        "hdr_stop_map": "Mapa de Locais de Paradas",
        "hdr_coloc_map": "Mapa de Co-localização",
        "hdr_custom_date": "Intervalo de Datas Personalizado",
        "msg_manage_data": "Gerenciar Dados Importados",
        "msg_import_photos": "Importar Locais de Fotos (EXIF GPS)",
        "msg_drawing_hint": "Desenhe uma forma (polígono/retângulo) para ver as coordenadas abaixo do mapa imediatamente.",
        "msg_tips_hotspot": "**Dicas:** Aumente o raio se as visitas estiverem separadas por algumas dezenas de metros; diminua para agrupamentos mais precisos.",
        "msg_coloc_requires": "A análise de co-localização requer **2 ou mais arquivos-fonte** carregados simultaneamente.",
        "msg_convert_single": "Converta um valor de coordenada entre formatos.",
        "msg_convert_utm": "Converta coordenadas UTM para latitude/longitude.",
        "msg_stops_no_time": "Nenhuma coluna de data/hora detectada. A detecção de paradas requer dados de tempo.",
        "msg_coloc_no_time": "Nenhuma coluna de data/hora detectada. A análise de co-localização requer dados de tempo.",
        "msg_no_valid_records": "Nenhum registro válido com coordenadas.",
        "msg_map_name_required": "Forneça o nome do mapa acima",
        "msg_check_lat_lon": "Verifique se seus dados têm colunas de Latitude e Longitude",
        "msg_photo_success": "Dados GPS extraídos de {} foto(s)",
        "msg_no_gps_photos": "Não foi possível extrair dados GPS das fotos carregadas.",
        "hdr_multisource_time": "Configuração de Tempo Multi-Fonte",
        "hdr_sample_filtered": "Amostra de Dados Filtrados",
        "hdr_time_filter": "Filtro de Tempo",
        "hdr_time_range_info": "Informações do Intervalo de Tempo dos Dados",
        "hdr_quick_filters": "Filtros Rápidos",
        "hdr_review_data": "Revisar Dados Importados",
        "hdr_apply_time_filter": "Aplicar Filtro de Tempo",
        "hdr_coord_diag": "Diagnóstico de Coordenadas dos Dados Carregados",
        "btn_download_csv": "Baixar Dados Filtrados como CSV",
        "msg_params_changed": "Parâmetros alterados — pressione 'Executar Análise de Hotspots' para recalcular.",
        "qf_all_data": "Todos os Dados",
        "qf_24h": "Últimas 24 Horas",
        "qf_week": "Última Semana",
        "qf_month": "Último Mês",
        "qf_custom": "Intervalo Personalizado",
        "lbl_quick_filter": "Escolha um intervalo predefinido ou personalizado:",
        "lbl_choose_files": "Escolher arquivos para analisar",
        "lbl_search_addr_ip": "Buscar (Endereço/IP)",
        "lbl_place_name": "Nome do Local ou Endereço",
        "lbl_enter_coord": "Inserir coordenada (GMS, GMD ou Decimal)",
        "lbl_time_col_optional": "Coluna de Tempo (opcional - para relógio tático)",
        "lbl_proximity_radius": "Raio de Proximidade (m)",
        "lbl_time_window": "Janela de Tempo (min)",
        "lbl_min_duration": "Duração Mínima (min)",
        "lbl_zone_number": "Número da Zona",
        "lbl_zone_letter": "Letra da Zona",
        "lbl_easting": "Leste (m)",
        "lbl_northing": "Norte (m)",
        "lbl_date_time_col": "Coluna de Data/Hora",
        "lbl_radius_col_meters": "Coluna de Raio (metros)",
        "msg_privacy": "Declaração de Privacidade e Uso de API",
    },
    "de": {
        "tab_review_ingest": "Daten Überprüfen",
        "tab_time_filter": "Zeitfilter",
        "tab_declutter": "Bereinigen",
        "tab_timezone": "Zeitzonenkonvertierung",
        "tab_geofence": "Geofence Erstellen",
        "tab_ip_mapping": "IP-Adress-Kartierung",
        "tab_preview_kml": "Vorschau/KML-Karte",
        "tab_analysis_maps": "Analysekarten",
        "tab_create_geofence": "Geofence Erstellen",
        "tab_advanced_analysis": "Erweiterte Analyse",
        "tab_stop_dwell": "Aufenthalts-Erkennung",
        "tab_colocation": "Ko-Lokalisierungs-Analyse",
        "tab_coord_tools": "Koordinatenwerkzeuge",
        "tab_single_conv": "Einzelkonvertierung",
        "tab_utm_conv": "UTM-Konverter",
        "map_clustered": "Gruppierte Marker",
        "map_points_trails": "Punkte & Routen",
        "map_hotspots": "Hotspots",
        "map_heatmap": "Heatmap",
        "map_cell_sites": "Mobilfunkstandorte",
        "mode_markers": "Marker",
        "mode_progression": "Punktverlauf Anzeigen",
        "mode_vapor": "Dampfspur",
        "lbl_select_map_type": "Kartentyp Auswählen",
        "lbl_select_map_activity": "Kartenaktivität Auswählen",
        "lbl_time_interval": "Anzuzeigendes Zeitintervall",
        "lbl_conversion_method": "Konvertierungsmethode",
        "lbl_output_format": "Ausgabeformat",
        "lbl_hemisphere": "Hemisphäre",
        "lbl_datetime_column": "Datum / Uhrzeit Spalte",
        "lbl_weight_column": "Gewichtungsspalte",
        "lbl_time_column": "Zeitspalte",
        "lbl_icon_style": "Kartensymbol-Stil Auswählen",
        "lbl_icon_labels": "Kartensymbol-Beschriftungen",
        "lbl_sector_color": "Sektorfarbe",
        "lbl_sector_footprint": "Sektorgröße",
        "lbl_sector_azimuth": "Sektor-Azimut",
        "lbl_beam_width": "Sektorstrahlbreite",
        "lbl_radius_meters": "Radius/Fußabdruck in Metern",
        "lbl_radius_distance": "Radius/Abstand vom Punkt in Metern",
        "lbl_tour_altitude": "Tour-Höhe (Meter)",
        "lbl_linger_time": "Tour-Verweilzeit (Sekunden)",
        "lbl_tour_tilt": "Tour-Neigung",
        "lbl_camera_fly": "Kamera-Flugmodus",
        "lbl_remove_rows": "Anzahl der zu entfernenden Anfangszeilen",
        "lbl_radius_m": "Radius (m)",
        "lbl_max_hotspots": "Maximale Hotspots",
        "lbl_source_tz": "Quell-Zeitzone",
        "lbl_target_tz": "Ziel-Zeitzone",
        "interval_daily": "Täglich",
        "interval_hourly": "Stündlich",
        "interval_10min": "10 Minuten",
        "interval_1min": "1 Minute",
        "conv_timezone": "Zeitzonenkonvertierung",
        "conv_offset": "Stundenversatz",
        "northern": "Nördlich",
        "southern": "Südlich",
        "fmt_kml": "KML",
        "fmt_kmz": "KMZ",
        "btn_search": "Suchen",
        "btn_run_hotspot": "Hotspot-Analyse Starten",
        "btn_clear_hotspots": "Hotspots Löschen",
        "btn_generate_kml": "KML Generieren",
        "btn_detect_stops": "Aufenthalte Erkennen",
        "btn_run_colocation": "Ko-Lokalisierungs-Analyse Starten",
        "btn_convert_utm": "UTM Konvertieren",
        "btn_apply_time_filter": "Zeitfilter Anwenden",
        "btn_preview_conversion": "Konvertierung Vorschau",
        "btn_apply_conversion": "Konvertierung Anwenden",
        "chk_advanced": "Erweitert",
        "chk_trim_chaining": "Verkettung Kürzen (Radius erzwingen)",
        "chk_accuracy_radius": "Datensatz enthält Genauigkeits- oder Radiusdaten",
        "chk_enable_time_filter": "Zeitfilter Aktivieren",
        "chk_per_source": "Jede Quelldatei separat analysieren",
        "chk_show_points": "Einzelne Punkte Anzeigen",
        "chk_show_col_info": "Spalteninformationen Anzeigen",
        "chk_footprint": "Datensatz enthält Radius-/Flächeninformationen",
        "chk_path_line": "Reisepfadlinie einschließen",
        "chk_kml_tour": "KML-Tour einschließen",
        "chk_has_dates": "Datensatz enthält Datum-/Uhrzeitinformationen",
        "chk_use_weight": "Gewichtungsspalte Verwenden",
        "chk_declutter": "Bereinigung Aktivieren",
        "hdr_advanced_analysis": "Erweiterte Analyse",
        "hdr_stop_dwell": "Aufenthalts-Erkennung",
        "hdr_colocation": "Ko-Lokalisierungs- / Nähe-Analyse",
        "hdr_coord_converter": "Koordinatenformat-Konverter",
        "hdr_hotspot_summary": "Hotspot-Zusammenfassung",
        "hdr_hotspot_clocks": "Hotspot Taktische Uhren",
        "hdr_design_kml": "KML-Karte Gestalten",
        "hdr_tour_settings": "Tour-Einstellungen",
        "hdr_filter_results": "Ergebnisse Filtern",
        "hdr_declutter": "\U0001f3af Bereinigungseinstellungen",
        "hdr_header_cleaning": "Kopfzeilen-Bereinigung",
        "hdr_data_preview": "Datenvorschau",
        "hdr_datetime_filter": "Datum/Uhrzeit-Filterung",
        "hdr_data_declutter": "Datenbereinigung",
        "hdr_timezone": "Zeitzonenkonvertierung",
        "hdr_stop_map": "Karte der Aufenthaltsstandorte",
        "hdr_coloc_map": "Ko-Lokalisierungskarte",
        "hdr_custom_date": "Benutzerdefinierter Datumsbereich",
        "msg_manage_data": "Importierte Daten Verwalten",
        "msg_import_photos": "Fotostandorte Importieren (EXIF GPS)",
        "msg_drawing_hint": "Zeichnen Sie eine Form (Polygon/Rechteck), um die Koordinaten sofort unter der Karte zu sehen.",
        "msg_tips_hotspot": "**Tipps:** Radius erhöhen, wenn Besuche einige Dutzend Meter entfernt sind; verringern für engere Gruppierungen.",
        "msg_coloc_requires": "Die Ko-Lokalisierungsanalyse erfordert **2 oder mehr Quelldateien** gleichzeitig.",
        "msg_convert_single": "Einen Koordinatenwert zwischen Formaten konvertieren.",
        "msg_convert_utm": "UTM-Koordinaten in Breiten-/Längengrad konvertieren.",
        "msg_stops_no_time": "Keine Datum/Uhrzeit-Spalten erkannt. Die Aufenthaltserkennung benötigt Zeitdaten.",
        "msg_coloc_no_time": "Keine Datum/Uhrzeit-Spalten erkannt. Die Ko-Lokalisierungsanalyse benötigt Zeitdaten.",
        "msg_no_valid_records": "Keine gültigen Datensätze mit Koordinaten.",
        "msg_map_name_required": "Kartenname oben angeben",
        "msg_check_lat_lon": "Stellen Sie sicher, dass Ihre Daten Breiten- und Längengradenspalten haben",
        "msg_photo_success": "GPS-Daten aus {} Foto(s) extrahiert",
        "msg_no_gps_photos": "Aus den hochgeladenen Fotos konnten keine GPS-Daten extrahiert werden.",
        "hdr_multisource_time": "Multi-Quellen-Zeitkonfiguration",
        "hdr_sample_filtered": "Stichprobe der Gefilterten Daten",
        "hdr_time_filter": "Zeitfilter",
        "hdr_time_range_info": "Datenzeitbereich-Informationen",
        "hdr_quick_filters": "Schnellfilter",
        "hdr_review_data": "Importierte Daten Überprüfen",
        "hdr_apply_time_filter": "Zeitfilter Anwenden",
        "hdr_coord_diag": "Koordinatendiagnose der Geladenen Daten",
        "btn_download_csv": "Gefilterte Daten als CSV Herunterladen",
        "msg_params_changed": "Parameter geändert — 'Hotspot-Analyse Starten' zum Neuberechnen drücken.",
        "qf_all_data": "Alle Daten",
        "qf_24h": "Letzte 24 Stunden",
        "qf_week": "Letzte Woche",
        "qf_month": "Letzter Monat",
        "qf_custom": "Benutzerdefinierter Bereich",
        "lbl_quick_filter": "Voreinstellung oder benutzerdefinierten Bereich wählen:",
        "lbl_choose_files": "Dateien zum Analysieren Auswählen",
        "lbl_search_addr_ip": "Suchen (Adresse/IP)",
        "lbl_place_name": "Ortsname oder Adresse",
        "lbl_enter_coord": "Koordinate eingeben (GMS, GMG oder Dezimal)",
        "lbl_time_col_optional": "Zeitspalte (optional - für taktische Uhr)",
        "lbl_proximity_radius": "Näheradius (m)",
        "lbl_time_window": "Zeitfenster (min)",
        "lbl_min_duration": "Mindestdauer (min)",
        "lbl_zone_number": "Zonennummer",
        "lbl_zone_letter": "Zonenbuchstabe",
        "lbl_easting": "Ostwert (m)",
        "lbl_northing": "Nordwert (m)",
        "lbl_date_time_col": "Datum/Uhrzeit-Spalte",
        "lbl_radius_col_meters": "Radiusspalte (Meter)",
        "msg_privacy": "Datenschutzerklärung und API-Nutzung",
    },
    "ru": {
        "tab_review_ingest": "Просмотр данных",
        "tab_time_filter": "Фильтр по времени",
        "tab_declutter": "Упрощение",
        "tab_timezone": "Конвертация часовых поясов",
        "tab_geofence": "Создать геозону",
        "tab_ip_mapping": "Картирование IP-адресов",
        "tab_preview_kml": "Предпросмотр/KML-карта",
        "tab_analysis_maps": "Аналитические карты",
        "tab_create_geofence": "Создать геозону",
        "tab_advanced_analysis": "Расширенный анализ",
        "tab_stop_dwell": "Обнаружение остановок",
        "tab_colocation": "Анализ совместного присутствия",
        "tab_coord_tools": "Инструменты координат",
        "tab_single_conv": "Одиночная конвертация",
        "tab_utm_conv": "Конвертер UTM",
        "map_clustered": "Сгруппированные маркеры",
        "map_points_trails": "Точки и маршруты",
        "map_hotspots": "Горячие точки",
        "map_heatmap": "Тепловая карта",
        "map_cell_sites": "Сотовые вышки",
        "mode_markers": "Маркеры",
        "mode_progression": "Показать последовательность точек",
        "mode_vapor": "Дымовой след",
        "lbl_select_map_type": "Выбрать тип карты",
        "lbl_select_map_activity": "Выбрать действие на карте",
        "lbl_time_interval": "Отображаемый интервал времени",
        "lbl_conversion_method": "Метод конвертации",
        "lbl_output_format": "Формат вывода",
        "lbl_hemisphere": "Полушарие",
        "lbl_datetime_column": "Столбец даты / времени",
        "lbl_weight_column": "Столбец веса",
        "lbl_time_column": "Столбец времени",
        "lbl_icon_style": "Выбрать стиль значка карты",
        "lbl_icon_labels": "Метки значков карты",
        "lbl_sector_color": "Цвет сектора",
        "lbl_sector_footprint": "Размер сектора",
        "lbl_sector_azimuth": "Азимут сектора",
        "lbl_beam_width": "Ширина луча сектора",
        "lbl_radius_meters": "Радиус/Область в метрах",
        "lbl_radius_distance": "Радиус/Расстояние от точки в метрах",
        "lbl_tour_altitude": "Высота тура (метры)",
        "lbl_linger_time": "Время задержки тура (секунды)",
        "lbl_tour_tilt": "Наклон тура",
        "lbl_camera_fly": "Режим полёта камеры",
        "lbl_remove_rows": "Количество строк для удаления с начала",
        "lbl_radius_m": "Радиус (м)",
        "lbl_max_hotspots": "Максимум горячих точек",
        "lbl_source_tz": "Исходный часовой пояс",
        "lbl_target_tz": "Целевой часовой пояс",
        "interval_daily": "Ежедневно",
        "interval_hourly": "Ежечасно",
        "interval_10min": "10 минут",
        "interval_1min": "1 минута",
        "conv_timezone": "Конвертация часовых поясов",
        "conv_offset": "Смещение по часам",
        "northern": "Северное",
        "southern": "Южное",
        "fmt_kml": "KML",
        "fmt_kmz": "KMZ",
        "btn_search": "Поиск",
        "btn_run_hotspot": "Запустить анализ горячих точек",
        "btn_clear_hotspots": "Очистить горячие точки",
        "btn_generate_kml": "Создать KML",
        "btn_detect_stops": "Обнаружить остановки",
        "btn_run_colocation": "Запустить анализ совместного присутствия",
        "btn_convert_utm": "Конвертировать UTM",
        "btn_apply_time_filter": "Применить фильтр по времени",
        "btn_preview_conversion": "Предпросмотр конвертации",
        "btn_apply_conversion": "Применить конвертацию",
        "chk_advanced": "Расширенный",
        "chk_trim_chaining": "Ограничить цепочку (применить радиус)",
        "chk_accuracy_radius": "Набор данных включает информацию о точности или радиусе",
        "chk_enable_time_filter": "Включить фильтр по времени",
        "chk_per_source": "Анализировать каждый исходный файл отдельно",
        "chk_show_points": "Показать отдельные точки",
        "chk_show_col_info": "Показать информацию о столбцах",
        "chk_footprint": "Набор данных включает информацию о радиусе/площади",
        "chk_path_line": "Включить линию маршрута",
        "chk_kml_tour": "Включить KML-тур",
        "chk_has_dates": "Набор данных включает информацию о дате/времени",
        "chk_use_weight": "Использовать столбец веса",
        "chk_declutter": "Включить упрощение",
        "hdr_advanced_analysis": "Расширенный анализ",
        "hdr_stop_dwell": "Обнаружение остановок",
        "hdr_colocation": "Анализ совместного присутствия / близости",
        "hdr_coord_converter": "Конвертер форматов координат",
        "hdr_hotspot_summary": "Сводка по горячим точкам",
        "hdr_hotspot_clocks": "Тактические часы горячих точек",
        "hdr_design_kml": "Создание KML-карты",
        "hdr_tour_settings": "Настройки тура",
        "hdr_filter_results": "Фильтр результатов",
        "hdr_declutter": "\U0001f3af Настройки упрощения",
        "hdr_header_cleaning": "Очистка заголовков",
        "hdr_data_preview": "Предпросмотр данных",
        "hdr_datetime_filter": "Фильтрация по дате/времени",
        "hdr_data_declutter": "Упрощение данных",
        "hdr_timezone": "Конвертация часовых поясов",
        "hdr_stop_map": "Карта местоположений остановок",
        "hdr_coloc_map": "Карта совместного присутствия",
        "hdr_custom_date": "Пользовательский диапазон дат",
        "msg_manage_data": "Управление загруженными данными",
        "msg_import_photos": "Импорт местоположений фотографий (EXIF GPS)",
        "msg_drawing_hint": "Нарисуйте фигуру (полигон/прямоугольник), чтобы сразу увидеть координаты под картой.",
        "msg_tips_hotspot": "**Советы:** Увеличьте радиус, если визиты разделены несколькими десятками метров; уменьшите для более тесных групп.",
        "msg_coloc_requires": "Анализ совместного присутствия требует **2 или более исходных файлов**, загруженных одновременно.",
        "msg_convert_single": "Конвертировать одно значение координаты между форматами.",
        "msg_convert_utm": "Конвертировать координаты UTM в широту/долготу.",
        "msg_stops_no_time": "Столбцы даты/времени не обнаружены. Обнаружение остановок требует данных о времени.",
        "msg_coloc_no_time": "Столбцы даты/времени не обнаружены. Анализ совместного присутствия требует данных о времени.",
        "msg_no_valid_records": "Нет допустимых записей с координатами.",
        "msg_map_name_required": "Укажите название карты выше",
        "msg_check_lat_lon": "Убедитесь, что в данных есть столбцы Широты и Долготы",
        "msg_photo_success": "Данные GPS извлечены из {} фото",
        "msg_no_gps_photos": "Не удалось извлечь данные GPS из загруженных фотографий.",
        "hdr_multisource_time": "Конфигурация времени нескольких источников",
        "hdr_sample_filtered": "Образец отфильтрованных данных",
        "hdr_time_filter": "Фильтр по времени",
        "hdr_time_range_info": "Информация о диапазоне времени данных",
        "hdr_quick_filters": "Быстрые фильтры",
        "hdr_review_data": "Просмотр загруженных данных",
        "hdr_apply_time_filter": "Применить фильтр по времени",
        "hdr_coord_diag": "Диагностика координат загруженных данных",
        "btn_download_csv": "Скачать отфильтрованные данные в CSV",
        "msg_params_changed": "Параметры изменены — нажмите 'Запустить анализ горячих точек' для пересчёта.",
        "qf_all_data": "Все данные",
        "qf_24h": "Последние 24 часа",
        "qf_week": "Последняя неделя",
        "qf_month": "Последний месяц",
        "qf_custom": "Пользовательский диапазон",
        "lbl_quick_filter": "Выберите предустановленный или пользовательский диапазон:",
        "lbl_choose_files": "Выбрать файлы для анализа",
        "lbl_search_addr_ip": "Поиск (Адрес/IP)",
        "lbl_place_name": "Название места или адрес",
        "lbl_enter_coord": "Введите координату (ГМС, ГМД или Десятичная)",
        "lbl_time_col_optional": "Столбец времени (необязательно - для тактических часов)",
        "lbl_proximity_radius": "Радиус близости (м)",
        "lbl_time_window": "Временное окно (мин)",
        "lbl_min_duration": "Минимальная длительность (мин)",
        "lbl_zone_number": "Номер зоны",
        "lbl_zone_letter": "Буква зоны",
        "lbl_easting": "Восток (м)",
        "lbl_northing": "Север (м)",
        "lbl_date_time_col": "Столбец Даты/Времени",
        "lbl_radius_col_meters": "Столбец радиуса (метры)",
        "msg_privacy": "Заявление о конфиденциальности и использовании API",
    },
}

def t(key: str) -> str:
    """Return the translated string for the current UI language."""
    lang_code = st.session_state.get("_ui_lang_code", "en")
    lang = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
    return lang.get(key, TRANSLATIONS["en"].get(key, key))

from polycircles import polycircles     #   creates kml polygons
import leafmap.foliumap as leafmap      #   maps 
from leafmap.foliumap import plugins    #   maps
import geopandas                        
import folium                           #   maps
from math import asin, atan2, cos, degrees, radians, sin    #   calculates shapes and polygons on sphere
from folium.plugins import Draw, Geocoder, TimestampedGeoJson, HeatMap      
from streamlit_folium import st_folium          #   used to create geofences
import datetime
import geocoder                         #   search bar for geofence, api calls for address and ip lookups
import gpxpy
import numpy as np
from dateutil import parser
import xml.etree.ElementTree as ET
import zipfile
from functools import lru_cache
from typing import Optional
try:
    import pytz
except ImportError:
    pytz = None
import hashlib

# Safe session-state helpers: using st.session_state before Streamlit initializes
# can raise runtime errors in some reload/timing scenarios. These wrappers
# catch those exceptions and provide safe fallbacks.
def safe_session_get(key, default=None):
    try:
        return st.session_state.get(key, default)
    except Exception:
        return default

def safe_session_set(key, value):
    try:
        st.session_state[key] = value
    except Exception:
        pass

# --- Persistence helpers to avoid storing large objects in session_state (Streamlit Cloud) ---
import pickle
import gzip
import tempfile

def persist_object_to_tempfile(obj) -> Optional[str]:
    """Persist object to a gzipped pickle and return filepath, or None on failure."""
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pkl.gz')
        tmp.close()
        with gzip.open(tmp.name, 'wb') as fh:
            pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
        return tmp.name
    except Exception:
        try:
            if 'tmp' in locals() and os.path.exists(tmp.name):
                os.unlink(tmp.name)
        except Exception:
            pass
        return None

def load_persisted_object(path):
    """Load an object previously persisted with persist_object_to_tempfile. Return None on failure."""
    try:
        if not path or not isinstance(path, str):
            return None
        if not os.path.exists(path):
            return None
        with gzip.open(path, 'rb') as fh:
            return pickle.load(fh)
    except Exception:
        return None

# -------------------------------------------------------------
# Performance/Stability Helpers (added v5 PERF)
# -------------------------------------------------------------
# Centralize expensive regex compilation so they aren't recompiled each call
IPV4_REGEX = re.compile(r'(?:\d{1,3}\.){3}\d{1,3}\b')
IPV6_REGEX = re.compile(r'(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))')

def filter_valid_coordinates(df: pandas.DataFrame, lat_col: str = 'LATITUDE', lon_col: str = 'LONGITUDE'):
    """Return a cleaned copy of df with only valid numeric finite coordinates.

    This consolidates previously duplicated logic (numeric coercion, NaN/inf removal)
    and returns (clean_df, skipped_count).
    """
    if df is None or df.empty:
        return pandas.DataFrame(columns=df.columns if df is not None else []), 0
    working = df.copy()
    if lat_col not in working.columns or lon_col not in working.columns:
        return pandas.DataFrame(columns=working.columns), len(working)

    original = len(working)
    # Drop obvious nulls first
    working = working.dropna(subset=[lat_col, lon_col])
    # Coerce numeric
    working[lat_col] = pandas.to_numeric(working[lat_col], errors='coerce')
    working[lon_col] = pandas.to_numeric(working[lon_col], errors='coerce')
    # Remove NaN / inf
    working = working[
        working[lat_col].notna() & working[lon_col].notna() &
        np.isfinite(working[lat_col]) & np.isfinite(working[lon_col])
    ]
    clean = working.dropna(subset=[lat_col, lon_col]).reset_index(drop=True)
    return clean, (original - len(clean))


def detect_and_set_header_from_rows(df: pandas.DataFrame, max_search_rows: int = 15) -> pandas.DataFrame:
    """Inspect the first `max_search_rows` rows of `df` to find a row that contains
    both latitude and longitude column labels (case-insensitive). If found, promote
    that row to be the DataFrame header and drop all rows above it. If not found,
    ensure column names are strings so downstream .str operations won't fail.

    Detection uses simple word-boundary regex for 'lat'/'latitude' and 'lon'/'longitude'.
    """
    if df is None or df.empty:
        return df

    # Make a defensive copy for inspection
    working = df.copy().reset_index(drop=True)
    nrows = min(len(working), max_search_rows)
    lat_pattern = r"\blat\b|\blatitude\b"
    lon_pattern = r"\blon\b|\blongitude\b"

    header_row_idx = None
    for i in range(nrows):
        # convert row values to strings and lowercase for matching
        row = working.iloc[i].astype(str).fillna("").str.lower()
        has_lat = row.str.contains(lat_pattern, regex=True, na=False).any()
        has_lon = row.str.contains(lon_pattern, regex=True, na=False).any()
        if has_lat and has_lon:
            header_row_idx = i
            break

    if header_row_idx is not None:
        # Use that row as header
        new_columns = working.iloc[header_row_idx].astype(str).str.strip().tolist()
        new_df = working.iloc[header_row_idx + 1 :].copy().reset_index(drop=True)
        # Ensure column names are unique strings
        new_df.columns = [str(c) for c in new_columns]
        return new_df

    # If no header row found, convert existing column names to strings
    try:
        working.columns = [str(c) for c in working.columns]
    except Exception:
        pass
    return working

@st.cache_data(show_spinner=False)
def cached_ip_lookup(ip: str):
    """Cache individual IP lookups to avoid repeated API calls during a session."""
    try:
        return geocoder.ipinfo(ip).json
    except Exception:
        return None

now = datetime.datetime.now()
st.set_page_config(
   page_title="Fetch v5.3",
   #page_icon="🔴",
   layout="wide",
   initial_sidebar_state="expanded",
    menu_items={}
)
logo = ("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")
_hdr_col, _lang_col = st.columns([7, 1])
with _hdr_col:
    header_html = "<img src='data:image/png;base64,{}' class='img-fluid'>".format(logo)
    st.markdown(header_html, unsafe_allow_html=True)
with _lang_col:
    _LANG_OPTIONS = {"English": "en", "Español": "es", "Português": "pt", "Deutsch": "de", "Русский": "ru"}
    _lang_sel = st.selectbox("🌐", list(_LANG_OPTIONS.keys()), key="_ui_lang_sel", label_visibility="collapsed")
    st.session_state["_ui_lang_code"] = _LANG_OPTIONS[_lang_sel]
#Custom button color to bring prominence to executable actions

st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #ff0000;
            color:#ffffff;
        }
        div.stButton > button:hover {
            background-color: #8b0000;
            color:#ff0000;
            }
        </style>""", unsafe_allow_html=True)
#This removes Streamlit default settings icons
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: visible;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)



# Top-level Kepler export button removed. Use the Kepler download button shown below the embedded map.

### Global Variables ###
get_headings = ""
selected_encoding = ""
icon_options = ["Yellow Paddle", "Green Paddle", "Blue Paddle", "White Paddle", "Teal Paddle", "Red Paddle", "Yellow Pushpin", "White Pushpin", "Red Pushpin", "Square"]
selected_icon = {'Square' :'http://maps.google.com/mapfiles/kml/shapes/placemark_square.png','Yellow Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/ylw-pushpin.png",'Red Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png",'White Pushpin' : "http://maps.google.com/mapfiles/kml/pushpin/wht-pushpin.png",'Red Paddle' : "http://maps.google.com/mapfiles/kml/paddle/red-circle.png",'Green Paddle' : "http://maps.google.com/mapfiles/kml/paddle/grn-circle.png",'Blue Paddle' : "http://maps.google.com/mapfiles/kml/paddle/blu-circle.png",'Teal Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ltblu-circle.png",'Yellow Paddle' : "http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png",'White Paddle' : "http://maps.google.com/mapfiles/kml/paddle/wht-circle.png"}
invalid_ips = ['0', '10.', '127.0.0.1','172.16', '172.17', '172.18', '172.19', '172.2',  '172.21', '172.22', '172.23', '172.24', '172.25',
            '172.26', '172.27', '172.28', '172.29', '172.30',  '172.31', '192.168', '169.254', "255.255" ,"fc00"]

# ---------------- Hotspot / Clustering Helpers ----------------
def compute_hotspots(df: pandas.DataFrame, radius_m: float, min_samples: int, time_col: Optional[str], trim_chaining: bool = True):
    """Run DBSCAN (haversine) on LATITUDE/LONGITUDE columns (meters radius) and return
    (clusters_df, summary_df).

    Notes
    -----
    DBSCAN's notion of a cluster allows *chaining*: points can be connected via a series
    of <= eps links even if the overall diameter is >> eps. That can yield MAX_DISTANCE_M
    much larger than the user-selected radius. When trim_chaining is True we post-filter
    each cluster to retain only points within radius_m of the cluster centroid; any points
    outside are re-labelled as noise. Clusters falling below min_samples after trimming
    are discarded. This makes MAX_DISTANCE_M always <= radius_m (or very close due to
    floating error) and matches an intuitive "circular hotspot" expectation.
    """
    try:
        from sklearn.cluster import DBSCAN  # dynamic import in case installed after first run
    except Exception as e:
        raise RuntimeError("scikit-learn not available: install scikit-learn") from e

    earth_radius_m = 6371000.0
    eps = radius_m / earth_radius_m
    coords_rad = np.radians(df[['LATITUDE','LONGITUDE']].to_numpy())
    model = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine')
    labels = model.fit_predict(coords_rad)
    df = df.copy()
    df['HOTSPOT_ID'] = labels
    clusters = df[df['HOTSPOT_ID'] != -1].copy()
    if clusters.empty:
        return df, pandas.DataFrame(columns=['HOTSPOT_ID','COUNT','CENTER_LAT','CENTER_LON','MAX_DISTANCE_M','RADIUS_INPUT_M','FIRST_OBS','LAST_OBS'])

    earth_r = earth_radius_m
    summary_rows = []
    groupby = clusters.groupby('HOTSPOT_ID')
    # We may need to relabel after trimming; collect relabel operations
    relabel_noise_indices: list[int] = []
    for cid, grp in groupby:
        lat_mean = grp['LATITUDE'].mean(); lon_mean = grp['LONGITUDE'].mean()
        lat_mean_r, lon_mean_r = np.radians(lat_mean), np.radians(lon_mean)
        lat_vals = grp['LATITUDE'].to_numpy(); lon_vals = grp['LONGITUDE'].to_numpy()
        lat_r = np.radians(lat_vals); lon_r = np.radians(lon_vals)
        dlat = lat_r - lat_mean_r; dlon = lon_r - lon_mean_r
        a = np.sin(dlat/2)**2 + np.cos(lat_mean_r) * np.cos(lat_r) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        dists = earth_r * c  # meters from centroid
        if trim_chaining:
            keep_mask = dists <= radius_m * 1.0005  # small tolerance
            if not np.all(keep_mask):
                # mark dropped points (by original index) to become noise
                dropped = grp.loc[~keep_mask]
                relabel_noise_indices.extend(dropped.index.tolist())
                grp = grp.loc[keep_mask]
                dists = dists[keep_mask]
        # After optional trimming, maybe cluster too small
        if len(grp) < min_samples:
            # whole cluster becomes noise
            relabel_noise_indices.extend(grp.index.tolist())
            continue
        max_dist = float(dists.max()) if len(dists) else 0.0
        first_time = last_time = None
        if time_col and time_col in grp.columns:
            times = pandas.to_datetime(grp[time_col], errors='coerce').dropna()
            if not times.empty:
                first_time, last_time = times.min(), times.max()
        summary_rows.append({
            'HOTSPOT_ID': cid,
            'COUNT': len(grp),
            'CENTER_LAT': lat_mean,
            'CENTER_LON': lon_mean,
            'MAX_DISTANCE_M': round(max_dist,2),
            'RADIUS_INPUT_M': radius_m,
            'FIRST_OBS': first_time,
            'LAST_OBS': last_time
        })
    # Apply relabeling (set to noise)
    if relabel_noise_indices:
        df.loc[relabel_noise_indices, 'HOTSPOT_ID'] = -1
        clusters = df[df['HOTSPOT_ID'] != -1].copy()
        # Rebuild summary_df if we trimmed any clusters away entirely
        if relabel_noise_indices:
            # regenerate summary from summary_rows already filtered
            pass
    summary_df = pandas.DataFrame(summary_rows).sort_values(by='COUNT', ascending=False).reset_index(drop=True)
    return df, summary_df

# Cached wrapper so repeated UI reruns don't recompute unnecessarily
@st.cache_data(show_spinner=False)
def cached_compute_hotspots(df: pandas.DataFrame, radius_m: float, min_samples: int, time_col: Optional[str], trim_chaining: bool = True):
    return compute_hotspots(df, radius_m, min_samples, time_col, trim_chaining=trim_chaining)

# -------------------------------------------------------------
# Coordinate Format Conversion Helpers (Feature #6)
# -------------------------------------------------------------
# Patterns for DMS (Degrees, Minutes, Seconds) coordinates
# Examples: 40°44'54"N, 40° 44' 54" N, 40-44-54N, 40d44m54sN
DMS_PATTERN = re.compile(
    r'^\s*(?P<deg>-?\d{1,3})\s*[\xb0dD\-]\s*'
    r'(?P<min>\d{1,2})\s*[\'\u2018\u2019mM\-]\s*'
    r'(?P<sec>\d{1,2}(?:\.\d+)?)\s*["\u201c\u201dsS]?\s*'
    r'(?P<dir>[NSEWnsew])?\s*$',
    re.VERBOSE
)
# Pattern for DD MM.MMM (Degrees Decimal Minutes)
DDM_PATTERN = re.compile(
    r'^\s*(?P<deg>-?\d{1,3})\s*[\xb0dD\-]\s*'
    r'(?P<min>\d{1,2}(?:\.\d+)?)\s*[\'\u2018\u2019mM]?\s*'
    r'(?P<dir>[NSEWnsew])?\s*$',
    re.VERBOSE
)

def dms_to_decimal(deg: float, minutes: float, seconds: float, direction: str = '') -> float:
    """Convert DMS (Degrees, Minutes, Seconds) to decimal degrees."""
    decimal = abs(deg) + minutes / 60.0 + seconds / 3600.0
    if direction.upper() in ('S', 'W') or deg < 0:
        decimal = -decimal
    return decimal

def ddm_to_decimal(deg: float, minutes: float, direction: str = '') -> float:
    """Convert DDM (Degrees Decimal Minutes) to decimal degrees."""
    decimal = abs(deg) + minutes / 60.0
    if direction.upper() in ('S', 'W') or deg < 0:
        decimal = -decimal
    return decimal

def parse_coordinate_value(value) -> Optional[float]:
    """Try to parse a coordinate value from various formats.
    Supports: decimal degrees, DMS, DDM.
    Returns float (decimal degrees) or None if unparseable.
    """
    if value is None:
        return None
    # Already numeric
    if isinstance(value, (int, float)):
        if np.isfinite(value):
            return float(value)
        return None
    s = str(value).strip()
    if not s:
        return None
    # Try plain float first
    try:
        v = float(s)
        if np.isfinite(v):
            return v
        return None
    except ValueError:
        pass
    # Try DMS
    m = DMS_PATTERN.match(s)
    if m:
        return dms_to_decimal(
            float(m.group('deg')),
            float(m.group('min')),
            float(m.group('sec')),
            m.group('dir') or ''
        )
    # Try DDM
    m = DDM_PATTERN.match(s)
    if m:
        return ddm_to_decimal(
            float(m.group('deg')),
            float(m.group('min')),
            m.group('dir') or ''
        )
    return None

def convert_coordinate_column(series: pandas.Series) -> pandas.Series:
    """Convert a column of coordinates from any supported format to decimal degrees.
    Handles: decimal degrees, DMS, DDM. Non-convertible values become NaN.
    """
    return series.apply(parse_coordinate_value).astype(float)

def detect_coordinate_format(series: pandas.Series) -> str:
    """Detect the coordinate format of a pandas Series.
    Returns one of: 'decimal', 'dms', 'ddm', 'mixed', 'unknown'
    """
    sample = series.dropna().head(20)
    formats_found = set()
    for val in sample:
        s = str(val).strip()
        try:
            float(s)
            formats_found.add('decimal')
            continue
        except ValueError:
            pass
        if DMS_PATTERN.match(s):
            formats_found.add('dms')
        elif DDM_PATTERN.match(s):
            formats_found.add('ddm')
        else:
            formats_found.add('unknown')
    if len(formats_found) == 1:
        return formats_found.pop()
    elif len(formats_found) > 1 and 'unknown' not in formats_found:
        return 'mixed'
    elif 'unknown' in formats_found and len(formats_found) > 1:
        return 'mixed'
    return 'unknown'

# UTM conversion (basic zones 1-60, WGS84)
def utm_to_latlon(easting: float, northing: float, zone_number: int, zone_letter: str = 'N') -> tuple:
    """Convert UTM coordinates to latitude/longitude (WGS84).
    Simple implementation without external UTM library dependency.
    """
    # WGS84 parameters
    a = 6378137.0
    f = 1 / 298.257223563
    e = (2 * f - f ** 2) ** 0.5
    e_prime_sq = e ** 2 / (1 - e ** 2)

    # Determine hemisphere
    northern = zone_letter.upper() >= 'N'

    x = easting - 500000.0
    y = northing
    if not northern:
        y = y - 10000000.0

    lon0 = radians((zone_number - 1) * 6 - 180 + 3)

    M = y / 0.9996
    mu = M / (a * (1 - e**2/4 - 3*e**4/64 - 5*e**6/256))

    e1 = (1 - (1 - e**2)**0.5) / (1 + (1 - e**2)**0.5)
    phi1 = mu + (3*e1/2 - 27*e1**3/32) * sin(2*mu)
    phi1 += (21*e1**2/16 - 55*e1**4/32) * sin(4*mu)
    phi1 += (151*e1**3/96) * sin(6*mu)
    phi1 += (1097*e1**4/512) * sin(8*mu)

    N1 = a / (1 - e**2 * sin(phi1)**2)**0.5
    T1 = (sin(phi1) / cos(phi1))**2
    C1 = e_prime_sq * cos(phi1)**2
    R1 = a * (1 - e**2) / (1 - e**2 * sin(phi1)**2)**1.5
    D = x / (N1 * 0.9996)

    lat = phi1 - (N1 * (sin(phi1) / cos(phi1)) / R1) * (
        D**2/2 - (5 + 3*T1 + 10*C1 - 4*C1**2 - 9*e_prime_sq) * D**4/24
        + (61 + 90*T1 + 298*C1 + 45*T1**2 - 252*e_prime_sq - 3*C1**2) * D**6/720
    )
    lon = lon0 + (D - (1 + 2*T1 + C1) * D**3/6
                  + (5 - 2*C1 + 28*T1 - 3*C1**2 + 8*e_prime_sq + 24*T1**2) * D**5/120) / cos(phi1)

    return (degrees(lat), degrees(lon))

UTM_PATTERN = re.compile(
    r'^\s*(?P<zone>\d{1,2})\s*(?P<letter>[A-Za-z])\s+'
    r'(?P<easting>\d+(?:\.\d+)?)\s*[mM]?\s*[Ee]?\s+'
    r'(?P<northing>\d+(?:\.\d+)?)\s*[mM]?\s*[Nn]?\s*$'
)

def parse_utm_string(s: str) -> Optional[tuple]:
    """Parse a UTM string like '17T 630000 4833000' into (lat, lon) or None."""
    m = UTM_PATTERN.match(str(s).strip())
    if not m:
        return None
    try:
        zone = int(m.group('zone'))
        letter = m.group('letter')
        easting = float(m.group('easting'))
        northing = float(m.group('northing'))
        if 1 <= zone <= 60:
            return utm_to_latlon(easting, northing, zone, letter)
    except Exception:
        pass
    return None

# -------------------------------------------------------------
# Co-Location / Proximity Analysis (Feature #3)
# -------------------------------------------------------------
def haversine_distance_m(lat1, lon1, lat2, lon2):
    """Calculate haversine distance in meters between two points."""
    R = 6371000.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlam = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlam/2)**2
    return 2 * R * atan2(a**0.5, (1-a)**0.5)

def compute_colocation(df: pandas.DataFrame, time_col: str,
                       radius_m: float = 50.0, time_window_min: float = 10.0) -> pandas.DataFrame:
    """Detect co-location events between different source files.

    For each pair of source files, find records where two subjects were within
    `radius_m` meters of each other within `time_window_min` minutes.

    Returns a DataFrame of co-location events with columns:
    SOURCE_A, SOURCE_B, TIME_A, TIME_B, LAT_A, LON_A, LAT_B, LON_B,
    DISTANCE_M, TIME_DIFF_MIN, MIDPOINT_LAT, MIDPOINT_LON
    """
    if 'SOURCE_FILE' not in df.columns:
        return pandas.DataFrame()

    sources = df['SOURCE_FILE'].unique()
    if len(sources) < 2:
        return pandas.DataFrame()

    # Pre-parse datetimes
    working = df.copy()
    working['_PARSED_DT'] = pandas.to_datetime(working[time_col], errors='coerce')
    working = working.dropna(subset=['_PARSED_DT', 'LATITUDE', 'LONGITUDE'])
    working['LATITUDE'] = pandas.to_numeric(working['LATITUDE'], errors='coerce')
    working['LONGITUDE'] = pandas.to_numeric(working['LONGITUDE'], errors='coerce')
    working = working.dropna(subset=['LATITUDE', 'LONGITUDE'])
    working = working.sort_values('_PARSED_DT').reset_index(drop=True)

    time_delta = pandas.Timedelta(minutes=time_window_min)
    events = []

    source_list = sorted(sources)
    for i in range(len(source_list)):
        for j in range(i+1, len(source_list)):
            src_a = source_list[i]
            src_b = source_list[j]
            df_a = working[working['SOURCE_FILE'] == src_a].reset_index(drop=True)
            df_b = working[working['SOURCE_FILE'] == src_b].reset_index(drop=True)

            if df_a.empty or df_b.empty:
                continue

            # For each point in A, find points in B within the time window
            # Use vectorized pre-filtering by time, then check distance
            for _, row_a in df_a.iterrows():
                t_a = row_a['_PARSED_DT']
                lat_a, lon_a = row_a['LATITUDE'], row_a['LONGITUDE']

                time_mask = (df_b['_PARSED_DT'] >= t_a - time_delta) & (df_b['_PARSED_DT'] <= t_a + time_delta)
                candidates = df_b[time_mask]

                for _, row_b in candidates.iterrows():
                    lat_b, lon_b = row_b['LATITUDE'], row_b['LONGITUDE']
                    dist = haversine_distance_m(lat_a, lon_a, lat_b, lon_b)
                    if dist <= radius_m:
                        events.append({
                            'SOURCE_A': src_a,
                            'SOURCE_B': src_b,
                            'TIME_A': t_a,
                            'TIME_B': row_b['_PARSED_DT'],
                            'LAT_A': lat_a,
                            'LON_A': lon_a,
                            'LAT_B': lat_b,
                            'LON_B': lon_b,
                            'DISTANCE_M': round(dist, 2),
                            'TIME_DIFF_MIN': round(abs((t_a - row_b['_PARSED_DT']).total_seconds()) / 60, 2),
                            'MIDPOINT_LAT': (lat_a + lat_b) / 2,
                            'MIDPOINT_LON': (lon_a + lon_b) / 2,
                        })

    result = pandas.DataFrame(events)
    if not result.empty:
        result = result.sort_values('TIME_A').reset_index(drop=True)
    return result

@st.cache_data(show_spinner=False)
def cached_compute_colocation(df: pandas.DataFrame, time_col: str, radius_m: float, time_window_min: float):
    return compute_colocation(df, time_col, radius_m, time_window_min)

# -------------------------------------------------------------
# Stop / Dwell Detection (Feature #7)
# -------------------------------------------------------------
def compute_stops(df: pandas.DataFrame, time_col: str, radius_m: float = 50.0,
                  min_duration_min: float = 5.0, source_file: Optional[str] = None) -> pandas.DataFrame:
    """Detect stationary periods (stops/dwells) in location data.

    Groups consecutive points that stay within `radius_m` of their running centroid
    for at least `min_duration_min` minutes.

    Returns a DataFrame with columns:
    STOP_ID, CENTER_LAT, CENTER_LON, ARRIVAL, DEPARTURE, DURATION_MIN, POINT_COUNT, SOURCE_FILE
    """
    working = df.copy()
    working['_PARSED_DT'] = pandas.to_datetime(working[time_col], errors='coerce')
    working['LATITUDE'] = pandas.to_numeric(working['LATITUDE'], errors='coerce')
    working['LONGITUDE'] = pandas.to_numeric(working['LONGITUDE'], errors='coerce')
    working = working.dropna(subset=['_PARSED_DT', 'LATITUDE', 'LONGITUDE'])
    working = working.sort_values('_PARSED_DT').reset_index(drop=True)

    if working.empty:
        return pandas.DataFrame(columns=['STOP_ID','CENTER_LAT','CENTER_LON','ARRIVAL','DEPARTURE','DURATION_MIN','POINT_COUNT','SOURCE_FILE'])

    stops = []
    stop_id = 0
    i = 0
    n = len(working)

    while i < n:
        # Start a candidate stop
        cluster_lats = [working.at[i, 'LATITUDE']]
        cluster_lons = [working.at[i, 'LONGITUDE']]
        cluster_start = working.at[i, '_PARSED_DT']
        cluster_end = cluster_start
        j = i + 1

        while j < n:
            lat_j = working.at[j, 'LATITUDE']
            lon_j = working.at[j, 'LONGITUDE']
            centroid_lat = np.mean(cluster_lats)
            centroid_lon = np.mean(cluster_lons)
            dist = haversine_distance_m(centroid_lat, centroid_lon, lat_j, lon_j)

            if dist <= radius_m:
                cluster_lats.append(lat_j)
                cluster_lons.append(lon_j)
                cluster_end = working.at[j, '_PARSED_DT']
                j += 1
            else:
                break

        duration = (cluster_end - cluster_start).total_seconds() / 60.0
        point_count = j - i

        if duration >= min_duration_min and point_count >= 2:
            stops.append({
                'STOP_ID': stop_id,
                'CENTER_LAT': round(np.mean(cluster_lats), 6),
                'CENTER_LON': round(np.mean(cluster_lons), 6),
                'ARRIVAL': cluster_start,
                'DEPARTURE': cluster_end,
                'DURATION_MIN': round(duration, 2),
                'POINT_COUNT': point_count,
                'SOURCE_FILE': source_file or (working.at[i, 'SOURCE_FILE'] if 'SOURCE_FILE' in working.columns else '')
            })
            stop_id += 1

        i = j if j > i else i + 1

    return pandas.DataFrame(stops)

@st.cache_data(show_spinner=False)
def cached_compute_stops(df: pandas.DataFrame, time_col: str, radius_m: float,
                         min_duration_min: float, source_file: Optional[str] = None):
    return compute_stops(df, time_col, radius_m, min_duration_min, source_file)

# -------------------------------------------------------------
# EXIF Photo Location Import (Feature #13)
# -------------------------------------------------------------
def extract_exif_gps(file_bytes: bytes, filename: str = '') -> Optional[dict]:
    """Extract GPS coordinates and metadata from a JPEG/TIFF image's EXIF data.
    Returns dict with LATITUDE, LONGITUDE, DATETIME, FILENAME or None.
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        import io

        img = Image.open(io.BytesIO(file_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return None

        gps_info = {}
        datetime_original = None

        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, tag_id)
            if tag_name == 'GPSInfo':
                for gps_tag_id, gps_value in value.items():
                    gps_tag_name = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag_name] = gps_value
            elif tag_name == 'DateTimeOriginal':
                datetime_original = value
            elif tag_name == 'DateTime' and datetime_original is None:
                datetime_original = value

        if not gps_info:
            return None

        # Extract latitude
        lat_data = gps_info.get('GPSLatitude')
        lat_ref = gps_info.get('GPSLatitudeRef', 'N')
        lon_data = gps_info.get('GPSLongitude')
        lon_ref = gps_info.get('GPSLongitudeRef', 'E')

        if not lat_data or not lon_data:
            return None

        def gps_to_decimal(gps_coords, ref):
            """Convert GPS EXIF format to decimal degrees."""
            try:
                d = float(gps_coords[0])
                m = float(gps_coords[1])
                s = float(gps_coords[2])
                decimal = d + m/60.0 + s/3600.0
                if ref in ('S', 'W'):
                    decimal = -decimal
                return decimal
            except (TypeError, IndexError, ValueError):
                return None

        lat = gps_to_decimal(lat_data, lat_ref)
        lon = gps_to_decimal(lon_data, lon_ref)

        if lat is None or lon is None:
            return None

        result = {
            'LATITUDE': lat,
            'LONGITUDE': lon,
            'FILENAME': filename,
        }

        # Parse datetime if available
        if datetime_original:
            try:
                # EXIF datetime format: "2024:01:15 14:30:00"
                dt = datetime.datetime.strptime(datetime_original, '%Y:%m:%d %H:%M:%S')
                result['DATETIME'] = dt
            except (ValueError, TypeError):
                result['DATETIME'] = None
        else:
            result['DATETIME'] = None

        # Extract altitude if available
        alt = gps_info.get('GPSAltitude')
        alt_ref = gps_info.get('GPSAltitudeRef', 0)
        if alt is not None:
            try:
                altitude = float(alt)
                if alt_ref == 1:  # below sea level
                    altitude = -altitude
                result['ELEVATION'] = altitude
            except (TypeError, ValueError):
                pass

        # Extract bearing/direction if available
        img_dir = gps_info.get('GPSImgDirection')
        if img_dir is not None:
            try:
                result['BEARING'] = float(img_dir)
            except (TypeError, ValueError):
                pass

        return result

    except ImportError:
        return None
    except Exception:
        return None

def ingest_photos(uploaded_photos) -> Optional[pandas.DataFrame]:
    """Process uploaded photo files and extract GPS data.
    Returns DataFrame with LATITUDE, LONGITUDE, DATETIME, FILENAME, etc.
    """
    if not uploaded_photos:
        return None

    records = []
    errors = []
    for photo in uploaded_photos:
        try:
            photo.seek(0)
            photo_bytes = photo.read()
            result = extract_exif_gps(photo_bytes, photo.name)
            if result:
                records.append(result)
            else:
                errors.append(photo.name)
        except Exception as e:
            errors.append(f"{photo.name}: {str(e)}")

    if errors:
        st.warning(f"No GPS data found in {len(errors)} photo(s): {', '.join(errors[:5])}" +
                   (f"... and {len(errors)-5} more" if len(errors) > 5 else ""))

    if not records:
        return None

    df = pandas.DataFrame(records)
    return df


def render_tactical_clock(points_df: pandas.DataFrame, time_col: str, title: str = "Tactical Clock", height: int = 520,
                          center_lat: Optional[float] = None, center_lon: Optional[float] = None, radius_m: Optional[float] = None,
                          visits: Optional[int] = None, max_distance_m: Optional[float] = None,
                          first_obs: Optional[pandas.Timestamp] = None, last_obs: Optional[pandas.Timestamp] = None):
    """Polar day/time chart with equal day wedges and radial hours.
    - Angular: 7 equal wedges (Mon..Sun clockwise)
    - Radial: hour (0 center -> 24 outer)
    - Color: count of observations for (day, hour)
    """
    if time_col not in points_df.columns:
        return
    times = pandas.to_datetime(points_df[time_col], errors='coerce').dropna()
    if times.empty:
        return
    day_idx = times.dt.dayofweek.to_numpy()  # 0=Mon
    hours = times.dt.hour.to_numpy()
    counts = np.zeros((7,24), dtype=int)
    for d, h in zip(day_idx, hours):
        counts[d, h] += 1
    max_count = counts.max()
    if max_count == 0:
        return
    try:
        import plotly.graph_objects as go
    except Exception:
        st.warning("Plotly not installed; tactical clock unavailable.")
        return
    day_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    day_wedge = 360/7
    thetas = []
    rs = []
    bases = []
    widths = []
    colors = []
    texts = []
    for d in range(7):
        theta_center = d*day_wedge + day_wedge/2
        for h in range(24):
            c = counts[d, h]
            thetas.append(theta_center)
            bases.append(h)
            rs.append(1)  # 1 hour thickness
            widths.append(day_wedge * 0.90)  # a touch more gap to reduce visual crowding
            colors.append(c)
            texts.append(f"Day: {day_names[d]}<br>Hour: {h:02d}:00<br>Count: {c}")
    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        theta=thetas,
        r=rs,
        base=bases,
        width=widths,
        marker=dict(
            color=colors,
            colorscale='Viridis',
            cmin=0,
            cmax=max_count if max_count>0 else 1,
            line=dict(color='#222', width=0.3),
            colorbar=dict(
                title='Count',
                orientation='h',
                x=0.5,
                y=-0.18,
                xanchor='center',
                yanchor='top',
                len=0.55,
                thickness=12
            )
        ),
        hovertemplate="%{text}<extra></extra>",
        text=texts
    ))
    day_tick_vals = [d*day_wedge + day_wedge/2 for d in range(7)]
    radial_ticks = list(range(0,25,3))
    # Build info block (embedded into title for PNG export completeness)
    info_lines = []
    if center_lat is not None and center_lon is not None:
        info_lines.append(f"Center {center_lat:.5f}, {center_lon:.5f}")
    if radius_m is not None:
        info_lines.append(f"Radius {int(radius_m)}m")
    if visits is not None:
        info_lines.append(f"Visits {visits}")
    if max_distance_m is not None:
        info_lines.append(f"MaxDist {max_distance_m}m")
    # Time window
    if first_obs is not None and last_obs is not None:
        try:
            fstr = pandas.to_datetime(first_obs).strftime('%Y-%m-%d %H:%M')
            lstr = pandas.to_datetime(last_obs).strftime('%Y-%m-%d %H:%M')
            info_lines.append(f"Span {fstr} → {lstr}")
        except Exception:
            pass
    info_html = " | ".join(info_lines)
    title_html = title if not info_html else f"{title}<br><span style='font-size:12px;color:#bbb'>{info_html}</span>"
    fig.update_layout(
        title={'text': title_html, 'x':0.5, 'xanchor':'center'},
        polar=dict(
            bgcolor='#0d0d0d',
            angularaxis=dict(
                direction='clockwise',
                rotation=90,
                tickmode='array',
                tickvals=day_tick_vals,
                ticktext=day_names,
                gridcolor='#222',
                tickfont=dict(size=13, color='#ddd')
            ),
            radialaxis=dict(
                range=[0,24.8],  # extend slightly to give day labels breathing room
                tickmode='array',
                tickvals=radial_ticks,
                ticktext=[str(t) for t in radial_ticks],
                tickfont=dict(size=10, color='#aaa'),
                angle=0,
                gridcolor='#222'
            )
        ),
    margin=dict(l=25, r=25, t=90 if info_html else 60, b=70),
        template='plotly_dark',
        height=height,
    annotations=[]
    )
    # Remove unusable zoom/pan controls while retaining image download & fullscreen
    remove_buttons = [
        'zoom2d','pan2d','select2d','lasso2d','zoomIn2d','zoomOut2d','autoScale2d','resetScale2d'
    ]
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            'displaylogo': False,
            'modeBarButtonsToRemove': remove_buttons,
            'responsive': True
        }
    )

####    Functions Live Here     ######

def add_color_legend(Map, df):
    """
    Adds a color legend to the map for multiple data sources
    """
    if 'SOURCE_FILE' in df.columns and 'POINT_COLOR' in df.columns:
        # Get unique combinations of source files and colors
        legend_items = df[['SOURCE_FILE', 'POINT_COLOR']].drop_duplicates()
        
        # Create HTML for the legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 10px; 
                    right: 10px; 
                    z-index: 1000;
                    background-color: #333333;
                    color: white;
                    padding: 5px;
                    border-radius: 5px;
                    border: 2px solid grey;
                    ">
        <h5>Data Sources</h5>
        '''
        
        # Add each source file and its color to the legend
        for _, row in legend_items.iterrows():
            legend_html += f'''
            <div style="display: flex; align-items: center; margin: 5px;">
                <div style="width: 15px; 
                           height: 15px; 
                           background-color: {row['POINT_COLOR']}; 
                           border-radius: 50%;
                           margin-right: 5px;">
                </div>
                <span>{row['SOURCE_FILE']}</span>
            </div>
            '''
        
        legend_html += '</div>'
        
        # Add the legend to the map
        Map.get_root().html.add_child(folium.Element(legend_html))

def get_bounds(feature_collection):
    """Calculate bounds from feature collection"""
    lats = []
    lngs = []
    
    for feature in feature_collection['features']:
        coords = feature['geometry']['coordinates']
        for coord in coords:
            lats.append(coord[1])
            lngs.append(coord[0])
            
    return [[min(lats), min(lngs)], [max(lats), max(lngs)]]


def convert_to_datetime_and_string(timestamp_string):  # function takes a timestamp string and converts to datetime and a uniform string output
    # parses the timestamp string into a datetime object
    datetime_value = parser.parse(timestamp_string)

    # Formats the datetime object into the desired string format
    formatted_string = datetime_value.strftime("%Y-%m-%dT%H:%M:%S")

    return datetime_value, formatted_string

def get_point_at_distance(lat1, lon1, d, bearing, R=6371):  # used to draw tower wedges
    """
    lat: initial latitude, in degrees
    lon: initial longitude, in degrees
    d: target distance from initial
    bearing: (true) heading in degrees
    R: optional radius of sphere, defaults to mean radius of earth

    Returns new lat/lon coordinate {d}km from initial, in degrees
    """
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    a = radians(bearing)
    lat2 = asin(sin(lat1) * cos(d/R) + cos(lat1) * sin(d/R) * cos(a))
    lon2 = lon1 + atan2(
        sin(a) * sin(d/R) * cos(lat1),
        cos(d/R) - sin(lat1) * sin(lat2)
    )
    return (degrees(lat2), degrees(lon2),)

def make_geofence_map():
    # --- Geofence Manager State ---
    if safe_session_get('geofences') is None:
        safe_session_set('geofences', [])  # list of dicts: id,name,color,geometry(type,wkt),created,updated,active,notes
    if safe_session_get('geofence_counter') is None:
        safe_session_set('geofence_counter', 1)

    help_Box = st.expander(label="Help")
    with help_Box:
        st.markdown("""
        Welcome to Fetch! This area is used to create geofences. To upload location data use the input area above.
        - Use the draw toolbar on the map (polygon/rectangle). 
        - Search for a street address or get the map of an IP address. See the IP address mapping tab to carry out bulk searches.
        """)

    # Search / locate
    with st.form("geoform"):
        user_geo_input = st.text_input(t("lbl_search_addr_ip"), placeholder="123 Main St or 8.8.8.8")
        search = st.form_submit_button("Locate")

    # Initialize session state for caching geocoding results
    if safe_session_get('cached_geocode_result') is None:
        safe_session_set('cached_geocode_result', None)
    if safe_session_get('cached_search_term') is None:
        safe_session_set('cached_search_term', None)

    # Initialize with neutral continental US view; we'll optionally recenter below
    geomap = folium.Map(zoom_start=4, location=[39,-98])
    Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                     attr='Esri', name='Esri Satellite', overlay=False, control=True).add_to(geomap)
    folium.LayerControl(position="topright", collapsed=True).add_to(geomap)

    # Geocode/IP locate - Only run when search button is clicked
    if search and user_geo_input:
        ipv4_ipv6_regex = r"(^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$)"

        # Check if we need to make a new API call
        # Use safe_session_get to avoid KeyError if cached_search_term is missing between reruns
        if user_geo_input != safe_session_get('cached_search_term'):
            if re.search(ipv4_ipv6_regex, user_geo_input):
                try:
                    st.info("🔍 Looking up IP address... (API call)")
                    ip_res = geocoder.ipinfo(user_geo_input)
                    if ip_res and ip_res.latlng:
                        # Cache the successful result
                        safe_session_set('cached_geocode_result', {
                            'type': 'ip',
                            'data': ip_res,
                            'input': user_geo_input
                        })
                        safe_session_set('cached_search_term', user_geo_input)
                        st.success("✅ IP address located successfully!")
                    else:
                        st.error("❌ Could not locate IP address")
                        safe_session_set('cached_geocode_result', None)
                        safe_session_set('cached_search_term', None)
                except Exception as e:
                    st.error(f"❌ IP lookup failed: {str(e)}")
                    safe_session_set('cached_geocode_result', None)
                    safe_session_set('cached_search_term', None)
            else:
                try:
                    st.info("🔍 Looking up address... (API call)")
                    geo_res = geocoder.arcgis(user_geo_input)
                    if geo_res and geo_res.latlng:
                        # Cache the successful result
                        safe_session_set('cached_geocode_result', {
                            'type': 'address',
                            'data': geo_res,
                            'input': user_geo_input
                        })
                        safe_session_set('cached_search_term', user_geo_input)
                        st.success("✅ Address located successfully!")
                    else:
                        st.error("❌ Could not locate address")
                        safe_session_set('cached_geocode_result', None)
                        safe_session_set('cached_search_term', None)
                except Exception as e:
                    st.error(f"❌ Address lookup failed: {str(e)}")
                    safe_session_set('cached_geocode_result', None)
                    safe_session_set('cached_search_term', None)
        else:
            st.info("📋 Using cached result (no API call needed)")

    # Display cached results if available (use .get() to avoid KeyError)
    if safe_session_get('cached_geocode_result'):
        cached_result = safe_session_get('cached_geocode_result')
        
        if cached_result['type'] == 'ip':
            ip_res = cached_result['data']
            user_geo_input = cached_result['input']
            
            # Format geocoder response for better readability
            st.write("**IP Geolocation Results - Location represents an estimated geographic area and does not indicate the point of usage.**")
            
            # Create organized display of key information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Location Information:**")
                location_info = {
                    "IP Address": getattr(ip_res, 'ip', user_geo_input),
                    "City": getattr(ip_res, 'city', 'Not available'),
                    "State/Region": getattr(ip_res, 'state', 'Not available'), 
                    "Country": getattr(ip_res, 'country', 'Not available'),
                    "Postal Code": getattr(ip_res, 'postal', 'Not available'),
                    "Coordinates": f"{ip_res.latlng[0]:.6f}, {ip_res.latlng[1]:.6f}",
                    "Timezone": getattr(ip_res, 'timezone', 'Not available')
                }
                for key, value in location_info.items():
                    st.write(f"• **{key}:** {value}")
            
            with col2:
                st.write("**🌐 Network Information:**")
                network_info = {
                    "Organization": getattr(ip_res, 'org', 'Not available'),
                    "Status": getattr(ip_res, 'status', 'Unknown'),
                    "Provider": ip_res.provider if hasattr(ip_res, 'provider') else 'ipinfo.io'
                }
                for key, value in network_info.items():
                    st.write(f"• **{key}:** {value}")
            
            # Show raw data in an expandable section
            with st.expander("🔧 Raw Geocoder Data (Debug)"):
                # Show all available attributes in a more organized way
                all_attrs = {}
                for attr in dir(ip_res):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(ip_res, attr)
                            if not callable(value):
                                all_attrs[attr] = value
                        except Exception:
                            pass
                st.json(all_attrs)
            
            # Rebuild map centered on result
            geomap = folium.Map(location=ip_res.latlng, zoom_start=11)
            Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
            folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                             attr='Esri', name='Esri Satellite', overlay=False, control=True).add_to(geomap)
            folium.LayerControl(position="topright", collapsed=True).add_to(geomap)
            
            # Create enhanced popup with correct field names
            popup_content = f"""
            <div style="width: 350px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">🌐 IP Geolocation Details</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">IP Address:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'ip', user_geo_input)}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Location:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'city', 'Unknown')}, {getattr(ip_res, 'state', 'Unknown')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Country:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'country', 'Unknown')}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Postal Code:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'postal', 'N/A')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Coordinates:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{ip_res.latlng[0]:.6f}, {ip_res.latlng[1]:.6f}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Organization:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'org', 'Unknown')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Timezone:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(ip_res, 'timezone', 'Unknown')}</td></tr>
                </table>
                <div style="margin-top: 8px; font-size: 11px; color: #6c757d; text-align: center;">
                    Data provided by {getattr(ip_res, 'provider', 'ipinfo.io')}
                </div>
            </div>
            """
            
            # Add enhanced marker
            folium.Marker(
                location=ip_res.latlng, 
                tooltip=f"🌐 {getattr(ip_res, 'ip', user_geo_input)} - {getattr(ip_res, 'city', 'Unknown')}, {getattr(ip_res, 'state', 'Unknown')}",
                popup=folium.Popup(popup_content, max_width=400),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(geomap)

            
        elif cached_result['type'] == 'address':
            geo_res = cached_result['data']
            user_geo_input = cached_result['input']
            
            # Format geocoder response for better readability
            st.write("**🔍 Address Geolocation Results:**")
            
            # Create organized display of key information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**📍 Location Information:**")
                location_info = {
                    "Search Term": user_geo_input,
                    "Full Address": getattr(geo_res, 'address', 'Not available'),
                    "City": getattr(geo_res, 'city', 'Not available'),
                    "State": getattr(geo_res, 'state', 'Not available'),
                    "Country": getattr(geo_res, 'country', 'Not available'),
                    "Postal Code": getattr(geo_res, 'postal', 'Not available'),
                    "Coordinates": f"{geo_res.latlng[0]:.6f}, {geo_res.latlng[1]:.6f}"
                }
                for key, value in location_info.items():
                    st.write(f"• **{key}:** {value}")
            
            with col2:
                st.write("**🎯 Accuracy Information:**")
                accuracy_info = {
                    "Confidence": getattr(geo_res, 'confidence', 'Not available'),
                    "Provider": geo_res.provider if hasattr(geo_res, 'provider') else 'ArcGIS',
                    "Status": getattr(geo_res, 'status', 'Unknown')
                }
                for key, value in accuracy_info.items():
                    st.write(f"• **{key}:** {value}")
            
            # Show raw data in an expandable section
            with st.expander("🔧 Raw Geocoder Data (Debug)"):
                all_attrs = {}
                for attr in dir(geo_res):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(geo_res, attr)
                            if not callable(value):
                                all_attrs[attr] = value
                        except Exception:
                            pass
                st.json(all_attrs)
            
            geomap = folium.Map(location=geo_res.latlng, zoom_start=16)
            Draw(export=True, draw_options={'circle': False,'circlemarker':False, 'marker':False}).add_to(geomap)
            folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                             attr='Esri', name='Esri Satellite', overlay=False, control=True).add_to(geomap)
            folium.LayerControl(position="topright", collapsed=True).add_to(geomap)
            
            # Create enhanced popup for address
            popup_content = f"""
            <div style="width: 350px; font-family: Arial, sans-serif;">
                <h4 style="margin: 0 0 10px 0; color: #2c3e50;">📍 Address Details</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Search Term:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{user_geo_input}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Full Address:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'address', 'Not available')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">City:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'city', 'Unknown')}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">State:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'state', 'Unknown')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Country:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'country', 'Unknown')}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Postal Code:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'postal', 'N/A')}</td></tr>
                    <tr style="background-color: #f8f9fa;"><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Coordinates:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{geo_res.latlng[0]:.6f}, {geo_res.latlng[1]:.6f}</td></tr>
                    <tr><td style="font-weight: bold; padding: 5px; border: 1px solid #dee2e6;">Confidence:</td><td style="padding: 5px; border: 1px solid #dee2e6;">{getattr(geo_res, 'confidence', 'Unknown')}</td></tr>
                </table>
                <div style="margin-top: 8px; font-size: 11px; color: #6c757d; text-align: center;">
                    Data provided by {getattr(geo_res, 'provider', 'ArcGIS')}
                </div>
            </div>
            """
            
            # Add enhanced marker
            folium.Marker(
                location=geo_res.latlng, 
                tooltip=f"📍 {getattr(geo_res, 'address', user_geo_input)}",
                popup=folium.Popup(popup_content, max_width=400),
                icon=folium.Icon(color='red', icon='map-marker')
            ).add_to(geomap)
            
        
    # Render existing saved geofences
    bounds_points = []
    geofences_list = safe_session_get('geofences') or []
    if geofences_list:
        for g in geofences_list:
            if not g.get('active'):  # skip inactive
                continue
            try:
                feature = {
                    'type': 'Feature',
                    'geometry': {'type': g['type'], 'coordinates': g['coordinates']},
                    'properties': {'name': g['name']}
                }
                folium.GeoJson(
                    feature,
                    name=g['name'],
                    tooltip=g['name'],
                    style_function=lambda feat, col=g['color']: {
                        'color': col,
                        'weight': 2,
                        'fillColor': col,
                        'fillOpacity': 0.15
                    }
                ).add_to(geomap)
                # Collect bounds points for recentering
                geom_type = g['type']
                coords = g['coordinates']
                if geom_type == 'Polygon':
                    for lon, lat in coords[0]:
                        bounds_points.append((lat, lon))
                elif geom_type == 'LineString':
                    for lon, lat in coords:
                        bounds_points.append((lat, lon))
                elif geom_type == 'Point':
                    lon, lat = coords
                    bounds_points.append((lat, lon))
            except Exception:
                continue

    # Include current drawing in bounds
    last_geojson_temp = None
    try:
        last_geojson_temp = safe_session_get('last_drawn_raw')
    except Exception:
        last_geojson_temp = None

    # Fallback: attempt to get from current output later; we will set after outputmap if needed.
    
    # Try to render interactive folium via streamlit_folium; if the component fails to load
    # (common on deployments where the frontend component isn't available), fall back to
    # embedding the map HTML. This avoids the "component failed to load" reset loop.
    outputmap = None
    try:
        outputmap = st_folium(geomap, width=1100, height=600, key="geofence_map")
    except Exception as e:
        # Log the error for debugging but don't crash the app; render HTML fallback.
        try:
            st.warning("streamlit_folium component failed to load; falling back to static HTML rendering.")
        except Exception:
            pass
        try:
            # Render map HTML as a safe fallback. This won't provide the drawing callbacks
            # that st_folium exposes, so we attempt to preserve the last drawn geometry
            # from session_state instead of relying on the component.
            html = geomap._repr_html_()
            import streamlit.components.v1 as components
            components.html(html, height=600, scrolling=True)
        except Exception:
            # If even HTML rendering fails, show a placeholder message.
            try:
                st.error("Unable to render the map via streamlit_folium or HTML fallback.")
            except Exception:
                pass

    # Capture last drawn geometry. If we used the HTML fallback, prefer the last stored drawing
    # from session_state because the fallback doesn't provide live drawing callbacks.
    last_geojson = None
    try:
        if isinstance(outputmap, dict):
            last_geojson = outputmap.get('last_active_drawing')
        if not last_geojson:
            # fallback to any previously stored drawing
            last_geojson = safe_session_get('last_drawn_raw')
    except Exception:
        last_geojson = safe_session_get('last_drawn_raw')
    if last_geojson:
        safe_session_set('last_drawn_raw', last_geojson)
        # Update bounds with current drawing
        try:
            g_t = last_geojson.get('geometry', {}).get('type')
            g_c = last_geojson.get('geometry', {}).get('coordinates')
            if g_t == 'Polygon':
                for lon, lat in g_c[0]:
                    bounds_points.append((lat, lon))
            elif g_t == 'LineString':
                for lon, lat in g_c:
                    bounds_points.append((lat, lon))
            elif g_t == 'Point':
                lon, lat = g_c
                bounds_points.append((lat, lon))
        except Exception:
            pass

    # Fit bounds if we have enough points and map still default
    if bounds_points:
        try:
            lats = [p[0] for p in bounds_points]
            lons = [p[1] for p in bounds_points]
            sw = (min(lats), min(lons))
            ne = (max(lats), max(lons))
            # Add a slight padding
            pad_lat = (ne[0]-sw[0]) * 0.05 if ne[0]!=sw[0] else 0.01
            pad_lon = (ne[1]-sw[1]) * 0.05 if ne[1]!=sw[1] else 0.01
            geomap.fit_bounds([[sw[0]-pad_lat, sw[1]-pad_lon], [ne[0]+pad_lat, ne[1]+pad_lon]])
        except Exception:
            pass

    st.markdown("### Current Drawing (Instant Coordinates)")
    coord_list = []
    g_type = None
    if last_geojson:
        geom_obj = last_geojson.get('geometry', {})
        g_type = geom_obj.get('type')
        raw_coords = geom_obj.get('coordinates')
        try:
            if g_type == 'Polygon' and raw_coords:
                for lon, lat in raw_coords[0]:
                    coord_list.append((lat, lon))
            elif g_type == 'LineString' and raw_coords:
                for lon, lat in raw_coords:
                    coord_list.append((lat, lon))
            elif g_type == 'Point' and raw_coords:
                lon, lat = raw_coords
                coord_list.append((lat, lon))
        except Exception:
            coord_list = []

    if coord_list:
        coords_text = "Latitude, Longitude\n" + "\n".join(f"{lat}, {lon}" for lat, lon in coord_list)
        st.caption(f"Geometry: {g_type} | Vertices: {len(coord_list)}")
        st.text_area("Coordinates", value=coords_text, height=160, key="coord_display", help="Copy / paste ready")
        colx1, colx2, colx3 = st.columns(3)
        with colx1:
            st.download_button("Download TXT", data=coords_text, file_name="geofence_coordinates.txt")
        with colx2:
            # Quick GeoJSON export of just this drawing
            import json as _json
            feature = {
                "type":"FeatureCollection",
                "features":[{"type":"Feature","geometry":{"type":g_type,"coordinates":last_geojson['geometry']['coordinates']},"properties":{}}]
            }
            st.download_button("Download GeoJSON", data=_json.dumps(feature), file_name="geofence.geojson")
        with colx3:
            # KML (very simple) if polygon
            if g_type == 'Polygon':
                kml_coords = " ".join(f"{lon},{lat},0" for lat, lon in coord_list)
                kml = f"""<?xml version='1.0' encoding='UTF-8'?>\n<kml xmlns='http://www.opengis.net/kml/2.2'>\n<Document><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>{kml_coords}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></Document></kml>"""
                st.download_button("Download KML", data=kml, file_name="geofence.kml")
            else:
                st.write(" ")
    else:
        st.info("Draw a shape (polygon/rectangle) to see coordinates below the map instantly.")

    # Advanced save/manage block removed per user request.

    # (Removed list management per user request)

    # Removed planned feature caption to declutter UI.


def parse_text_for_IPs(text):  #used to map ips
    # Use precompiled regex objects for performance
    ipv4_addresses = IPV4_REGEX.findall(text)
    ipv6_addresses = IPV6_REGEX.findall(text)
    
    ipv6_list = []
    ip_list = list(set(ipv4_addresses))

    for address in ipv6_addresses:
        clean_ipv6 = [item for item in address if len(item) > 16]
        if clean_ipv6:      # checks for empty lists
            ipv6_list.append(clean_ipv6)
    unique_ip6_list = [str(inner_list[0]) for inner_list in ipv6_list]
    unique_ip6_list = list(set(unique_ip6_list))
    ip_list.extend(unique_ip6_list)
    return ip_list

def get_IP_locale(invalidList, IPs):
    """Used to map IPs with better handling of API limits"""
    valid_only = [address for address in IPs if not any(address.startswith(inval) for inval in invalidList)]
    
    # Counter for successful lookups
    lookup_count = 0
    api_limit = 1000  # Daily limit for free tier
    results = []
    for ip in valid_only:
        try:
            data = cached_ip_lookup(ip)
            if not data:
                continue
            # Check for rate limit hint
            if isinstance(data, dict) and data.get('status_code') == 429:
                st.error(f"🚫 IP lookup limit reached (Error 429). Daily free limit ~{api_limit}. Try later or consider sponsored expansion.")
                break
            results.append(data)
            lookup_count += 1
            if lookup_count % 25 == 0:
                st.info(f"Processed {lookup_count} IPs...")
        except Exception as e:
            st.warning(f"⚠️ Error processing IP {ip}: {e}")
    # Return results directly (no global mutation)
    return results

def geo_ip_to_Dataframe(geo_list):  #used to map ips
    df = pandas.json_normalize(geo_list)
    df = df.dropna(how='all') #removes entirely empty rows
    columns = df.columns
    columnnamelist = []
    for name in columns:
        columnnamelist.append(name.upper())
    df.columns = columnnamelist
    df.rename(columns={"IP": 'IP ADDRESS','LAT': 'LATITUDE', 'LNG': "LONGITUDE", 'ORG': "SERVICE PROVIDER"}, inplace=True)
    return (df)

def convert_df(df):
    return df.to_csv().encode('utf-8')
def make_IPaddress_Map():   #used to map ips
    # help_Box = st.expander(label="Help")
    user_location = st.text_input("Place Name or Address - Use to Add a Relevant Location to the Map (Place e-mail received, point of comparison, etc)")
    ipdata = st.text_area("Input Data with IP Addresses or an E-Mail Header",height=200)
    ip_geo_button = st.button(t("btn_search"))
    

    if ip_geo_button == True:
        
        search_geo_results = geocoder.arcgis(user_location)
        search_latlng = search_geo_results.json
        # print(search_latlng)
        
        try:
            parsed_IPs = parse_text_for_IPs(ipdata) # Parses text for IP addresses
            ip_results = get_IP_locale(invalid_ips, parsed_IPs)  # Filters out local ip and keeps valid public ips
            datfram = geo_ip_to_Dataframe(geo_list=ip_results)  
            if datfram.empty:
                st.warning("Warning: No values resembling public IP addresses were found. Check the submitted data.")
              
            show_these = ('IP ADDRESS', 'STATUS','SERVICE PROVIDER', 'CITY', 'STATE', 'COUNTRY','LATITUDE', 'LONGITUDE')
            # show_these = None
            st.dataframe(data=datfram,hide_index=True,column_order=show_these) 
            csv = convert_df(datfram)
            st.download_button(label="Download as CSV",
                            data=csv,
                            file_name='Fetch_IP_Lookup.csv',
                            mime='text/csv',
                            )   
        
            cleandf, skipped_count = filter_valid_coordinates(datfram, 'LATITUDE', 'LONGITUDE')
            valid_count = len(cleandf)
            cleandf = cleandf.reset_index(drop=True)
            
            if skipped_count > 0:
                st.warning(f"⚠️ Skipped {skipped_count} IP record(s) that were missing latitude or longitude values. {valid_count} valid records will be processed.")
            
            if valid_count == 0:
                st.error("No valid IP records found with location data.")
                return
            
            gdf = geopandas.GeoDataFrame(cleandf, geometry=geopandas.points_from_xy(cleandf.LONGITUDE, cleandf.LATITUDE))
        except KeyError:
            print("key error in makeipaddressmap")
            pass
        
        try:
            user_gdf = pandas.json_normalize(search_latlng)
        except NotImplementedError:
            # st.info("No Place Name or Address provided. Attempting to Map IPs.")
            pass
        try:
            user_gdf = geopandas.GeoDataFrame(user_gdf, geometry=geopandas.points_from_xy(user_gdf.lng, user_gdf.lat))
        except UnboundLocalError:
            pass
        ipmap = leafmap.Map(zoom=2)    
        ipmap.add_basemap(basemap='OpenStreetMap')                       # free default
        ipmap.add_basemap(basemap='ROADMAP', show=False)
        ipmap.add_basemap(basemap='TERRAIN', show=False)
        ipmap.add_basemap(basemap='HYBRID', show=False)
        ipmap.add_basemap(basemap='Esri.WorldImagery', show=False)       # free satellite
        ipmap.add_basemap(basemap='CartoDB.Positron', show=False)        # free light
        ipmap.add_basemap(basemap='CartoDB.DarkMatter', show=False)      # free dark
        # ipmap.zoom_to_gdf(gdf) 
        try:
            user_spot = ipmap.add_circle_markers_from_xy(data=user_gdf, x="lng", y="lat",color='Red',fill_color="White")
        except UnboundLocalError:
            pass
        try:
            circle_Points = ipmap.add_circle_markers_from_xy(data=gdf, x="LONGITUDE", y="LATITUDE",color="Yellow",fill_color="Yellow", radius=5)
            ipmap.to_streamlit()
            # Record the last rendered map type so the unified download button can choose the correct exporter
            try:
                safe_session_set('last_map_type', 'leaflet')
            except Exception:
                pass
            downloadfile = ipmap.to_html()               # for downloads
            download_test = st.download_button(label="Download HTML Map", data=downloadfile,file_name="Fetch_Analysis_Map.html")
        except UnboundLocalError:
            pass
        #     st.error("Input Data is required OR No location data was located from the provided data.")


def make_map(in_df):       #bring in pandas dataframe
    valid_records, skipped_count = filter_valid_coordinates(in_df, 'LATITUDE', 'LONGITUDE')
    valid_count = len(valid_records)

    # Notify user if records were skipped
    if skipped_count > 0:
        st.warning(f"⚠️ Skipped {skipped_count} record(s) missing valid coordinates. Proceeding with {valid_count}.")

    # Check if we have any valid records left
    if valid_count == 0:
        st.error(t("msg_no_valid_records"))
        return

    gdf = geopandas.GeoDataFrame(valid_records, geometry=geopandas.points_from_xy(valid_records.LONGITUDE, valid_records.LATITUDE))
    # Reset index to ensure sequential indexing for iloc operations
    gdf = gdf.reset_index(drop=True)
    _mt_en = ["Clustered Markers", "Points & Trails", "Hotspots", "Heatmap", "Cell Sites"]
    _mt_tr = [t("map_clustered"), t("map_points_trails"), t("map_hotspots"), t("map_heatmap"), t("map_cell_sites")]
    _mt_sel = st.radio(t("lbl_select_map_type"), options=_mt_tr, horizontal=True)
    map_Type = _mt_en[_mt_tr.index(_mt_sel)]
    Map = leafmap.Map()
    # Defer zooming for Hotspots so we can compute a tighter fit later
    if map_Type != "Hotspots":
        Map.zoom_to_gdf(gdf) 
    Map.add_basemap(basemap='OpenStreetMap')                       # free default
    Map.add_basemap(basemap='ROADMAP', show=False)
    Map.add_basemap(basemap='TERRAIN', show=False)
    Map.add_basemap(basemap='HYBRID', show=False)
    Map.add_basemap(basemap='Esri.WorldImagery', show=False)       # free satellite
    Map.add_basemap(basemap='CartoDB.Positron', show=False)        # free light
    Map.add_basemap(basemap='CartoDB.DarkMatter', show=False)      # free dark

    if map_Type == "Clustered Markers":
        grouped_Points = Map.add_points_from_xy(gdf, x="LONGITUDE", y="LATITUDE", min_width=10,max_width=250,layer_name="Clustered Points", add_legend=False)
    
    map_rendered = False  # track if we've already sent map to streamlit

    if map_Type == "Hotspots":
        st.markdown("---")
        clean_coords = valid_records.copy()
        colh1, colh2, colh3, colh4 = st.columns(4)
        with colh1:
            radius_m = st.number_input(t("lbl_radius_m"), min_value=5, max_value=1000, value=30, step=5)
        with colh2:
            max_hotspots = st.number_input(t("lbl_max_hotspots"), min_value=1, max_value=500, value=3, step=1)
        with colh3:
            possible_time_cols = [c for c in clean_coords.columns if 'TIME' in c.upper() or 'DATE' in c.upper()]
            time_col = st.selectbox(t("lbl_time_col_optional"), options=[None]+possible_time_cols, index=0)
        with colh4:
            advanced = st.checkbox(t("chk_advanced"), value=False, help="Show min points parameter")
        if advanced:
            min_samples = st.slider("Min Points (DBSCAN)", min_value=2, max_value=50, value=3, step=1)
        else:
            min_samples = 3
        trim_chaining = st.checkbox(
            t("chk_trim_chaining"), value=True,
            help="If checked, any points farther than the chosen radius from a hotspot's centroid are removed (prevents elongated 'snake' clusters)."
        )
        run_cluster = st.button(t("btn_run_hotspot"))
        if safe_session_get('hotspot_store') is None:
            safe_session_set('hotspot_store', None)
        param_key = f"r{radius_m}_m{min_samples}_t{time_col}_max{max_hotspots}_trim{trim_chaining}"
        clusters_df = pandas.DataFrame(); summary_df = pandas.DataFrame()
        if run_cluster:
            try:
                clusters_df, summary_df = cached_compute_hotspots(clean_coords, radius_m, min_samples, time_col, trim_chaining=trim_chaining)
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Hotspot clustering error: {e}")
            # Persist large DataFrames to disk and store only file paths in session_state
            clusters_path = persist_object_to_tempfile(clusters_df)
            summary_path = persist_object_to_tempfile(summary_df)
            safe_session_set('hotspot_store', {
                'params': param_key,
                'clusters_path': clusters_path,
                'summary_path': summary_path,
                'radius_m': radius_m,
                'min_samples': min_samples,
                'time_col': time_col,
                'max_hotspots': max_hotspots,
                'trim_chaining': trim_chaining
            })
        else:
            store = safe_session_get('hotspot_store')
            if store and store.get('params') == param_key:
                clusters_df = load_persisted_object(store.get('clusters_path')) or pandas.DataFrame()
                summary_df = load_persisted_object(store.get('summary_path')) or pandas.DataFrame()
            elif store and store.get('params') != param_key and store.get('summary') is not None:
                st.info(t("msg_params_changed"))

        if not summary_df.empty:
            st.markdown("### Hotspot Summary")
            # Ensure deterministic ordering (highest visit count first) then create sequential display IDs
            summary_df = summary_df.sort_values('COUNT', ascending=False).reset_index(drop=True)
            summary_df['DISPLAY_ID'] = summary_df.index + 1  # 1-based numbering for user-friendly display
            total_clusters = len(summary_df)
            limited_summary = summary_df.head(max_hotspots)
            id_map = dict(zip(summary_df['HOTSPOT_ID'], summary_df['DISPLAY_ID']))
            if total_clusters > max_hotspots:
                st.caption(f"Showing top {max_hotspots} of {total_clusters} hotspots (by visits).")
            # Prepare a user-facing table with contiguous hotspot numbers
            limited_display = limited_summary.copy()
            # Rename DISPLAY_ID column for clarity and place first
            cols_order = ['DISPLAY_ID'] + [c for c in limited_display.columns if c != 'DISPLAY_ID']
            limited_display = limited_display[cols_order].rename(columns={'DISPLAY_ID': 'HOTSPOT'})
            # Remove internal HOTSPOT_ID from user-facing table
            if 'HOTSPOT_ID' in limited_display.columns:
                limited_display = limited_display.drop(columns=['HOTSPOT_ID'])
            # Hide the implicit 0,1,2... index column from the user-facing table
            try:
                st.dataframe(limited_display.style.hide(axis='index'))
            except Exception:
                # Fallback if Styler.hide not available
                st.dataframe(limited_display.set_index(limited_display.columns[0], drop=True))
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "Download Shown CSV",
                    data=limited_display.to_csv(index=False),
                    file_name="Fetch_Hotspots_Top.csv"
                )
            with col_dl2:
                # Provide full summary with both IDs so user can reconcile if needed
                full_display = summary_df.copy()
                full_display = full_display[['DISPLAY_ID'] + [c for c in full_display.columns if c != 'DISPLAY_ID']]
                full_display = full_display.rename(columns={'DISPLAY_ID': 'HOTSPOT'})
                if 'HOTSPOT_ID' in full_display.columns:
                    full_display = full_display.drop(columns=['HOTSPOT_ID'])
                st.download_button(
                    "Download All CSV",
                    data=full_display.to_csv(index=False),
                    file_name="Fetch_Hotspots_All.csv"
                )
            if st.button(t("btn_clear_hotspots"), type="secondary"):
                # Remove any persisted files
                store = safe_session_get('hotspot_store') or {}
                try:
                    cp = store.get('clusters_path')
                    sp = store.get('summary_path')
                    if cp and os.path.exists(cp):
                        os.unlink(cp)
                    if sp and os.path.exists(sp):
                        os.unlink(sp)
                except Exception:
                    pass
                safe_session_set('hotspot_store', None)
                st.rerun()
            palette = ["red","blue","green","orange","purple","teal","pink","yellow","white","gray","cadetblue","darkred","darkblue","darkgreen"]
            # --- Center & zoom based on hotspot CENTERS (ignoring any outlier member points) ---
            try:
                if not limited_summary.empty:
                    # Compute center-of-centers
                    mean_lat = float(limited_summary['CENTER_LAT'].mean())
                    mean_lon = float(limited_summary['CENTER_LON'].mean())
                    # Compute max pairwise center distance (approx haversine) to scale zoom
                    import math
                    def hav(lat1, lon1, lat2, lon2):
                        R = 6371000.0
                        phi1, phi2 = math.radians(lat1), math.radians(lat2)
                        dphi = math.radians(lat2-lat1)
                        dl = math.radians(lon2-lon1)
                        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
                        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))
                    centers = limited_summary[['CENTER_LAT','CENTER_LON']].to_numpy()
                    max_dist = 0.0
                    for i in range(len(centers)):
                        for j in range(i+1, len(centers)):
                            d = hav(centers[i][0], centers[i][1], centers[j][0], centers[j][1])
                            if d > max_dist:
                                max_dist = d
                    # Map distance span (meters) to an approximate Leaflet zoom level
                    # Values chosen empirically for typical mid-latitude scale
                    if max_dist <= 60: zoom = 18
                    elif max_dist <= 120: zoom = 17
                    elif max_dist <= 300: zoom = 16
                    elif max_dist <= 600: zoom = 15
                    elif max_dist <= 1200: zoom = 14
                    elif max_dist <= 2500: zoom = 13
                    elif max_dist <= 5000: zoom = 12
                    elif max_dist <= 10000: zoom = 11
                    elif max_dist <= 20000: zoom = 10
                    elif max_dist <= 40000: zoom = 9
                    else: zoom = 8
                    # Slightly tighten if only a single hotspot
                    if len(limited_summary) == 1:
                        zoom = max(zoom, 17)
                    Map.set_center(mean_lon, mean_lat, zoom=zoom)
            except Exception:
                pass
            for idx, row in limited_summary.iterrows():
                color = palette[idx % len(palette)]
                display_id = row.DISPLAY_ID
                folium.Circle(
                    location=[row.CENTER_LAT, row.CENTER_LON],
                    radius=radius_m,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.35,
                    popup=f"Hotspot {display_id}<br>Visits: {row.COUNT}<br>Max Dist: {row.MAX_DISTANCE_M} m"
                ).add_to(Map)
                folium.Marker(
                    [row.CENTER_LAT, row.CENTER_LON],
                    tooltip=f"#{display_id} ({row.COUNT})"
                ).add_to(Map)
            show_points = st.checkbox(t("chk_show_points"), value=True, help="Display all member points for the shown hotspots (may slow large datasets)")
            if show_points:
                try:
                    pts = clusters_df[clusters_df['HOTSPOT_ID'].isin(limited_summary['HOTSPOT_ID'])]
                    if len(pts) > 25000:
                        st.warning("Showing individual points for very large hotspot sets may slow the browser.")
                    for cid, grp in pts.groupby('HOTSPOT_ID'):
                        color = palette[int(id_map.get(cid, cid)) % len(palette)]
                        for lat, lon in zip(grp['LATITUDE'], grp['LONGITUDE']):
                            folium.CircleMarker(location=[lat, lon], radius=2, color=color, fill=True, fill_color=color, fill_opacity=0.9).add_to(Map)
                except Exception as e:
                    st.error(f"Failed to render individual points: {e}")
            st.markdown("**Tips:** Increase radius if visits are a few dozen meters apart; decrease radius for tighter grouping.")
            # Render the map here (above clocks) once hotspots & optional points are drawn
            Map.to_streamlit()
            try:
                try:
                    safe_session_set('last_map_type', 'leaflet')
                except Exception:
                    pass
            except Exception:
                pass
            map_rendered = True

            if time_col:
                st.markdown("---")
                t_sub = st.subheader(t("hdr_hotspot_clocks"))
                # Show one clock per hotspot (limited set only)
                for idx, row in limited_summary.iterrows():
                    hid = row.HOTSPOT_ID
                    display_id = row.DISPLAY_ID
                    subset = clusters_df[(clusters_df['HOTSPOT_ID']==hid)]
                    with st.expander(f"Hotspot {display_id} — {row.COUNT} visits", expanded=len(limited_summary)<=3):
                        render_tactical_clock(
                            subset,
                            time_col,
                            title=f"Hotspot {display_id} Activity",
                            height=560,
                            center_lat=row.CENTER_LAT,
                            center_lon=row.CENTER_LON,
                            radius_m=radius_m,
                            visits=int(row.COUNT),
                            max_distance_m=row.MAX_DISTANCE_M,
                            first_obs=row.FIRST_OBS,
                            last_obs=row.LAST_OBS
                        )
                # Overall clock
                with st.expander("All Hotspots Combined", expanded=False):
                    combined = clusters_df[clusters_df['HOTSPOT_ID']!=-1]
                    # Aggregate span and stats
                    agg_visits = int(combined.shape[0]) if not combined.empty else None
                    try:
                        first_obs_all = pandas.to_datetime(combined[time_col], errors='coerce').min()
                        last_obs_all = pandas.to_datetime(combined[time_col], errors='coerce').max()
                    except Exception:
                        first_obs_all = last_obs_all = None
                    render_tactical_clock(
                        combined,
                        time_col,
                        title="All Hotspots Combined",
                        height=560,
                        radius_m=radius_m,
                        visits=agg_visits,
                        first_obs=first_obs_all,
                        last_obs=last_obs_all
                    )
        else:
            if run_cluster:
                st.warning("No hotspots found with current parameters.")

    # (Single final Map.to_streamlit() call occurs later; removed interim render to avoid duplicate maps.)


    if map_Type == "Heatmap":
            st.markdown("---")
            heat_df = gdf[["LATITUDE","LONGITUDE"]].dropna()
            if heat_df.empty:
                st.error("No valid points for heatmap.")
            else:
                col_h1, col_h2, col_h3 = st.columns(3)
                with col_h1:
                    heat_radius = st.slider("Point Radius (px)", 2, 50, 12)
                with col_h2:
                    heat_blur = st.slider("Blur", 2, 40, 18)
                with col_h3:
                    use_weight = st.checkbox(t("chk_use_weight"))
                weights = None
                if use_weight:
                    numeric_cols = [
                        c for c in gdf.columns
                        if c not in ("LATITUDE","LONGITUDE","geometry")
                        and pandas.api.types.is_numeric_dtype(gdf[c])
                    ]
                    if numeric_cols:
                        weight_col = st.selectbox(t("lbl_weight_column"), options=numeric_cols)
                        weights = pandas.to_numeric(gdf[weight_col], errors='coerce').fillna(0).tolist()
                    else:
                        st.info("No numeric columns available for weights.")
                try:
                    heat_data = list(zip(heat_df['LATITUDE'], heat_df['LONGITUDE'], weights if weights else [1]*len(heat_df)))
                    HeatMap(
                        data=[(lat, lon, w) for lat, lon, w in heat_data],
                        name="Heatmap",
                        radius=heat_radius,
                        blur=heat_blur,
                        max_zoom=18
                    ).add_to(Map)
                    folium.LayerControl().add_to(Map)
                    Map.zoom_to_gdf(gdf)
                    map_rendered = True
                    # Immediately render to avoid waiting for final fallback (gives user instant feedback)
                    Map.to_streamlit()
                    try:
                        try:
                            safe_session_set('last_map_type', 'leaflet')
                        except Exception:
                            pass
                    except Exception:
                        pass
                except Exception as e:
                    st.error(f"Heatmap error: {e}")

    if map_Type == "Points & Trails":
            st.markdown("---")
            Map.zoom_to_gdf(gdf) 
            _pp_en = ["Markers", "Show Point Progression", "Vapour Trail"]
            _pp_tr = [t("mode_markers"), t("mode_progression"), t("mode_vapor")]
            _pp_sel = st.radio(label=t("lbl_select_map_activity"), options=_pp_tr, horizontal=True)
            points_or_path = _pp_en[_pp_tr.index(_pp_sel)]
            
            if points_or_path == "Markers":     #Shows markers only
                if "POINT_COLOR" in valid_records.columns:
                    # First add the accuracy circles with lower z-index
                    if st.checkbox(t("chk_accuracy_radius")):
                        # Filter to show numeric columns for radius selection.
                        # Use coercion to detect numeric-like columns (handles object dtypes with numeric strings).
                        numeric_columns = []
                        for col in gdf.columns:
                            if col in ['LATITUDE', 'LONGITUDE']:
                                continue
                            coerced = pandas.to_numeric(gdf[col], errors='coerce')
                            if coerced.notna().any():
                                numeric_columns.append(col)
                        
                        if not numeric_columns:
                            st.error("No numeric columns found for radius/accuracy information. Please ensure your data contains numeric columns for radius values.")
                        else:
                            radius_value = st.selectbox(label=t("lbl_radius_meters"), options=numeric_columns)
                            try:
                                for idx, row in gdf.iterrows():
                                    rad_value = row[radius_value]
                                    # Only create circle if radius value exists and is valid
                                    if pandas.notna(rad_value) and float(rad_value) > 0:                        
                                        circle = folium.Circle(
                                            location=[row['LATITUDE'], row['LONGITUDE']],
                                            radius=rad_value,
                                            color=row["POINT_COLOR"],
                                            fill_color=row["POINT_COLOR"],                                
                                            fill=True,
                                            fill_opacity=0.5,
                                        ).add_to(Map)
                            except (KeyError, ValueError) as e:
                                st.error(f"Error processing radius information: {str(e)}. Please select a column with positive numeric values.")
                    
                    # Then add the markers with higher z-index
                    for idx, row in gdf.iterrows():
                        # Create a single-row dataframe for this point
                        single_point_df = pandas.DataFrame([row]).reset_index(drop=True)
                        circle_Points = Map.add_circle_markers_from_xy(
                            data=single_point_df, 
                            x="LONGITUDE", 
                            y="LATITUDE",
                            color=row["POINT_COLOR"],
                            fill_color=row["POINT_COLOR"],
                            radius=5,
                        )

                else:
                    # Use color from color picker (stored in POINT_COLOR column)
                    color = gdf['POINT_COLOR'].iloc[0] if 'POINT_COLOR' in gdf.columns and len(gdf) > 0 else "#FF0000"
                    
                    if st.checkbox(t("chk_accuracy_radius")):
                        # Filter to show numeric columns for radius selection (coercion-based)
                        numeric_columns = []
                        for col in gdf.columns:
                            if col in ['LATITUDE', 'LONGITUDE']:
                                continue
                            coerced = pandas.to_numeric(gdf[col], errors='coerce')
                            if coerced.notna().any():
                                numeric_columns.append(col)
                        
                        if not numeric_columns:
                            st.error("No numeric columns found for radius/accuracy information. Please ensure your data contains numeric columns for radius values.")
                        else:
                            radius_value = st.selectbox(label=t("lbl_radius_meters"), options=numeric_columns)
                            try:
                                for idx, row in gdf.iterrows():
                                    rad_value = row[radius_value]
                                    if pandas.notna(rad_value) and float(rad_value) > 0:
                                        circle = folium.Circle(
                                            location=[row['LATITUDE'], row['LONGITUDE']],
                                            radius=rad_value,
                                            color=color,
                                            fill_color=color,                                
                                            fill=True,
                                            fill_opacity=0.5,
                                            weight=1,
                                            z_index=1,  # Lower z-index for circles
                                        ).add_to(Map)
                            except (KeyError, ValueError) as e:
                                st.error(f"Error processing radius information: {str(e)}. Please select a column with positive numeric values.")
                    
                    # Add markers with higher z-index
                    circle_Points = Map.add_circle_markers_from_xy(
                        data=gdf, 
                        x="LONGITUDE", 
                        y="LATITUDE",
                        color=color,
                        fill_color=color, 
                        radius=5,
                        z_index_offset=1000  # Higher z-index for markers
                    )
            if points_or_path == "Show Point Progression":      #Shows the moving path between markers
                list_of_path_points = []    #stores coordinates from dataframe, but in long/lat format
                pathpointforreal = []       #stores corrected coordinates in lat/long form to be used by the Antpath tool
                
                if "SOURCE_FILE" in valid_records.columns and "POINT_COLOR" in valid_records.columns:
                    # Group data by source file
                    grouped = valid_records.groupby('SOURCE_FILE')
                    
                    # Create markers and paths for each source file
                    for source_file, group_df in grouped:
                        # Reset index to avoid iloc issues
                        group_df = group_df.reset_index(drop=True)
                        # Convert group DataFrame to GeoDataFrame
                        group_gdf = geopandas.GeoDataFrame(
                            group_df, 
                            geometry=geopandas.points_from_xy(group_df.LONGITUDE, group_df.LATITUDE)
                        )
                        # Reset index for the geodataframe too
                        group_gdf = group_gdf.reset_index(drop=True)
                        
                        # Add markers using the file's selected color
                        color = group_df['POINT_COLOR'].iloc[0]  # Get color for this file
                        circle_Points = Map.add_circle_markers_from_xy(
                            data=group_gdf, 
                            x="LONGITUDE", 
                            y="LATITUDE",
                            color=color,
                            fill_color=color, 
                            radius=5
                        )
                        
                        # Create path points for this group
                        group_path_points = []
                        for index, row in group_gdf.iterrows():
                            for pt in list(row['geometry'].coords):
                                group_path_points.append(pt)
                        
                        # Convert coordinates for this group
                        group_pathpoints = []
                        for ting in group_path_points:
                            [longy, laty] = ting
                            group_pathpoints.append([float(laty), float(longy)])
                        
                        # Add AntPath for this group with its color
                        plugins.AntPath(
                            locations=group_pathpoints,
                            color=color,
                            weight=2,
                            opacity=0.8
                        ).add_to(Map)
                        
                else:
                    # Use color from color picker (stored in POINT_COLOR column)
                    color = gdf['POINT_COLOR'].iloc[0] if 'POINT_COLOR' in gdf.columns and len(gdf) > 0 else "#FF0000"
                        
                    try:
                        circle_Points = Map.add_circle_markers_from_xy(
                            data=gdf, 
                            x="LONGITUDE", 
                            y="LATITUDE",
                            color=color,
                            fill_color=color, 
                            radius=5
                        )
                    except ValueError as e:
                        st.error(f"Error plotting markers: {e}. Please verify the selected data columns contain valid coordinate values.")
                        
                    for index, row in gdf.iterrows():
                        for pt in list(row['geometry'].coords):
                            list_of_path_points.append(pt)
                    
                    for ting in list_of_path_points:
                        [longy, laty] = ting
                        pathpointforreal.append([float(laty), float(longy)])
                    plugins.AntPath(locations=pathpointforreal,color=color).add_to(Map)


            #   GOTTA ORDER THE DATAFRAME BY TIME AND DATE THEN ADD THE POINTS IN ORDER TO A LIST TO BE READ BY THE ANTPATH


            if points_or_path == "Vapour Trail":
                choose_datetime_column = st.selectbox(t("lbl_datetime_column"), options=gdf.columns, key="datetime_vapor")
                _ti_en = ["Daily", "Hourly", "10 Minutes", "1 Minute"]
                _ti_tr = [t("interval_daily"), t("interval_hourly"), t("interval_10min"), t("interval_1min")]
                _ti_sel = st.radio(t("lbl_time_interval"), options=_ti_tr, horizontal=True)
                time_interval = _ti_en[_ti_tr.index(_ti_sel)]
                
                # Only show color selector if there's no SOURCE_FILE column
                if 'SOURCE_FILE' not in gdf.columns:
                    vapor_trail_color = st.selectbox(
                        "Vapour Trail Color",
                        ['DarkRed', 'Yellow', 'Pink', 'Green', 'Teal', 'Blue', 'White'],
                        key="vapor_color"
                    )
                
                # Set time intervals
                if time_interval == 'Daily': chosen_interval = 'PT24H'
                if time_interval == 'Hourly': chosen_interval = 'PT1H'
                if time_interval == '10 Minutes': chosen_interval = 'PT10M'  
                if time_interval == '1 Minute': chosen_interval = 'PT1M'   

                # Create a FeatureGroup for the vapor trail
                vapor_trail = folium.FeatureGroup(name='Vapor Trail')
                vapor_trail.add_to(Map)

                travel_history = []
                skipped_entries = 0

                # If we have multiple source files
                if 'SOURCE_FILE' in gdf.columns:
                    # Group by source file
                    for source_file, group_df in gdf.groupby('SOURCE_FILE'):
                        # Reset index to avoid iloc issues
                        group_df = group_df.reset_index(drop=True)
                        color = group_df['POINT_COLOR'].iloc[0]  # Get color for this file
                        
                        # Process each group separately
                        for i in range(len(group_df) - 1):
                            row1 = group_df.iloc[i]
                            row2 = group_df.iloc[i + 1]
                            
                            # Skip if any coordinate or timestamp is NaN
                            if (pandas.isna(row1['LONGITUDE']) or pandas.isna(row1['LATITUDE']) or 
                                pandas.isna(row2['LONGITUDE']) or pandas.isna(row2['LATITUDE']) or 
                                pandas.isna(row1[choose_datetime_column]) or pandas.isna(row2[choose_datetime_column])):
                                skipped_entries += 1
                                continue

                            try:
                                if 'datetime.datetime' in str(type(row1[choose_datetime_column])):
                                    row1_timestampstr = (row1[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                                    row2_timestampstr = (row2[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                                else:
                                    row1_timestampstr = str(row1[choose_datetime_column])
                                    row2_timestampstr = str(row2[choose_datetime_column])
                                            
                                coord = [[float(row1["LONGITUDE"]), float(row1["LATITUDE"])],
                                        [float(row2["LONGITUDE"]), float(row2["LATITUDE"])]]
                                
                                entry = {
                                    "type": "Feature",
                                    "geometry": {
                                        "type": "LineString",
                                        "coordinates": coord
                                    },
                                    "properties": {
                                        "times": [row1_timestampstr, row2_timestampstr],
                                        "style": {
                                            "color": color,  # Use the color from the source file
                                            "weight": 8
                                        },
                                        "source": source_file  # Add source file info to properties
                                    }
                                }
                                travel_history.append(entry)
                            except (ValueError, TypeError) as e:
                                skipped_entries += 1
                                st.warning(f"Skipping invalid data point: {e}")
                                continue
                else:
                    # Original single-color processing for single files
                    for i in range(len(gdf) - 1):
                        row1 = gdf.iloc[i]
                        row2 = gdf.iloc[i + 1]
                        
                        if (pandas.isna(row1['LONGITUDE']) or pandas.isna(row1['LATITUDE']) or 
                            pandas.isna(row2['LONGITUDE']) or pandas.isna(row2['LATITUDE']) or 
                            pandas.isna(row1[choose_datetime_column]) or pandas.isna(row2[choose_datetime_column])):
                            skipped_entries += 1
                            continue

                        try:
                            if 'datetime.datetime' in str(type(row1[choose_datetime_column])):
                                row1_timestampstr = (row1[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                                row2_timestampstr = (row2[choose_datetime_column]).strftime("%Y-%m-%dT%H:%M:%S")
                            else:
                                row1_timestampstr = str(row1[choose_datetime_column])
                                row2_timestampstr = str(row2[choose_datetime_column])
                                        
                            coord = [[float(row1["LONGITUDE"]), float(row1["LATITUDE"])],
                                    [float(row2["LONGITUDE"]), float(row2["LATITUDE"])]]
                            
                            entry = {
                                "type": "Feature",
                                "geometry": {
                                    "type": "LineString",
                                    "coordinates": coord
                                },
                                "properties": {
                                    "times": [row1_timestampstr, row2_timestampstr],
                                    "style": {
                                        "color": vapor_trail_color,
                                        "weight": 8
                                    }
                                }
                            }
                            travel_history.append(entry)
                        except (ValueError, TypeError) as e:
                            skipped_entries += 1
                            st.warning(f"Skipping invalid data point: {e}")
                            continue

                # Show skipped entries warning
                if skipped_entries > 0:
                    st.warning(f"⚠️ Skipped {skipped_entries} entries due to missing timestamps or invalid data")

                if travel_history:
                    # Create feature collection
                    feature_collection = {
                        "type": "FeatureCollection",
                        "features": travel_history
                    }

                    try:
                        # Create a TimestampedGeoJson layer
                        vapor_trail_layer = TimestampedGeoJson(
                            feature_collection,
                            period=chosen_interval,
                            auto_play=True,
                            loop=True,
                            date_options="YYYY-MM-DD HH:mm:ss",
                            add_last_point=False,
                            transition_time=1000,
                            duration=None
                        )

                        # Add the vapor trail layer to the map
                        vapor_trail_layer.add_to(Map)            

                        # Add LayerControl
                        folium.LayerControl().add_to(Map)
                    except Exception as e:
                        st.error(f"Error creating vapor trail: {e}")
                else:
                    st.warning("No valid data points found for creating vapor trail")

        
    if map_Type == "Cell Sites":
            # Columns are already uppercased earlier in the pipeline — no need to repeat
            Map.zoom_to_gdf(gdf)

            st.markdown("---")

            # --- Sector color controls ---
            sector_palette = ['Red', 'Blue', 'Green', 'Purple', 'Orange', 'DarkRed', 'Beige',
                              'DarkBlue', 'DarkGreen', 'CadetBlue', 'Pink', 'LightBlue',
                              'LightGreen', 'Gray', 'Black', 'LightGray']

            color_mode = "single"  # default
            if 'SOURCE_FILE' not in gdf.columns:
                color_mode = st.radio(
                    "Sector Coloring",
                    options=["Single Color", "Cycle Per Sector"],
                    horizontal=True,
                    help="'Cycle Per Sector' auto-assigns a different color to each row so overlapping sectors are distinguishable."
                )
                color_mode = "cycle" if color_mode == "Cycle Per Sector" else "single"
                if color_mode == "single":
                    wedge_color = st.selectbox(t("lbl_sector_color"), options=sector_palette)

            # Sector transparency slider
            sector_opacity = st.slider("Sector Fill Opacity", min_value=0.0, max_value=1.0, value=0.5, step=0.05,
                                       help="Lower values let you see through overlapping sectors.")

            # --- Column selection helpers ---
            all_columns = [col for col in valid_records.columns
                           if col not in ['LATITUDE', 'LONGITUDE', 'SOURCE_FILE', 'POINT_COLOR', 'geometry']]

            if not all_columns:
                st.error("No columns found for azimuth and beam width values. Please ensure your data contains the necessary columns.")
                st.stop()

            # Auto-detect best-match column index for azimuth
            azimuth_keywords = ['AZIMUTH', 'BEARING', 'DIRECTION', 'ANGLE', 'AZ']
            azimuth_default = 0
            for i, col in enumerate(all_columns):
                if any(kw in col.upper() for kw in azimuth_keywords):
                    azimuth_default = i
                    break

            # Auto-detect best-match column index for beam width
            bw_keywords = ['BEAMWIDTH', 'BEAM_WIDTH', 'BW', 'SECTOR_ANGLE', 'BEAM']
            bw_default = 0
            for i, col in enumerate(all_columns):
                if any(kw in col.upper() for kw in bw_keywords):
                    bw_default = i
                    break

            # --- Sector footprint size: presets + "From Column" ---
            # Detect numeric columns for the "From Column" option
            numeric_radius_cols = []
            for col in all_columns:
                coerced = pandas.to_numeric(valid_records[col], errors='coerce')
                if coerced.notna().any():
                    numeric_radius_cols.append(col)

            radius_options = ["1 KM", "1.5 Mile"]
            if numeric_radius_cols:
                radius_options.append("From Column")
            radii = st.selectbox(t("lbl_sector_footprint"), options=radius_options)

            # Create the radius column based on selection
            if radii == "1.5 Mile":
                valid_records = valid_records.copy()
                valid_records["1.5 Mile"] = 2414
                gdf["1.5 Mile"] = 2414
                radii = "1.5 Mile"
            elif radii == "1 KM":
                valid_records = valid_records.copy()
                valid_records["1 KM"] = 1000
                gdf["1 KM"] = 1000
                radii = "1 KM"
            elif radii == "From Column":
                # Auto-detect radius column
                radius_kw = ['RADIUS', 'RANGE', 'DISTANCE', 'RADII']
                radius_default = 0
                for i, col in enumerate(numeric_radius_cols):
                    if any(kw in col.upper() for kw in radius_kw):
                        radius_default = i
                        break
                radii = st.selectbox(t("lbl_radius_col_meters"), options=numeric_radius_cols, index=radius_default)
                # Ensure numeric values in gdf
                gdf[radii] = pandas.to_numeric(gdf[radii], errors='coerce').fillna(0)

            # Azimuth and Beam Width dropdowns with auto-detected defaults
            Azimuth = st.selectbox(t("lbl_sector_azimuth"), options=all_columns, index=azimuth_default)
            beam_width = st.selectbox(t("lbl_beam_width"), options=all_columns, index=bw_default,
                                      placeholder='None')

            # --- Build tower markers with popups (FeatureGroup for layer control) ---
            tower_fg = folium.FeatureGroup(name="Tower Markers")
            sector_fg = folium.FeatureGroup(name="Sector Wedges")

            total_sectors = len(gdf)
            use_progress = total_sectors > 200
            if use_progress:
                st.info(f"Rendering {total_sectors} sectors — this may take a moment.")
                progress_bar = st.progress(0)

            azimuth_warnings = 0

            try:
                for row_i, (index, row) in enumerate(gdf.iterrows()):
                    if radii in row:
                        radius_m = float(row[radii])
                        if radius_m <= 0:
                            continue
                        length = radius_m / 1000  # Convert to km for get_point_at_distance

                        # Beam width with NaN fallback (120° = standard 3-sector site)
                        raw_bw = row[beam_width]
                        if pandas.notna(raw_bw):
                            try:
                                bw_val = float(raw_bw)
                            except (ValueError, TypeError):
                                bw_val = 120.0
                        else:
                            bw_val = 120.0
                        half_beamwidth = bw_val / 2

                        # Azimuth with validation
                        raw_az = row[Azimuth]
                        try:
                            az_val = float(raw_az) % 360
                        except (ValueError, TypeError):
                            azimuth_warnings += 1
                            continue
                        if float(raw_az) < 0 or float(raw_az) > 360:
                            azimuth_warnings += 1

                        upside = (az_val + half_beamwidth) % 360
                        downside = (az_val - half_beamwidth) % 360

                        # Determine sector color
                        if "POINT_COLOR" in row and pandas.notna(row.get("POINT_COLOR")):
                            current_color = row["POINT_COLOR"]
                        elif color_mode == "cycle":
                            current_color = sector_palette[row_i % len(sector_palette)]
                        else:
                            current_color = wedge_color

                        up_lat, up_lon = get_point_at_distance(row["LATITUDE"], row["LONGITUDE"], d=length, bearing=upside)
                        dwn_lat, dwn_lon = get_point_at_distance(row["LATITUDE"], row["LONGITUDE"], d=length, bearing=downside)

                        leafmap.folium.PolyLine(
                            [[row["LATITUDE"], row["LONGITUDE"]], [up_lat, up_lon]],
                            color=current_color
                        ).add_to(sector_fg)
                        leafmap.folium.PolyLine(
                            [[row["LATITUDE"], row["LONGITUDE"]], [dwn_lat, dwn_lon]],
                            color=current_color
                        ).add_to(sector_fg)

                        # Build popup content (exclude internal/geometry columns)
                        popup_items = [f'{k}: {v}' for k, v in row.items()
                                       if k not in ('geometry', 'POINT_COLOR', 'SOURCE_FILE')]
                        popup_html = '<br>'.join(popup_items)

                        plugins.SemiCircle(
                            (row["LATITUDE"], row["LONGITUDE"]),
                            radius=float(row[radii]) / 2,
                            direction=az_val,
                            arc=bw_val,
                            color=current_color,
                            fill_color=current_color,
                            opacity=1,
                            fill_opacity=sector_opacity,
                            popup=popup_html
                        ).add_to(sector_fg)

                        # Tower marker with popup (icon + larger radius for visibility)
                        folium.CircleMarker(
                            location=[row["LATITUDE"], row["LONGITUDE"]],
                            radius=5,
                            color='black',
                            fill=True,
                            fill_color='white',
                            fill_opacity=1.0,
                            weight=2,
                            popup=folium.Popup(popup_html, max_width=350),
                            tooltip=f"Tower ({row['LATITUDE']:.5f}, {row['LONGITUDE']:.5f})"
                        ).add_to(tower_fg)

                    if use_progress:
                        progress_bar.progress((row_i + 1) / total_sectors)

                if use_progress:
                    progress_bar.empty()

            except (TypeError, ValueError) as e:
                st.info("Assign columns for Sector Footprint Size (Radius from Station in Meters), Tower Direction/Azimuth (Degrees), & Beam Width (Degrees)")
                st.error(f"Error: {str(e)}")

            if azimuth_warnings > 0:
                st.warning(f"⚠️ {azimuth_warnings} sector(s) had azimuth values outside 0–360° (corrected via modulo) or non-numeric values (skipped).")

            # Add feature groups and layer control
            sector_fg.add_to(Map)
            tower_fg.add_to(Map)
            folium.LayerControl(collapsed=False).add_to(Map)

    # Add the legend if we have multiple data sources
    if 'SOURCE_FILE' in valid_records.columns and 'POINT_COLOR' in valid_records.columns:
        add_color_legend(Map, valid_records)

    # Final fallback render if not already rendered earlier
    if not map_rendered:
        Map.to_streamlit()
        # After rendering the final map, provide a single download button beneath it
        try:
            try:
                downloadfile = Map.to_html()
            except Exception:
                # Some Map objects provide get_root().render(); try that
                try:
                    downloadfile = Map.get_root().render()
                except Exception:
                    downloadfile = None

            if downloadfile is not None:
                st.download_button(label="Download Map HTML", data=downloadfile, file_name="Fetch_Analysis_Map.html")
        except Exception:
            pass
        
def get_footprint_color(icon_Color):
    if "Yellow" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(50, simplekml.Color.yellow)
    elif "Red" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.red)
    elif "Blue" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.blue)
    elif "White" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.white)
    elif "Green" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.green)
    elif "Teal" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.lightblue)
    elif "Square" in icon_Color:
        footprint_color = simplekml.Color.changealphaint(200, simplekml.Color.white)
    else:
        footprint_color = simplekml.Color.changealphaint(100, simplekml.Color.white)
    return footprint_color

def HTML_output_file(name_for_file):
    try:
        name_for_file = name_for_file + ".html"
    except Exception:
        st.error(t("msg_map_name_required"))
    out_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'Fetch_Maps')
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    out_file = os.path.join(out_folder, name_for_file)
    return out_file

def KML_output_file(name_for_file):
    name_for_file = name_for_file + ".kml"
    out_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'Fetch_Maps')
    if not os.path.exists(out_folder):
        os.makedirs(out_folder)
    out_file = os.path.join(out_folder, name_for_file)
    return out_file

def get_file_encoding(infile):      #checks file encoding
    return (chardet.detect(infile.read()))
 
# 

def _compute_bearing(lat1, lon1, lat2, lon2):
    """Compute initial bearing (degrees 0-360) from point 1 to point 2."""
    lat1, lon1, lat2, lon2 = radians(lat1), radians(lon1), radians(lat2), radians(lon2)
    dlon = lon2 - lon1
    x = sin(dlon) * cos(lat2)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dlon)
    bearing = atan2(x, y)
    return (degrees(bearing) + 360) % 360


def _haversine_km(lat1, lon1, lat2, lon2):
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(a ** 0.5)


def create_kml_tour(df, output_file, altitude, tilt, linger, time_column, icon, footprint, radii,
                    fly_mode="smooth", kml_obj=None):
    """
    Creates a KML tour (and placemarks + path line) either into a new KML or
    into an existing *kml_obj* so tour + placemarks live in one file.

    Parameters:
        df: DataFrame with LATITUDE / LONGITUDE columns.
        output_file: Path to save the KML file (used only when kml_obj is None).
        altitude: Camera height in meters (int).
        tilt: Camera tilt in degrees (int).
        linger: Seconds to linger at each point (float).
        time_column: Column name for timestamps, or None.
        icon: Icon style key into selected_icon dict.
        footprint: Whether to draw radius polygons.
        radii: Column name for radius data.
        fly_mode: 'smooth' for cinematic flight, 'bounce' for default Google Earth hop.
        kml_obj: Optional existing simplekml.Kml to append tour into.
    """
    try:
        altitude = int(altitude)
        tilt = int(tilt)
        linger = float(linger)

        kml = kml_obj if kml_obj is not None else simplekml.Kml()
        tour = kml.newgxtour(name="Fetch Tour")
        playlist = tour.newgxplaylist()

        if 'LONGITUDE' not in df.columns or 'LATITUDE' not in df.columns:
            raise ValueError("DataFrame must contain 'LONGITUDE' and 'LATITUDE' columns.")

        # Coordinate cleaning
        valid_df, skipped_count = filter_valid_coordinates(df, 'LATITUDE', 'LONGITUDE')
        valid_count = len(valid_df)

        if skipped_count > 0:
            st.warning(f"⚠️ Skipped {skipped_count} record(s) missing coordinates for KML tour.")

        if valid_count == 0:
            st.warning("No valid records found for KML tour generation.")
            return

        # Convert time column
        if time_column is not None:
            try:
                valid_df[time_column] = pandas.to_datetime(valid_df[time_column])
            except ValueError:
                valid_df[time_column] = pandas.to_datetime(valid_df[time_column], utc=True)
                valid_df[time_column] = valid_df[time_column].dt.tz_convert('UTC')

        # Determine fly-to mode
        gx_flyto_mode = simplekml.GxFlyToMode.smooth if fly_mode == "smooth" else simplekml.GxFlyToMode.bounce

        # Collect coords for path LineString
        path_coords = []
        rows_list = list(valid_df.iterrows())

        for i, (idx, row) in enumerate(rows_list):
            try:
                lon, lat = float(row['LONGITUDE']), float(row['LATITUDE'])
                path_coords.append((lon, lat))

                description_lines = [f"{key}: {value}" for key, value in row.items()]
                description = "\n".join(description_lines)

                placemark = kml.newpoint(
                    name=f"{row[time_column]}" if time_column else f"{lat}, {lon}",
                    coords=[(lon, lat)],
                    description=description
                )
                placemark.style.iconstyle.icon.href = selected_icon[icon]

                if footprint and radii:
                    rad = row[radii]
                    polycircle = polycircles.Polycircle(
                        latitude=lat, longitude=lon,
                        radius=float(rad), number_of_vertices=72
                    )
                    pol = kml.newpolygon(
                        name=f"{lat}, {lon}, {rad}",
                        outerboundaryis=polycircle.to_kml()
                    )
                    pol.style.polystyle.color = get_footprint_color(icon_Color=icon)

                # --- Compute smart heading (bearing toward next point) ---
                if i + 1 < len(rows_list):
                    next_row = rows_list[i + 1][1]
                    next_lat, next_lon = float(next_row['LATITUDE']), float(next_row['LONGITUDE'])
                    heading = _compute_bearing(lat, lon, next_lat, next_lon)
                    dist_km = _haversine_km(lat, lon, next_lat, next_lon)
                else:
                    # Last point: keep heading from previous leg (or 0)
                    heading = heading if i > 0 else 0  # noqa: F821 — heading set in prior iteration
                    dist_km = 0

                # --- Scale fly duration by distance (1s min, 8s max) ---
                fly_duration = max(1.0, min(8.0, dist_km * 0.5 + 1.0))

                flyto = playlist.newgxflyto(gxduration=fly_duration)
                flyto.gxflytomode = gx_flyto_mode
                flyto.camera.longitude = lon
                flyto.camera.latitude = lat
                flyto.camera.altitude = altitude
                flyto.camera.altitudemode = simplekml.AltitudeMode.relativetoground
                flyto.camera.heading = heading
                flyto.camera.tilt = tilt
                flyto.camera.roll = 0

                if time_column is not None:
                    flyto.when = row[time_column].isoformat()

                playlist.newgxwait(gxduration=linger)

            except (AttributeError, TypeError) as e:
                st.warning(f"Tour: skipping point {idx}: {e}")

        # Add a LineString showing the full travel path
        if len(path_coords) >= 2:
            line = kml.newlinestring(name="Travel Path")
            line.coords = path_coords
            line.style.linestyle.color = simplekml.Color.changealphaint(180, simplekml.Color.cyan)
            line.style.linestyle.width = 3
            line.altitudemode = simplekml.AltitudeMode.clamptoground

        # Save only if we created the KML ourselves (not injected via kml_obj)
        if kml_obj is None:
            kml.save(output_file)
            st.info(f"KML tour saved as {output_file}")

    except TypeError as e:
        st.error(f"Error creating KML tour. Check for errors in the data set. ({e})")

def create_kml(df_in, outfile):
    try:
        headers = df_in.columns.to_list()

        # Streamlit UI for selecting columns
        st.subheader(t("hdr_design_kml"))

        # Only show color selector if there's no POINT_COLOR column
        if 'POINT_COLOR' not in df_in.columns:
            icon = st.selectbox(t("lbl_icon_style"), options=icon_options)
        else:
            icon = "Yellow Paddle"  # Default icon style
            st.info("Using colors selected during file upload")

        label_for_icons = st.selectbox(t("lbl_icon_labels"), options=headers)

        footprint = st.checkbox(t("chk_footprint"), value=False)
        radii = None
        if footprint:
            radii = st.selectbox(t("lbl_radius_distance"), options=headers)

        # --- Path line option ---
        add_path_line = st.checkbox(t("chk_path_line"), value=False,
                                    help="Draws a LineString connecting all points in order.")

        # --- Output format ---
        output_format = st.radio(t("lbl_output_format"), options=["KML", "KMZ"], horizontal=True,
                                 help="KMZ is a compressed KML — smaller file size.")

        tour = st.checkbox(t("chk_kml_tour"), value=False)
        if tour:
            st.subheader(t("hdr_tour_settings"))
            there_are_dates = st.checkbox(t("chk_has_dates"), value=False)
            if there_are_dates:
                time_column = st.selectbox(t("lbl_date_time_col"), options=headers)
            else:
                time_column = None
            tour_altitude = st.selectbox(t("lbl_tour_altitude"), options=[50, 150, 250, 300, 750, 1500, 10000], index=2)
            tour_linger_time = st.selectbox(t("lbl_linger_time"), options=[1, 2, 3, 4, 5, 10, 15], index=3)
            tour_tilt = st.selectbox(t("lbl_tour_tilt"), options=[0, 5, 10, 20], index=1)
            tour_fly_mode = st.radio(t("lbl_camera_fly"), options=["smooth", "bounce"], index=0, horizontal=True,
                                     help="Smooth = cinematic continuous flight. Bounce = camera zooms out and back in between points.")

    except AttributeError:
        st.error("Check for errors in column selection.")

    if st.button(t("btn_generate_kml")):
        filename = "Fetch_KML_Map_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        if not filename:
            st.error("Map Name Required")
        else:
            try:
                # Coordinate cleaning
                valid_df, skipped_count = filter_valid_coordinates(df_in, 'LATITUDE', 'LONGITUDE')
                valid_count = len(valid_df)

                if skipped_count > 0:
                    st.warning(f"⚠️ Skipped {skipped_count} record(s) missing coordinates. {valid_count} valid records will be processed.")

                if valid_count == 0:
                    st.error("No valid records found for KML generation. All records are missing latitude or longitude values.")
                    return

                kml = simplekml.Kml()
                Label = label_for_icons

                # --- Folder grouping by SOURCE_FILE ---
                has_source = 'SOURCE_FILE' in valid_df.columns
                folders = {}  # source_file -> simplekml.Folder

                path_coords = []  # for optional LineString

                for idx, row in valid_df.iterrows():
                    lon, lat = float(row['LONGITUDE']), float(row['LATITUDE'])
                    path_coords.append((lon, lat))

                    description_lines = [f"{key}: {value}" for key, value in row.items()]
                    descript = "\n".join(description_lines)
                    lab = row[Label]

                    # Pick the target container (folder or root kml)
                    if has_source:
                        src = str(row.get('SOURCE_FILE', 'Unknown'))
                        if src not in folders:
                            folders[src] = kml.newfolder(name=src)
                        container = folders[src]
                    else:
                        container = kml

                    point = container.newpoint(name=lab, coords=[(lon, lat)], description=descript)

                    # Apply icon + color
                    if 'POINT_COLOR' in row and pandas.notna(row.get('POINT_COLOR')):
                        hex_color = str(row['POINT_COLOR']).lstrip('#')
                        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                        kml_color = simplekml.Color.rgb(*rgb)
                        point.style.iconstyle.icon.href = selected_icon[icon]
                        point.style.iconstyle.color = kml_color
                    else:
                        point.style.iconstyle.icon.href = selected_icon[icon]

                    if footprint and radii:
                        rad = row[radii]
                        polycircle = polycircles.Polycircle(
                            latitude=lat, longitude=lon,
                            radius=float(rad), number_of_vertices=72
                        )
                        pol = container.newpolygon(
                            name=f"{lat}, {lon}, {rad}",
                            outerboundaryis=polycircle.to_kml()
                        )
                        if 'POINT_COLOR' in row and pandas.notna(row.get('POINT_COLOR')):
                            pol.style.polystyle.color = kml_color
                        else:
                            pol.style.polystyle.color = get_footprint_color(icon_Color=icon)

                # --- Optional travel path LineString ---
                if add_path_line and len(path_coords) >= 2:
                    line = kml.newlinestring(name="Travel Path")
                    line.coords = path_coords
                    line.style.linestyle.color = simplekml.Color.changealphaint(180, simplekml.Color.cyan)
                    line.style.linestyle.width = 3
                    line.altitudemode = simplekml.AltitudeMode.clamptoground

            except Exception as e:
                st.error(f"Error generating KML: {e}")
                return

            # --- Tour: inject into the same KML object ---
            if tour:
                create_kml_tour(
                    df=valid_df, output_file=outfile,
                    altitude=tour_altitude, tilt=tour_tilt,
                    linger=tour_linger_time, time_column=time_column,
                    icon=icon, footprint=False, radii=None,  # placemarks already added above
                    fly_mode=tour_fly_mode, kml_obj=kml
                )

            # --- Save & download ---
            if output_format == "KMZ":
                kmz_outfile = outfile.replace('.kml', '.kmz')
                kml.savekmz(kmz_outfile)
                with open(kmz_outfile, 'rb') as f:
                    file_data = f.read()
                dl_name = "Fetch_KML_Download.kmz"
                st.download_button("Download KMZ", data=file_data, file_name=dl_name)
                st.success(f"KMZ file generated: {dl_name}")
            else:
                kml.save(outfile)
                with open(outfile, 'rb') as f:
                    file_data = f.read()
                dl_name = "Fetch_KML_Download.kml"
                st.download_button("Download KML", data=file_data, file_name=dl_name)
                st.success(f"KML file generated: {dl_name}")


@st.cache_data
def prepare_datetime_column(df, date_column):
    """Prepare datetime column with proper conversion and caching for performance"""
    df_copy = df.copy()
    try:
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column])
    except ValueError:
        # Handle GPX UTC inputs
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column], utc=True)
        df_copy[date_column] = df_copy[date_column].dt.tz_convert('UTC')
    except Exception:
        # Coerce errors to NaT for invalid dates
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column], errors='coerce')
    
    # Remove rows with invalid dates
    df_copy = df_copy.dropna(subset=[date_column])
    return df_copy

def detect_datetime_columns_by_source(df):
    """Detect potential datetime columns for each source file"""
    datetime_mapping = {}
    
    if 'SOURCE_FILE' in df.columns:
        for source_file in df['SOURCE_FILE'].unique():
            source_data = df[df['SOURCE_FILE'] == source_file]
            
            # Look for datetime-like column names
            datetime_candidates = []
            for col in source_data.columns:
                if col in ['SOURCE_FILE', 'POINT_COLOR', 'LATITUDE', 'LONGITUDE']:
                    continue
                col_upper = col.upper()
                if any(keyword in col_upper for keyword in ['TIME', 'DATE', 'TIMESTAMP', 'DATETIME']):
                    datetime_candidates.append(col)
            
            # Test each candidate for actual datetime data
            valid_datetime_cols = []
            for col in datetime_candidates:
                try:
                    test_data = source_data[col].dropna().head(10)
                    if len(test_data) > 0:
                        pandas.to_datetime(test_data)
                        valid_datetime_cols.append(col)
                except Exception:
                    continue
            
            datetime_mapping[source_file] = {
                'candidates': datetime_candidates,
                'valid': valid_datetime_cols
            }
    
    return datetime_mapping

def create_unified_datetime_column(df, datetime_mapping):
    """Create a unified UNIFIED_DATETIME column from multiple source columns"""
    df_copy = df.copy()
    df_copy['UNIFIED_DATETIME'] = pandas.NaT
    processed_files = []
    
    for source_file, datetime_col in datetime_mapping.items():
        if datetime_col and datetime_col != 'Skip this file':
            source_mask = df_copy['SOURCE_FILE'] == source_file
            source_data = df_copy.loc[source_mask, datetime_col]
            
            # Try multiple parsing strategies
            converted_dates = None
            strategy_used = None
            
            strategies = [
                ('Standard parsing', lambda x: pandas.to_datetime(x)),
                ('UTC parsing', lambda x: pandas.to_datetime(x, utc=True)),
                ('Inferred format', lambda x: pandas.to_datetime(x, format='mixed')),
                ('Standard format', lambda x: pandas.to_datetime(x, format='%Y-%m-%d %H:%M:%S')),
                ('US format', lambda x: pandas.to_datetime(x, format='%m/%d/%Y %H:%M:%S')),
                ('ISO format', lambda x: pandas.to_datetime(x, format='%Y-%m-%dT%H:%M:%S')),
            ]
            
            for strategy_name, strategy_func in strategies:
                try:
                    converted_dates = strategy_func(source_data)
                    strategy_used = strategy_name
                    break
                except Exception:
                    continue
            
            if converted_dates is not None:
                df_copy.loc[source_mask, 'UNIFIED_DATETIME'] = converted_dates
                processed_files.append(f"{source_file} ({strategy_used})")
            else:
                st.error(f"Could not parse datetime data from {source_file} column {datetime_col}")
    
    if processed_files:
        st.success(f"Successfully processed datetime data from: {', '.join(processed_files)}")
    
    return df_copy

def multi_source_time_filter_config(df):
    """Configure datetime columns for multiple source files"""
    if 'SOURCE_FILE' not in df.columns:
        return None
    
    source_files = df['SOURCE_FILE'].unique()
    st.subheader(t("hdr_multisource_time"))
    st.info(f"You have {len(source_files)} source files. Configure datetime columns for each file:")
    
    datetime_mapping_detected = detect_datetime_columns_by_source(df)
    datetime_column_mapping = {}
    
    for i, source_file in enumerate(source_files):
        st.markdown(f"**File: {source_file}**")
        source_data = df[df['SOURCE_FILE'] == source_file]
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Show sample data
            st.write("Sample data:")
            display_cols = [col for col in source_data.columns if col not in ['POINT_COLOR']][:6]
            st.dataframe(source_data[display_cols].head(2), use_container_width=True)
        
        with col2:
            # Show detected datetime candidates
            detected_info = datetime_mapping_detected.get(source_file, {})
            if detected_info.get('valid'):
                st.write("Detected datetime columns:")
                for col in detected_info['valid']:
                    st.write(f"✓ {col}")
            elif detected_info.get('candidates'):
                st.write("Potential datetime columns:")
                for col in detected_info['candidates']:
                    st.write(f"? {col}")
            else:
                st.write("No datetime columns detected")
        
        # Column selection
        all_columns = ['Skip this file'] + [col for col in source_data.columns if col not in ['SOURCE_FILE', 'POINT_COLOR']]
        
        # Pre-select the best candidate if available
        default_index = 0
        if detected_info.get('valid'):
            best_candidate = detected_info['valid'][0]
            if best_candidate in all_columns:
                default_index = all_columns.index(best_candidate)
        
        datetime_col = st.selectbox(
            f"Select datetime column for {source_file}",
            options=all_columns,
            index=default_index,
            key=f"datetime_col_{source_file}_{i}"
        )
        
        if datetime_col != 'Skip this file':
            datetime_column_mapping[source_file] = datetime_col
            
            # Test the column
            try:
                test_data = source_data[datetime_col].dropna().head(5)
                if len(test_data) > 0:
                    test_conversion = pandas.to_datetime(test_data)
                    st.success(f"✓ Valid datetime format detected")
                    st.write(f"Sample: {test_conversion.iloc[0]}")
                else:
                    st.warning("No data found in this column")
            except Exception as e:
                st.warning(f"Potential parsing issue: {str(e)[:100]}")
        else:
            st.info("This file will be skipped during time filtering")
        
        st.markdown("---")
    
    return datetime_column_mapping

def display_filter_results(filtered_df, original_df):
    """Display filter results with metrics and sample data"""
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Records", len(filtered_df))
    with col2:
        st.metric("Original Records", len(original_df))
    with col3:
        if len(original_df) > 0:
            percentage = (len(filtered_df) / len(original_df)) * 100
            st.metric("✅ Retained", f"{percentage:.1f}%")
        else:
            st.metric("✅ Retained", "0%")
    
    # Show sample of results instead of full table
    if len(filtered_df) > 0:
        st.subheader(t("hdr_sample_filtered"))
        # Show first 10 rows with better formatting
        sample_df = filtered_df.head(10)
        st.dataframe(sample_df, use_container_width=True)
        
        if len(filtered_df) > 10:
            st.info(f"ℹShowing first 10 of {len(filtered_df):,} records")
        
        # Add download option for filtered data
        if st.button(t("btn_download_csv")):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"filtered_data_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ No records match the selected time range")

def time_filter(in_df, date_column_or_mapping):
    """Improved time filter with support for single and multi-source data"""
    st.subheader(t("hdr_time_filter"))
    
    try:
        # Handle multi-source vs single-source scenarios
        if isinstance(date_column_or_mapping, dict):
            # Multi-source: create unified datetime column
            st.info("Processing multi-source data with unified datetime column...")
            df_with_datetime = create_unified_datetime_column(in_df, date_column_or_mapping)
            
            # Check if any data was successfully processed
            valid_datetime_count = df_with_datetime['UNIFIED_DATETIME'].notna().sum()
            if valid_datetime_count == 0:
                st.error("No valid datetime records found across all source files")
                return in_df
            
            date_column = 'UNIFIED_DATETIME'
            st.success(f"Created unified datetime column with {valid_datetime_count:,} valid records")
            
        else:
            # Single source: use existing logic
            df_with_datetime = prepare_datetime_column(in_df, date_column_or_mapping)
            date_column = date_column_or_mapping
            
            if len(df_with_datetime) == 0:
                st.error("No valid datetime records found in the selected column")
                return in_df
        
        # Data range info
        min_date = df_with_datetime[date_column].min()
        max_date = df_with_datetime[date_column].max()
        total_span = max_date - min_date
        
        # Info panel
        st.subheader(t("hdr_time_range_info"))
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Earliest Record", min_date.strftime("%Y-%m-%d %H:%M"))
        with col2:
            st.metric("Latest Record", max_date.strftime("%Y-%m-%d %H:%M"))
        with col3:
            st.metric("Total Span", f"{total_span.days} days")
        
        # Quick filters
        st.subheader(t("hdr_quick_filters"))
        st.info(f"Preset ranges are calculated from your data's latest record: {max_date.strftime('%Y-%m-%d %H:%M')}")
        
        _qf_en = ["All Data", "Last 24 Hours", "Last Week", "Last Month", "Custom Range"]
        _qf_tr = [t("qf_all_data"), t("qf_24h"), t("qf_week"), t("qf_month"), t("qf_custom")]
        _qf_sel = st.radio(t("lbl_quick_filter"), _qf_tr, horizontal=True, key="time_filter_quick")
        quick_filter = _qf_en[_qf_tr.index(_qf_sel)]
        
        # Set date range based on selection (relative to dataset's max_date)
        if quick_filter == "All Data":
            start_dt, end_dt = min_date, max_date
        elif quick_filter == "Last 24 Hours":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(days=1)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        elif quick_filter == "Last Week":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(weeks=1)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        elif quick_filter == "Last Month":
            end_dt = max_date
            start_dt = max_date - pandas.Timedelta(days=30)
            start_dt = max(start_dt, min_date)  # Don't go before dataset start
        
        # Show selected date range for preset filters
        if quick_filter != "Custom Range":
            st.success(f"Selected range: {start_dt.strftime('%Y-%m-%d %H:%M')} to {end_dt.strftime('%Y-%m-%d %H:%M')}")
            if start_dt == min_date and quick_filter != "All Data":
                st.info("Note: Range limited to dataset start date")
        
        else:  # Custom Range
            st.subheader("Custom Date Range")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Start Date & Time**")
                start_date = st.date_input(
                    "Start Date", 
                    value=min_date.date(),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key="time_filter_start_date"
                )
                start_time = st.time_input(
                    "Start Time",
                    value=min_date.time(),
                    key="time_filter_start_time"
                )
                start_dt = pandas.Timestamp.combine(start_date, start_time)
            with col2:
                st.write("**End Date & Time**")
                end_date = st.date_input(
                    "End Date", 
                    value=max_date.date(),
                    min_value=min_date.date(),
                    max_value=max_date.date(),
                    key="time_filter_end_date"
                )
                end_time = st.time_input(
                    "End Time",
                    value=max_date.time(),
                    key="time_filter_end_time"
                )
                end_dt = pandas.Timestamp.combine(end_date, end_time)
            
            # Validation for custom range
            if start_dt >= end_dt:
                st.error("❌ Start date must be before end date")
                return in_df
        
        # Apply filter
        filtered_df = df_with_datetime[
            (df_with_datetime[date_column] >= start_dt) & 
            (df_with_datetime[date_column] <= end_dt)
        ].copy()
        
        # Display results
        st.subheader(t("hdr_filter_results"))
        display_filter_results(filtered_df, df_with_datetime)
        
        return filtered_df
        
    except Exception as e:
        st.error(f"❌ Error processing time filter: {str(e)}")
        st.error("Please ensure the selected column contains valid date/time data. Remove any non-date addons such as UTC+3")
        return in_df

def declutterer(in_df, date_column):
    """Improved declutterer with better UI and error handling"""
    st.subheader(t("hdr_declutter"))
    
    try:
        # Convert to datetime
        df_copy = in_df.copy()
        df_copy[date_column] = pandas.to_datetime(df_copy[date_column])
        
        # Show data info
        total_records = len(df_copy)
        st.info(f"Processing {total_records:,} records for decluttering")
        
        # Time interval settings with better layout
        Time_intervals = {
            "🟢 Minute": "T", 
            "🔵 Hour": "H", 
            "🟡 Day": "D", 
            "🟠 Week": "W", 
            "🔴 Month": "M", 
            "🟤 Year": "A"
        }
        
        col1, col2 = st.columns([1, 2])
        with col1:
            count_of_time = st.number_input(
                "Interval Count", 
                min_value=1, 
                max_value=60, 
                value=1,
                help="Number of time units to group together"
            )
        with col2:
            choose_interval = st.selectbox(
                "Time Unit", 
                options=list(Time_intervals.keys()),
                help="Time period for grouping locations"
            )
        
        # Build resample rate
        interval_code = Time_intervals[choose_interval]
        resample_Rate = str(count_of_time) + interval_code
        
        # Show what this means
        interval_name = choose_interval.split(" ", 1)[1]  # Remove emoji
        st.info(f"Grouping locations every **{count_of_time} {interval_name.lower()}{'s' if count_of_time > 1 else ''}**")
        
        # Process the data
        with st.spinner("Processing declutter operation..."):
            declutter_data = df_copy.set_index(date_column)
            
            # Check if we have required columns
            if 'LATITUDE' not in declutter_data.columns or 'LONGITUDE' not in declutter_data.columns:
                st.error("❌ LATITUDE and LONGITUDE columns are required for decluttering")
                return in_df
            
            # Perform resampling
            declutter_data = declutter_data.resample(resample_Rate).agg({
                'LATITUDE': 'mean', 
                'LONGITUDE': 'mean'
            })
            
            # Remove rows with NaN values
            declutter_data = declutter_data[declutter_data['LATITUDE'].notna()]
            
            # Reset index to get datetime back as column
            declutter_data = declutter_data.reset_index()
        
        # Show results
        final_count = len(declutter_data)
        reduction_pct = ((total_records - final_count) / total_records) * 100 if total_records > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Original Records", f"{total_records:,}")
        with col2:
            st.metric("Averaged Locations", f"{final_count:,}")
        with col3:
            st.metric("Reduction", f"{reduction_pct:.1f}%")
        
        if final_count > 0:
            st.success(f"✅ Successfully consolidated {total_records:,} records into {final_count:,} averaged locations")
        else:
            st.warning("⚠️ No data remains after decluttering. Try a larger time interval.")
            return in_df
            
        return declutter_data
        
    except Exception as e:
        st.error(f"❌ Error during decluttering: {str(e)}")
        st.error("Please ensure the selected column contains valid date/time data.Remove any non-date addons such as UTC+3")
        return in_df

def convert_kml_2_DF(kml_file):
    if isinstance(kml_file, str):   # used for parsing kml collected from kmz
        tree = ET.ElementTree(ET.fromstring(kml_file))
    else:                    # used for parsing a direct kml submission
        tree = ET.parse(kml_file)
    root = tree.getroot()

    # Namespace dictionary to handle namespaces in the KML file
    ns = {
        'kml': 'http://www.opengis.net/kml/2.2'
    }

    # Extract placemarks
    placemarks = root.findall('.//kml:Placemark', ns)

    # Initialize a list to hold dictionaries of each placemark's data
    placemark_data = []

    # Iterate through each placemark
    for placemark in placemarks:
        # Initialize a dictionary to hold the current placemark's data
        data = {}
        keys_seen = set()  # To track keys in a case-insensitive manner, also used to avoid duplicate keys (getting dup lat and long columns from kml descriptions)
        
        # Extract standard fields (name and coordinates)
        name = placemark.find('kml:name', ns)
        coordinates = placemark.find('.//kml:coordinates', ns)
        
        if name is not None:
            data['name'] = name.text
            keys_seen.add('name'.lower())
        if coordinates is not None:
            # Split coordinates into individual coordinate sets
            coord_sets = coordinates.text.strip().split()
            if len(coord_sets) == 1:  # Only consider placemarks with a single set of coordinates
                coord_values = re.split(r'[,\s]+', coord_sets[0])
                if len(coord_values) >= 2:
                    data['longitude'] = float(coord_values[0])
                    data['latitude'] = float(coord_values[1])
                    keys_seen.update(['longitude', 'latitude'])
                if len(coord_values) == 3:
                    data['altitude'] = float(coord_values[2])
                    keys_seen.add('altitude')

        # Extract ExtendedData/Data elements
        extended_data = placemark.findall('.//kml:ExtendedData/kml:Data', ns)
        for ed in extended_data:
            key = ed.attrib.get('name')
            if key and key.lower() not in keys_seen:
                value = ed.find('kml:value', ns).text if ed.find('kml:value', ns) is not None else ''
                data[key] = value
                keys_seen.add(key.lower())

        # Handle SchemaData elements
        schema_data = placemark.findall('.//kml:ExtendedData/kml:SchemaData/kml:SimpleData', ns)
        for sd in schema_data:
            key = sd.attrib.get('name')
            value = sd.text if sd is not None else ''
            if key and key.lower() not in keys_seen:
                data[key] = value
                keys_seen.add(key.lower())

        # Add the placemark data to the list
        placemark_data.append(data)

    # Create a DataFrame from the extracted data
    df = pandas.DataFrame(placemark_data)

    # Ensure all coordinates are numeric
    df['latitude'] = pandas.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pandas.to_numeric(df['longitude'], errors='coerce')

    # Drop rows with missing latitude or longitude
    df = df.dropna(subset=['latitude', 'longitude'])
    return df


def ingest_multiple_files():
    uploaded_files = st.file_uploader(t("lbl_choose_files"), 
                                    type=["csv", "txt", "tsv", "xlsx", "xls", "gpx", "kmz", "kml"],
                                    accept_multiple_files=True)

    # --- EXIF Photo Location Import (Feature #13) ---
    with st.expander(t("msg_import_photos"), expanded=False):
        st.caption("Upload JPEG/TIFF photos to extract GPS coordinates from EXIF metadata.")
        uploaded_photos = st.file_uploader(
            "Choose photos",
            type=["jpg", "jpeg", "tiff", "tif"],
            accept_multiple_files=True,
            key="photo_uploader"
        )
        if uploaded_photos:
            try:
                photo_df = ingest_photos(uploaded_photos)
                if photo_df is not None and not photo_df.empty:
                    st.success(f"Extracted GPS data from {len(photo_df)} photo(s)")
                    st.dataframe(photo_df.head(10), use_container_width=True)
                    photo_color = st.color_picker("Photo point color", value="#00FF00", key="photo_color_picker")
                    photo_df['SOURCE_FILE'] = 'EXIF_Photos'
                    photo_df['POINT_COLOR'] = photo_color
                    photo_df.columns = photo_df.columns.str.upper()
                    safe_session_set('exif_photo_df', photo_df)
                else:
                    st.warning("No GPS data could be extracted from the uploaded photos.")
                    safe_session_set('exif_photo_df', None)
            except Exception as e:
                st.error(f"Error processing photos: {str(e)}")
                safe_session_set('exif_photo_df', None)

    if not uploaded_files:
        # Still return photo data if available
        exif_df = safe_session_get('exif_photo_df')
        if exif_df is not None and not exif_df.empty:
            return exif_df.copy()
        return None

    # Set how many columns per row
    num_cols = 3  
    color_selections = {}
    
    # Create color selector grid
    for i in range(0, len(uploaded_files), num_cols):
        cols = st.columns(num_cols)
        for j, file in enumerate(uploaded_files[i:i+num_cols]):
            with cols[j]:
                st.markdown(f"**{file.name}**")
                # Use a deterministic, compact key derived from the filename to avoid Streamlit duplicate-key errors
                _digest = hashlib.md5(file.name.encode()).hexdigest()
                _cp_key = f"color_picker_{_digest}"
                color_selections[file.name] = st.color_picker(
                    f"Select color for points in {file.name}", 
                    value="#FF0000", 
                    key=_cp_key
                )    
    
    df_list = []
    for file in uploaded_files:
        try:
            # Reset file pointer
            file.seek(0)
            filename_lower = file.name.lower()
            # Excel files: read without inferring header so we can detect custom header rows
            if any(ext in file.name.lower() for ext in [".xls", ".xlsx"]):
                try:
                    df = pandas.read_excel(file, header=None)
                    df = detect_and_set_header_from_rows(df, max_search_rows=15)
                except Exception:
                    # fallback to default read
                    df = pandas.read_excel(file)
            
            # CSV/TXT files  
            elif any(ext in file.name.lower() for ext in [".csv", ".txt"]):
                enc = selected_encoding if selected_encoding else "utf-8"
                # read without header so we can detect header row within first rows
                try:
                    df = pandas.read_csv(file, encoding=enc, header=None)
                    df = detect_and_set_header_from_rows(df, max_search_rows=15)
                except Exception:
                    # fallback to standard read
                    df = pandas.read_csv(file, encoding=enc)
            
            # TSV files
            elif ".tsv" in file.name.lower():
                enc = selected_encoding if selected_encoding else "utf-8"
                try:
                    df = pandas.read_csv(file, encoding=enc, sep="\t", header=None)
                    df = detect_and_set_header_from_rows(df, max_search_rows=15)
                except Exception:
                    df = pandas.read_csv(file, encoding=enc, sep="\t")
            
            # GPX files
            elif ".gpx" in file.name.lower():
                gpx = gpxpy.parse(file)
                points_data = []
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            points_data.append({
                                'LATITUDE': point.latitude,
                                'LONGITUDE': point.longitude,
                                'ELEVATION': point.elevation,
                                'DATETIME': point.time
                            })
                df = pandas.DataFrame.from_records(points_data)
            
            # KML files
            elif ".kml" in file.name.lower():
                df = convert_kml_2_DF(file)
                # Ensure column names are standardized
                df.columns = df.columns.str.upper()
                # Rename lat/long columns if needed
                if 'LAT' in df.columns and 'LATITUDE' not in df.columns:
                    df = df.rename(columns={'LAT': 'LATITUDE'})
                if 'LON' in df.columns and 'LONGITUDE' not in df.columns:
                    df = df.rename(columns={'LON': 'LONGITUDE'})
            
            # KMZ files  
            elif ".kmz" in file.name.lower():
                with zipfile.ZipFile(file, 'r') as kmz:
                    kml_file_name = next(
                        (name for name in kmz.namelist() if name.endswith('.kml')), 
                        None
                    )
                    if kml_file_name:
                        kml_content = kmz.read(kml_file_name).decode('utf-8')
                        df = convert_kml_2_DF(kml_content)
                    else:
                        st.error(f"No KML file found in {file.name}")
                        continue

            # Clean up DataFrame
            # Create a copy to avoid SettingWithCopyWarning
            # Reset index and drop old index
            if not df.empty:
                df = df.copy().reset_index(drop=True)
            else:
                st.warning(f"File {file.name} contains no data")
                continue
            
            # Standardize column names and remove duplicates
            df.columns = df.columns.str.upper()
            
            # Check if dataframe is empty after processing
            if df.empty:
                st.warning(f"File {file.name} resulted in empty dataframe after processing")
                continue
                
            # Remove duplicate columns safely
            if len(df.columns) > 0:
                df = df.loc[:, ~df.columns.duplicated()]
            else:
                st.error(f"File {file.name} has no valid columns")
                continue
            
            # Add source tracking
            try:
                df["SOURCE_FILE"] = file.name
                df["POINT_COLOR"] = color_selections.get(file.name, "#FF0000")
            except Exception as assign_error:
                st.error(f"Error adding tracking columns to {file.name}: {str(assign_error)}")
                continue
            
            # Validate required columns
            if "LATITUDE" not in df.columns or "LONGITUDE" not in df.columns:
                st.error(f"File {file.name} - first 15 rows were searched for latitude/longitude columns. None found. Data must include 'latitude' and 'longitude' columns.")
                continue

            # --- Coordinate Format Conversion (Feature #6) ---
            # Detect and convert non-decimal coordinate formats (DMS, DDM, UTM)
            for coord_col in ['LATITUDE', 'LONGITUDE']:
                if coord_col in df.columns:
                    fmt = detect_coordinate_format(df[coord_col])
                    if fmt in ('dms', 'ddm', 'mixed'):
                        st.info(f"📐 {file.name}: Detected **{fmt.upper()}** format in {coord_col} — converting to decimal degrees.")
                        df[coord_col] = convert_coordinate_column(df[coord_col])
                    elif fmt == 'decimal':
                        df[coord_col] = pandas.to_numeric(df[coord_col], errors='coerce')
                    else:
                        # Try converting anyway in case of mixed numeric/text
                        df[coord_col] = convert_coordinate_column(df[coord_col])

            df_list.append(df)

        except Exception as e:
            st.error(f"Error processing {file.name}: {str(e)}")
            continue

    if df_list:
        try:
            # Combine all dataframes with clean indexes
            combined_df = pandas.concat(df_list, ignore_index=True, sort=False)
            
            # Ensure unique columns and reset index one final time
            combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
            combined_df = combined_df.reset_index(drop=True)

            # Merge EXIF photo data if available
            exif_df = safe_session_get('exif_photo_df')
            if exif_df is not None and not exif_df.empty:
                exif_copy = exif_df.copy()
                exif_copy.columns = exif_copy.columns.str.upper()
                combined_df = pandas.concat([combined_df, exif_copy], ignore_index=True, sort=False)
                combined_df = combined_df.loc[:, ~combined_df.columns.duplicated()]
                combined_df = combined_df.reset_index(drop=True)
                st.info(f"📷 Merged {len(exif_df)} photo location(s) into dataset.")

            return combined_df
        except Exception as e:
            st.error(f"Error combining data: {str(e)}")
            return None
    else:
        st.error("No valid dataframes were ingested.") 
        return None


########################################
#### In Progress ####


########################################

####    Main Page   ####

uploaded_file = None
preview_data = None
notices = st.empty()            #   Places notifications at the top of the screen


# else:
combined_df = ingest_multiple_files()
if combined_df is not None:
    # Warn users about large datasets that may cause slow rendering
    _row_count = len(combined_df)
    if _row_count > 100_000:
        st.warning(f"⚠️ Large dataset detected ({_row_count:,} rows). Map rendering and analysis may be slow. Consider filtering or sampling your data.")
    combined_df.rename(columns=lambda x: x.lower(), inplace=True)
    combined_df.columns = combined_df.columns.str.upper()  # standardize columns to uppercase
    
    # Update point colors if color pickers have changed
    if 'SOURCE_FILE' in combined_df.columns and 'POINT_COLOR' in combined_df.columns:
        # Get current color picker values for each file
        unique_files = combined_df['SOURCE_FILE'].unique()
        
        for file_name in unique_files:
            # Derive the same deterministic key used when the uploader created the picker
            _digest = hashlib.md5(file_name.encode()).hexdigest()
            color_picker_key = f"color_picker_{_digest}"
            if safe_session_get(color_picker_key) is not None:
                current_color = safe_session_get(color_picker_key)
                # Update the color for this file in the dataframe
                file_mask = combined_df['SOURCE_FILE'] == file_name
                combined_df.loc[file_mask, 'POINT_COLOR'] = current_color
    
    preview_data = combined_df
        

if preview_data is not None:
    with st.expander("Manage Ingested Data"):
        tabi, tabii, tabiii, tabiv = st.tabs([t("tab_review_ingest"), t("tab_time_filter"), t("tab_declutter"), t("tab_timezone")])
        with tabi:
            st.subheader(t("hdr_review_data"))
            
            # Show data overview
            if preview_data is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", f"{len(preview_data):,}")
                with col2:
                    st.metric("Columns", len(preview_data.columns))
                with col3:
                    if 'SOURCE_FILE' in preview_data.columns:
                        unique_files = preview_data['SOURCE_FILE'].nunique()
                        st.metric("Source Files", unique_files)
                    else:
                        st.metric("Source Files", 1)
            
            # Row removal option
            st.subheader(t("hdr_header_cleaning"))
            lines_t0_remove = st.slider(
                label="Number of Rows to Remove from Start",
                min_value=0, 
                max_value=10,
                value=0,
                help="Remove header rows or unwanted data from the beginning of your dataset. First remaining row should contain 'Latitude' and 'Longitude' data."
            )
            
            if lines_t0_remove > 0:
                st.info(f"ℹRemoving the first {lines_t0_remove} row{'s' if lines_t0_remove > 1 else ''} from the dataset")
                
            # Show sample of current data
            st.subheader(t("hdr_data_preview"))
            if preview_data is not None and len(preview_data) > 0:
                # Apply row removal if specified
                display_data = preview_data.iloc[lines_t0_remove:] if lines_t0_remove > 0 else preview_data
                
                # Show first few rows
                st.dataframe(display_data.head(10), use_container_width=True)
                
                if len(display_data) > 10:
                    st.info(f"ℹShowing first 10 rows of {len(display_data):,} total records")
                    
                # Column information
                show_column_info = st.checkbox(t("chk_show_col_info"), value=False)
                if show_column_info:
                    col_info = []
                    for col in display_data.columns:
                        col_type = str(display_data[col].dtype)
                        non_null = display_data[col].count()
                        null_count = len(display_data) - non_null
                        col_info.append({
                            "Column": col,
                            "Data Type": col_type,
                            "Non-Null Values": f"{non_null:,}",
                            "Null Values": f"{null_count:,}"
                        })
                    
                    col_df = pandas.DataFrame(col_info)
                    st.dataframe(col_df, use_container_width=True)
            else:
                st.warning("⚠️ No data available to preview")
                
            # Apply row removal to actual data if specified
            if lines_t0_remove > 0 and preview_data is not None:
                preview_data = preview_data.iloc[lines_t0_remove:].copy()
                st.success(f"✅ Applied row removal: {lines_t0_remove} rows removed from dataset")            

           
        with tabii:
            st.subheader(t("hdr_datetime_filter"))
            filterbytime = st.checkbox(t("chk_enable_time_filter"), help="Filter data to a specific date/time range")
            if filterbytime:
                # Check if we have multiple source files
                if 'SOURCE_FILE' in preview_data.columns and preview_data['SOURCE_FILE'].nunique() > 1:
                    st.info("Multiple source files detected. Configure datetime columns for each file:")
                    
                    # Multi-source configuration
                    datetime_mapping = multi_source_time_filter_config(preview_data)
                    
                    if datetime_mapping:
                        st.subheader(t("hdr_apply_time_filter"))
                        if st.button(t("btn_apply_time_filter")):
                            preview_data = time_filter(preview_data, datetime_mapping)
                    else:
                        st.warning("No files configured for time filtering")
                        
                else:
                    # Single source configuration
                    st.info("Select the column containing your date/time data, then choose your filtering options below.")
                    datetime_Column = st.selectbox(
                        "Select Date/Time Column", 
                        options=preview_data.columns,
                        help="Choose the column that contains date/time information"
                    )
                    preview_data = time_filter(preview_data, datetime_Column)
                
        with tabiii:
            st.subheader(t("hdr_data_declutter"))
            declutter_dis = st.checkbox(
                "Consolidate Location Points", 
                help="Average multiple location points over specified time intervals to reduce data density"
            )
            if declutter_dis:
                st.info("💡 This feature combines nearby points taken within the same time interval into a single averaged location.")
                try:
                    datetim_Column = st.selectbox(
                        "Choose Date/Time Column", 
                        options=preview_data.columns,
                        help="Select the column containing date/time data for grouping"
                    )
                except AttributeError:
                    st.error("❌ No date/time columns available. Please ensure your data contains date/time information.")
                try:
                    preview_data = declutterer(preview_data, date_column=datetim_Column)
                except Exception as e:
                    st.error(f"❌ Error processing declutter: {str(e)}")
                    st.error("Please select a valid date/time column")

        with tabiv:
            st.subheader(t("hdr_timezone"))
            
            # Detect datetime columns
            datetime_columns = []
            if preview_data is not None:
                for col in preview_data.columns:
                    # Check if column contains datetime-like data
                    if preview_data[col].dtype == 'object':
                        # Try to convert a sample to see if it's datetime-like
                        try:
                            sample_values = preview_data[col].dropna().head(5)
                            if len(sample_values) > 0:
                                pandas.to_datetime(sample_values.iloc[0])
                                datetime_columns.append(col)
                        except Exception:
                            pass
                    elif 'datetime' in str(preview_data[col].dtype).lower():
                        datetime_columns.append(col)
            
            if datetime_columns:
                st.info("Convert datetime columns using timezone names (with daylight savings) or simple hourly offsets.")
                
                # Column selection
                tz_column = st.selectbox(
                    "Select DateTime Column to Convert",
                    options=datetime_columns,
                    help="Choose the datetime column you want to convert to a different timezone"
                )
                
                # Conversion method selection
                _cm_en = ["Timezone Conversion", "Hourly Offset"]
                _cm_tr = [t("conv_timezone"), t("conv_offset")]
                _cm_sel = st.radio(
                    t("lbl_conversion_method"),
                    options=_cm_tr,
                    help="Choose between timezone-aware conversion (handles DST) or simple hourly offset"
                )
                conversion_method = _cm_en[_cm_tr.index(_cm_sel)]
                
                if conversion_method == "Timezone Conversion":
                    # Timezone selection with common timezones
                    common_timezones = [
                        'UTC',
                        'US/Eastern',
                        'US/Central', 
                        'US/Mountain',
                        'US/Pacific',
                        'US/Alaska',
                        'US/Hawaii',
                        'Europe/London',
                        'Europe/Paris',
                        'Europe/Berlin',
                        'Asia/Tokyo',
                        'Asia/Shanghai',
                        'Australia/Sydney',
                        'Australia/Melbourne'
                    ]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        source_tz = st.selectbox(
                            "Source Timezone",
                            options=['Auto-detect'] + common_timezones,
                            help="Current timezone of the data. Auto-detect will try to determine automatically."
                        )
                    
                    with col2:
                        target_tz = st.selectbox(
                            "Convert to Timezone",
                            options=common_timezones,
                            index=1,  # Default to US/Eastern
                            help="Target timezone for conversion"
                        )
                
                else:  # Hourly Offset
                    st.info("💡 Positive values add hours (e.g., +3 for 3 hours ahead), negative values subtract hours (e.g., -5 for 5 hours behind)")
                    
                    hour_offset = st.number_input(
                        "Hour Offset",
                        min_value=-12.0,
                        max_value=14.0,
                        value=0.0,
                        step=0.5,
                        help="Number of hours to add (+) or subtract (-) from the datetime. Supports half-hour increments."
                    )
                
                # Show sample conversion
                if st.button(t("btn_preview_conversion")):
                    try:
                        # Get sample data
                        sample_data = preview_data[tz_column].dropna().head(3)
                        
                        if len(sample_data) > 0:
                            st.write("**Sample Conversion Preview:**")
                            
                            preview_results = []
                            for idx, original_value in sample_data.items():
                                try:
                                    # Convert to datetime if not already
                                    if not pandas.api.types.is_datetime64_any_dtype(type(original_value)):
                                        dt_value = pandas.to_datetime(original_value)
                                    else:
                                        dt_value = original_value
                                    
                                    if conversion_method == "Timezone Conversion":
                                        # Timezone conversion logic
                                        if pytz is None:
                                            raise ImportError("pytz library required for timezone conversion")
                                        
                                        # Handle source timezone
                                        if source_tz == 'Auto-detect':
                                            # Try to detect if already timezone-aware
                                            if dt_value.tz is None:
                                                # Assume UTC if no timezone info
                                                dt_value = dt_value.tz_localize('UTC')
                                        else:
                                            # Localize or convert based on current timezone info
                                            if dt_value.tz is None:
                                                dt_value = dt_value.tz_localize(source_tz)
                                            else:
                                                dt_value = dt_value.tz_convert('UTC').tz_convert(source_tz)
                                        
                                        # Convert to target timezone
                                        converted_value = dt_value.tz_convert(target_tz)
                                        
                                        preview_results.append({
                                            'Original': str(original_value),
                                            'Source TZ': str(dt_value),
                                            'Converted': str(converted_value)
                                        })
                                    
                                    else:  # Hourly Offset
                                        # Simple hour offset logic
                                        from datetime import timedelta
                                        
                                        # Remove timezone info for offset calculation
                                        if hasattr(dt_value, 'tz') and dt_value.tz is not None:
                                            dt_naive = dt_value.tz_localize(None)
                                        else:
                                            dt_naive = dt_value
                                        
                                        # Apply hour offset
                                        converted_value = dt_naive + timedelta(hours=hour_offset)
                                        
                                        preview_results.append({
                                            'Original': str(original_value),
                                            'Hour Offset': f"{hour_offset:+.1f} hours",
                                            'Converted': str(converted_value)
                                        })
                                    
                                except Exception as e:
                                    preview_results.append({
                                        'Original': str(original_value),
                                        'Error': str(e),
                                        'Converted': 'Error'
                                    })
                            
                            preview_df = pandas.DataFrame(preview_results)
                            st.dataframe(preview_df, use_container_width=True)
                        else:
                            st.warning("No valid datetime values found in selected column")
                            
                    except Exception as e:
                        st.error(f"Error during conversion preview: {str(e)}")
                
                # Apply conversion
                if st.button(t("btn_apply_conversion"), type="primary"):
                    try:
                        with st.spinner("Converting datetime..."):
                            # Create a copy of the data
                            converted_data = preview_data.copy()
                            
                            # Convert the datetime column
                            dt_series = pandas.to_datetime(converted_data[tz_column])
                            
                            if conversion_method == "Timezone Conversion":
                                if pytz is None:
                                    st.error("pytz library required for timezone conversion. Please install with: pip install pytz")
                                    st.stop()
                                
                                # Handle source timezone
                                if source_tz == 'Auto-detect':
                                    # If no timezone info, assume UTC
                                    if dt_series.dt.tz is None:
                                        dt_series = dt_series.dt.tz_localize('UTC')
                                else:
                                    if dt_series.dt.tz is None:
                                        dt_series = dt_series.dt.tz_localize(source_tz)
                                    else:
                                        dt_series = dt_series.dt.tz_convert(source_tz)
                                
                                # Convert to target timezone
                                converted_series = dt_series.dt.tz_convert(target_tz)
                                
                                success_message = f"✅ Successfully converted {tz_column} from {source_tz} to {target_tz}"
                            
                            else:  # Hourly Offset
                                from datetime import timedelta
                                
                                # Remove timezone info for offset calculation
                                if dt_series.dt.tz is not None:
                                    dt_series = dt_series.dt.tz_localize(None)
                                
                                # Apply hour offset
                                converted_series = dt_series + pandas.Timedelta(hours=hour_offset)
                                
                                success_message = f"✅ Successfully applied {hour_offset:+.1f} hour offset to {tz_column}"
                            
                            # Update the dataframe
                            converted_data[tz_column] = converted_series
                            preview_data = converted_data
                            
                            st.success(success_message)
                            # Prevent an infinite rerun loop by only rerunning once per conversion action
                            if not safe_session_get('_tz_conversion_rerun_done'):
                                try:
                                    safe_session_set('_tz_conversion_rerun_done', True)
                                except Exception:
                                    pass
                                st.rerun()
                            
                    except Exception as e:
                        st.error(f"Error during conversion: {str(e)}")
            else:
                st.info("No datetime columns detected in the data. Upload data with datetime information to use timezone conversion.")

if preview_data is None:
    tabA, tabB = st.tabs([t("tab_geofence"), t("tab_ip_mapping")])
    with tabA:
        make_geofence_map()
    with tabB:
        make_IPaddress_Map()
        

if preview_data is not None:
    # Simple filter status display
    declutter_active = 'declutter_dis' in locals() and declutter_dis
    timefilter_active = 'filterbytime' in locals() and filterbytime
    
    if declutter_active or timefilter_active:
        st.markdown(":orange[Filters are active]")
        
    tab1, tab2, tab3, tab4 = st.tabs([t("tab_preview_kml"), t("tab_analysis_maps"), t("tab_create_geofence"), t("tab_advanced_analysis")])
    with tab1:
        try:
            # Clean preview_data before passing to st.map to avoid null value errors
            if 'LATITUDE' in preview_data.columns and 'LONGITUDE' in preview_data.columns:
                # Count original records
                original_count = len(preview_data)
                
                # Clean the data for st.map
                clean_preview = preview_data.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
                
                # Additional validation to ensure numeric values
                clean_preview = clean_preview[
                    pandas.to_numeric(clean_preview['LATITUDE'], errors='coerce').notna() &
                    pandas.to_numeric(clean_preview['LONGITUDE'], errors='coerce').notna()
                ].copy()
                
                # Convert to numeric and remove infinite values
                clean_preview['LATITUDE'] = pandas.to_numeric(clean_preview['LATITUDE'], errors='coerce')
                clean_preview['LONGITUDE'] = pandas.to_numeric(clean_preview['LONGITUDE'], errors='coerce')
                
                clean_preview = clean_preview[
                    pandas.notna(clean_preview['LATITUDE']) & 
                    pandas.notna(clean_preview['LONGITUDE']) &
                    np.isfinite(clean_preview['LATITUDE']) &
                    np.isfinite(clean_preview['LONGITUDE'])
                ]
                
                # Final cleanup
                clean_preview = clean_preview.dropna(subset=['LATITUDE', 'LONGITUDE'])
                
                # Check if we have valid data for mapping
                valid_count = len(clean_preview)
                skipped_count = original_count - valid_count
                
                if skipped_count > 0:
                    st.info(f"ℹ️ Preview map: Showing {valid_count} valid records. {skipped_count} records with missing coordinates were excluded from the map display.")
                
                if valid_count > 0:
                    map_kwargs = dict(
                        data=clean_preview,
                        latitude='LATITUDE',
                        longitude='LONGITUDE',
                    )
                    if 'POINT_COLOR' in clean_preview.columns:
                        map_kwargs['color'] = 'POINT_COLOR'
                    st.map(**map_kwargs)
                else:
                    st.error("No valid coordinate data available for preview map.")
            else:
                st.warning("No LATITUDE / LONGITUDE columns found — cannot render preview map.")
                
            st.download_button("Download as CSV", data=preview_data.to_csv(), file_name="Fetch_CSV_Export.csv")
        except TypeError:
            st.error("Ensure you have correct settings in Manage Ingested Data and Date/Time Filtering. Remove any non-numeric characters from your Lat/Long columns.")          
        except NameError:
            st.error("preview data not defined")
        # KML = st.button("GENERATE KML")
        st.markdown("---")
        try:
            outFile = KML_output_file("Fetch_KML_Map"+str(now))
            create_kml(df_in=preview_data,outfile=outFile)
        except Exception as e:
            st.error(f"Error generating KML: {e}")
        
    with tab2:
        try:
            make_map(preview_data)
        except AttributeError:
            st.error(t("msg_check_lat_lon"))
    with tab3:
        make_geofence_map()
    with tab4:
        st.header(t("hdr_advanced_analysis"))
        adv_tab1, adv_tab2, adv_tab3 = st.tabs([t("tab_stop_dwell"), t("tab_colocation"), t("tab_coord_tools")])

        with adv_tab1:
            # --- Stop / Dwell Detection (Feature #7) ---
            st.subheader(t("hdr_stop_dwell"))
            st.caption("Detect locations where a subject remained stationary for a configurable duration.")

            # Time column detection
            stop_time_cols = [c for c in preview_data.columns if 'TIME' in c.upper() or 'DATE' in c.upper()]
            if not stop_time_cols:
                st.warning(t("msg_stops_no_time"))
            else:
                stop_col1, stop_col2, stop_col3 = st.columns(3)
                with stop_col1:
                    stop_time_col = st.selectbox(t("lbl_time_column"), options=stop_time_cols, key="stop_time_col")
                with stop_col2:
                    stop_radius = st.number_input(t("lbl_radius_m"), min_value=5, max_value=2000, value=50, step=5, key="stop_radius",
                                                  help="Maximum distance from centroid to be considered the same stop")
                with stop_col3:
                    stop_min_duration = st.number_input(t("lbl_min_duration"), min_value=1, max_value=1440, value=5, step=1, key="stop_min_dur",
                                                        help="Minimum time at a location to qualify as a stop")

                # Per-source or combined
                run_stops_per_source = False
                if 'SOURCE_FILE' in preview_data.columns and preview_data['SOURCE_FILE'].nunique() > 1:
                    run_stops_per_source = st.checkbox(t("chk_per_source"), value=True, key="stop_per_src")

                if st.button(t("btn_detect_stops"), key="run_stops"):
                    with st.spinner("Analyzing stops..."):
                        all_stops = []
                        if run_stops_per_source:
                            for src in preview_data['SOURCE_FILE'].unique():
                                src_df = preview_data[preview_data['SOURCE_FILE'] == src]
                                stops_df = cached_compute_stops(src_df, stop_time_col, stop_radius, stop_min_duration, src)
                                if not stops_df.empty:
                                    all_stops.append(stops_df)
                            if all_stops:
                                stops_result = pandas.concat(all_stops, ignore_index=True)
                            else:
                                stops_result = pandas.DataFrame()
                        else:
                            stops_result = cached_compute_stops(preview_data, stop_time_col, stop_radius, stop_min_duration)

                        if stops_result.empty:
                            st.warning("No stops detected with current parameters. Try increasing the radius or decreasing the minimum duration.")
                        else:
                            safe_session_set('stop_results', stops_result)

                # Display results
                stops_result = safe_session_get('stop_results')
                if stops_result is not None and isinstance(stops_result, pandas.DataFrame) and not stops_result.empty:
                    st.markdown(f"### Found {len(stops_result)} Stop(s)")

                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Total Stops", len(stops_result))
                    with col_m2:
                        avg_dur = stops_result['DURATION_MIN'].mean()
                        st.metric("Avg Duration", f"{avg_dur:.1f} min")
                    with col_m3:
                        total_dwell = stops_result['DURATION_MIN'].sum()
                        if total_dwell > 60:
                            st.metric("Total Dwell Time", f"{total_dwell/60:.1f} hrs")
                        else:
                            st.metric("Total Dwell Time", f"{total_dwell:.1f} min")

                    st.dataframe(stops_result, use_container_width=True)
                    st.download_button("Download Stops CSV", data=stops_result.to_csv(index=False),
                                       file_name="Fetch_Stops.csv", key="dl_stops")

                    # Map the stops
                    st.markdown("### Stop Locations Map")
                    stop_map = leafmap.Map()
                    stop_map.add_basemap(basemap='OpenStreetMap')                       # free default
                    stop_map.add_basemap(basemap='ROADMAP', show=False)
                    stop_map.add_basemap(basemap='TERRAIN', show=False)
                    stop_map.add_basemap(basemap='HYBRID', show=False)
                    stop_map.add_basemap(basemap='Esri.WorldImagery', show=False)       # free satellite
                    stop_map.add_basemap(basemap='CartoDB.Positron', show=False)        # free light
                    stop_map.add_basemap(basemap='CartoDB.DarkMatter', show=False)      # free dark

                    stop_palette = ["red","blue","green","orange","purple","teal","pink","yellow"]
                    for idx, row in stops_result.iterrows():
                        color = stop_palette[idx % len(stop_palette)]
                        dur_str = f"{row['DURATION_MIN']:.0f} min" if row['DURATION_MIN'] < 60 else f"{row['DURATION_MIN']/60:.1f} hrs"
                        popup_text = (f"Stop #{row['STOP_ID']+1}<br>"
                                      f"Arrive: {row['ARRIVAL']}<br>"
                                      f"Depart: {row['DEPARTURE']}<br>"
                                      f"Duration: {dur_str}<br>"
                                      f"Points: {row['POINT_COUNT']}")
                        if row.get('SOURCE_FILE'):
                            popup_text += f"<br>Source: {row['SOURCE_FILE']}"
                        folium.Circle(
                            location=[row['CENTER_LAT'], row['CENTER_LON']],
                            radius=stop_radius if 'stop_radius' in dir() else 50,
                            color=color, fill=True, fill_color=color, fill_opacity=0.3,
                            popup=popup_text
                        ).add_to(stop_map)
                        folium.Marker(
                            [row['CENTER_LAT'], row['CENTER_LON']],
                            tooltip=f"Stop #{row['STOP_ID']+1} ({dur_str})",
                            icon=folium.Icon(color=color if color in ['red','blue','green','orange','purple'] else 'red', icon='pause', prefix='fa')
                        ).add_to(stop_map)

                    # Fit bounds
                    if len(stops_result) > 0:
                        stop_lats = stops_result['CENTER_LAT'].tolist()
                        stop_lons = stops_result['CENTER_LON'].tolist()
                        sw = [min(stop_lats)-0.001, min(stop_lons)-0.001]
                        ne = [max(stop_lats)+0.001, max(stop_lons)+0.001]
                        stop_map.fit_bounds([sw, ne])

                    stop_map.to_streamlit()

        with adv_tab2:
            # --- Co-Location / Proximity Analysis (Feature #3) ---
            st.subheader(t("hdr_colocation"))
            st.caption("Detect when and where two subjects (from different source files) were at the same place at the same time.")

            if 'SOURCE_FILE' not in preview_data.columns or preview_data['SOURCE_FILE'].nunique() < 2:
                st.info("Co-location analysis requires **2 or more source files** loaded simultaneously. Upload multiple files to use this feature.")
            else:
                sources = sorted(preview_data['SOURCE_FILE'].unique())
                st.write(f"**{len(sources)} source files loaded:** {', '.join(sources)}")

                coloc_time_cols = [c for c in preview_data.columns if 'TIME' in c.upper() or 'DATE' in c.upper()]
                if not coloc_time_cols:
                    st.warning(t("msg_coloc_no_time"))
                else:
                    coloc_c1, coloc_c2, coloc_c3 = st.columns(3)
                    with coloc_c1:
                        coloc_time_col = st.selectbox(t("lbl_time_column"), options=coloc_time_cols, key="coloc_time_col")
                    with coloc_c2:
                        coloc_radius = st.number_input(t("lbl_proximity_radius"), min_value=5, max_value=5000, value=50, step=5, key="coloc_radius",
                                                       help="Maximum distance between two subjects to be considered co-located")
                    with coloc_c3:
                        coloc_time_window = st.number_input(t("lbl_time_window"), min_value=1, max_value=1440, value=10, step=1, key="coloc_window",
                                                            help="Maximum time difference between observations")

                    if st.button(t("btn_run_colocation"), key="run_coloc"):
                        with st.spinner("Analyzing co-location events... This may take a moment for large datasets."):
                            coloc_result = cached_compute_colocation(preview_data, coloc_time_col, coloc_radius, coloc_time_window)
                            safe_session_set('coloc_results', coloc_result)

                    coloc_result = safe_session_get('coloc_results')
                    if coloc_result is not None and isinstance(coloc_result, pandas.DataFrame) and not coloc_result.empty:
                        st.markdown(f"### {len(coloc_result)} Co-Location Event(s) Detected")

                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric("Total Events", len(coloc_result))
                        with col_m2:
                            avg_dist = coloc_result['DISTANCE_M'].mean()
                            st.metric("Avg Distance", f"{avg_dist:.1f} m")
                        with col_m3:
                            pairs = coloc_result.groupby(['SOURCE_A','SOURCE_B']).size().reset_index(name='count')
                            st.metric("Subject Pairs", len(pairs))

                        # Show pair breakdown
                        if len(pairs) > 1:
                            st.markdown("**Events per subject pair:**")
                            for _, pair_row in pairs.iterrows():
                                st.write(f"- {pair_row['SOURCE_A']} ↔ {pair_row['SOURCE_B']}: **{pair_row['count']}** events")

                        st.dataframe(coloc_result, use_container_width=True)
                        st.download_button("Download Co-Location CSV", data=coloc_result.to_csv(index=False),
                                           file_name="Fetch_CoLocation.csv", key="dl_coloc")

                        # Map co-location events
                        st.markdown("### Co-Location Map")
                        coloc_map = leafmap.Map()
                        coloc_map.add_basemap(basemap='OpenStreetMap')                       # free default
                        coloc_map.add_basemap(basemap='ROADMAP', show=False)
                        coloc_map.add_basemap(basemap='TERRAIN', show=False)
                        coloc_map.add_basemap(basemap='HYBRID', show=False)
                        coloc_map.add_basemap(basemap='Esri.WorldImagery', show=False)       # free satellite
                        coloc_map.add_basemap(basemap='CartoDB.Positron', show=False)        # free light
                        coloc_map.add_basemap(basemap='CartoDB.DarkMatter', show=False)      # free dark

                        for idx, row in coloc_result.iterrows():
                            popup_text = (f"Co-Location #{idx+1}<br>"
                                          f"{row['SOURCE_A']} ↔ {row['SOURCE_B']}<br>"
                                          f"Time A: {row['TIME_A']}<br>"
                                          f"Time B: {row['TIME_B']}<br>"
                                          f"Distance: {row['DISTANCE_M']} m<br>"
                                          f"Time Diff: {row['TIME_DIFF_MIN']} min")
                            # Draw line between the two points
                            folium.PolyLine(
                                locations=[[row['LAT_A'], row['LON_A']], [row['LAT_B'], row['LON_B']]],
                                color='red', weight=2, opacity=0.8
                            ).add_to(coloc_map)
                            # Midpoint marker
                            folium.Marker(
                                [row['MIDPOINT_LAT'], row['MIDPOINT_LON']],
                                tooltip=f"Co-Location #{idx+1} ({row['DISTANCE_M']}m, {row['TIME_DIFF_MIN']}min)",
                                popup=popup_text,
                                icon=folium.Icon(color='red', icon='users', prefix='fa')
                            ).add_to(coloc_map)

                        # Fit bounds
                        all_lats = coloc_result['MIDPOINT_LAT'].tolist()
                        all_lons = coloc_result['MIDPOINT_LON'].tolist()
                        if all_lats:
                            sw = [min(all_lats)-0.001, min(all_lons)-0.001]
                            ne = [max(all_lats)+0.001, max(all_lons)+0.001]
                            coloc_map.fit_bounds([sw, ne])

                        coloc_map.to_streamlit()

                    elif coloc_result is not None and isinstance(coloc_result, pandas.DataFrame) and coloc_result.empty:
                        if safe_session_get('coloc_results') is not None:
                            st.info("No co-location events found with the current parameters. Try increasing the radius or time window.")

        with adv_tab3:
            # --- Coordinate Tools (Feature #6) ---
            st.subheader(t("hdr_coord_converter"))
            st.caption("Convert coordinates between formats or inspect what Fetch detected during import.")

            conv_tab1, conv_tab2 = st.tabs([t("tab_single_conv"), t("tab_utm_conv")])

            with conv_tab1:
                st.markdown(t("msg_convert_single"))
                coord_input = st.text_input(t("lbl_enter_coord"),
                                             placeholder='e.g. 40°44\'54"N  or  40 44.9 N  or  40.748333',
                                             key="coord_convert_input")
                if coord_input:
                    parsed = parse_coordinate_value(coord_input)
                    if parsed is not None:
                        # Show all formats
                        abs_val = abs(parsed)
                        d = int(abs_val)
                        m_full = (abs_val - d) * 60
                        m = int(m_full)
                        s = (m_full - m) * 60
                        sign = '-' if parsed < 0 else ''
                        st.success(f"**Decimal:** {parsed:.6f}")
                        st.write(f"**DMS:** {sign}{d}° {m}' {s:.2f}\"")
                        st.write(f"**DDM:** {sign}{d}° {m_full:.4f}'")
                    else:
                        st.error("Could not parse the coordinate. Supported formats: decimal (40.7484), DMS (40°44'54\"N), DDM (40°44.9'N)")

            with conv_tab2:
                st.markdown(t("msg_convert_utm"))
                utm_c1, utm_c2, utm_c3 = st.columns(3)
                with utm_c1:
                    utm_zone = st.number_input(t("lbl_zone_number"), min_value=1, max_value=60, value=17, key="utm_zone")
                with utm_c2:
                    utm_letter = st.text_input(t("lbl_zone_letter"), value="T", max_chars=1, key="utm_letter")
                with utm_c3:
                    _hemi_en = ["Northern", "Southern"]
                    _hemi_tr = [t("northern"), t("southern")]
                    _hemi_sel = st.radio(t("lbl_hemisphere"), options=_hemi_tr, horizontal=True, key="utm_hemi")
                    utm_hemisphere = _hemi_en[_hemi_tr.index(_hemi_sel)]

                utm_e_col, utm_n_col = st.columns(2)
                with utm_e_col:
                    utm_easting = st.number_input(t("lbl_easting"), min_value=100000.0, max_value=999999.0, value=630000.0, step=1.0, key="utm_east")
                with utm_n_col:
                    utm_northing = st.number_input(t("lbl_northing"), min_value=0.0, max_value=9999999.0, value=4833000.0, step=1.0, key="utm_north")

                if st.button(t("btn_convert_utm"), key="convert_utm"):
                    try:
                        letter = utm_letter.upper() if utm_letter else ('N' if utm_hemisphere == "Northern" else 'S')
                        lat, lon = utm_to_latlon(utm_easting, utm_northing, utm_zone, letter)
                        st.success(f"**Latitude:** {lat:.6f}  |  **Longitude:** {lon:.6f}")
                    except Exception as e:
                        st.error(f"Conversion error: {str(e)}")

            # Show coordinate format diagnostics for loaded data
            if preview_data is not None:
                st.markdown("---")
                st.subheader(t("hdr_coord_diag"))
                for coord_col in ['LATITUDE', 'LONGITUDE']:
                    if coord_col in preview_data.columns:
                        fmt = detect_coordinate_format(preview_data[coord_col])
                        sample = preview_data[coord_col].dropna().head(3).tolist()
                        st.write(f"**{coord_col}**: Detected format = `{fmt}` — Sample values: {sample}")

    # Reset one-shot rerun guard so future timezone conversions can trigger a rerun again
    if safe_session_get('_tz_conversion_rerun_done'):
        try:
            safe_session_set('_tz_conversion_rerun_done', False)
        except Exception:
            pass
    
# add a button to open a popup window that will contain hyperlinks
st.markdown("---")

with st.expander("Privacy Statement and API Use"):
    st.write("""
    ## Data Privacy Statement and API Usage Information
    
    We take your privacy seriously. North Loop Consulting will only have temporary access to small portions of data that may be involved in error reporting.  
    This data will not be stored for any period longer than needed to identify and correct any issues, if at all.
                
    We make use of a third party company, Streamlit, to provide hosting for Fetch.  
    For more information about Streamlit and their handling of user data, please refer to their [Privacy Policy](https://streamlit.io/privacy-policy).
    
    For specific information about how Streamlit handles data sets you have uploaded as files, please refer to their 
    [documents on file uploads](https://docs.streamlit.io/knowledge-base/using-streamlit/where-file-uploader-store-when-deleted).
    
    It is always best to avoid uploading sensitive data to any online service. Please do not upload any data that may contain personal identifiable information or sensitive data.

    Fetch is intended to be a free tool available to everyone.  To do this, free resources are used to return information like IP address data.  There are caps on this free usage.  You may run into periods where that cap has been met and these resources are not available. If you would like to explore financial support for the tool to expand these capabilities, I am open to the conversation. Just reach out via the Contact Page on our site.   
    """)
st.markdown(":orange[© 2026 North Loop Consulting - Fetch_v5.3]")
