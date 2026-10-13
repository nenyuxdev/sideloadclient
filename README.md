# SideloadClient

Una herramienta CLI portátil desarrollada en Python diseñada específicamente para la *scene* de Android. Permite flashear de forma limpia y rápida Custom ROMs, Custom Recoveries, imágenes de root (Magisk/KernelSU/APatch) y kernels (en formato AnyKernel) sin necesidad de instalaciones previas de controladores o configuraciones en el `PATH` del sistema.

---

## 🚀 Características principales

* **Portabilidad total:** Integra de forma nativa los binarios de `platform-tools` (`adb` y `fastboot`) para **Windows**, **Linux** y **macOS**.
* **Flasheo versátil:**
  * **Modo Sideload:** Compatible con archivos `.zip` (Custom ROMs, Kernels AnyKernel3, Magisk, etc.).
  * **Modo Fastboot:** Flasheo automático de imágenes `.img` en particiones clave (`boot`, `recovery`, `dtbo`, `dtb`, `vendor_boot`, `init_boot`, `vbmeta`).
* **Detección inteligente de particiones (A/B):** Identifica automáticamente el slot activo (`_a` o `_b`) en dispositivos modernos y asigna la partición correspondiente según el nombre del archivo.
* **Automatización de estados:** Detecta si el dispositivo está en modo normal, recovery o fastboot, ofreciendo la opción de reiniciarlo e ingresar al modo adecuado automáticamente.
* **Interfaz visual limpia:** Muestra barras de progreso interactivas en la terminal durante el proceso de transferencia y flasheo.
