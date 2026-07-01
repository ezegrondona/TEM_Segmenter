# TEM Segmenter

![Versión](https://img.shields.io/badge/Versión-1.0.0-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)

## Descripción

**TEM Segmenter** es una aplicación de escritorio desarrollada en Python para asistir en la segmentación de imágenes de Microscopía Electrónica de Transmisión (TEM). 

El objetivo es combinar el poder de la **Inteligencia Artificial (MobileSAM)** con la experiencia del investigador, permitiendo una segmentación rápida, precisa y con flujos de trabajo 100% compatibles con Fiji/ImageJ.

> *La inteligencia artificial propone. El investigador decide.*

---

## 🚀 Características Principales

*   **Segmentación Asistida y Manual**: Utiliza MobileSAM para segmentar estructuras complejas con un solo clic. También incluye herramientas clásicas (polígonos manuales) para ajustes finos.
*   **Gestión de Calibración Inteligente**: Lee automáticamente la calibración de píxeles (escala) incrustada en archivos TIFF generados por microscopios o Fiji. Permite calibración manual mediante trazado de líneas.
*   **Análisis Cuantitativo (Estilo FIJI)**: Mide en tiempo real tus segmentaciones. Calcula Área, Valor Medio (Intensidad), Perímetro, Diámetro de Feret y Descriptores de Forma (Circularidad, Aspect Ratio, Redondez y Solidez).
*   **Exportación Profesional**:
    *   **Fiji ROI Manager**: Exporta tus selecciones directamente a un archivo `RoiSet.zip` nativo de Fiji.
    *   **Imágenes**: Exporta las imágenes con los ROIs incrustados (como contornos vectoriales o relleno sólido transparente), conservando siempre la **resolución original del píxel**.
    *   **Datos**: Exporta los resultados de todas las mediciones a un archivo `.csv` compatible con Excel y GraphPad.
*   **Sistema de Sesiones Automáticas**: Si cerrás el programa, tu progreso se guarda. Al volver a cargar el proyecto, todas tus máscaras y calibraciones siguen ahí.

---

## 💻 Instalación (Sin código ni terminal)

Este proyecto fue diseñado para investigadores. No necesitas saber de programación ni tocar la consola para usarlo.

1. Ve a la sección **Releases** en este repositorio.
2. Descarga el instalador **`Instalar_TEM_Segmenter.exe`**.
3. Haz doble clic en el instalador. Te dejará un acceso directo en tu escritorio.
4. ¡Listo! La primera vez que abras el programa, el sistema detectará automáticamente si necesitas dependencias o modelos de IA y los descargará por ti de manera transparente.

---

## 👨‍🔬 Uso Rápido

1. Haz clic en **Cargar imagen** (soporta `.tif`, `.png`, `.jpg`).
2. Revisa la escala en el panel derecho. Si no tiene, usa el botón **Calibrar**.
3. Selecciona **Segmentación Automática** y haz clic sobre las estructuras que deseas separar.
4. Presiona **ENTER** para aceptar la máscara propuesta o **ESCAPE** para cancelar.
5. Revisa tus datos en **Medir Segmentaciones** o exporta tu trabajo desde **Archivo > Exportar...**.

---

## Estado del Proyecto

**Versión:** 1.0.0 (Estable)  
El núcleo de la aplicación, el motor de Inteligencia Artificial (MobileSAM), el panel interactivo y los módulos de exportación están 100% operativos.