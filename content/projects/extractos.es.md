---
title: unaudio
date: 2026-04-17
summary: Buscá una frase de una canción de los Redondos y obtené el clip exacto donde se canta. También es mi laboratorio de DevOps de punta a punta, con usuarios reales.
---

Escribí una frase de una canción de Patricio Rey y sus Redonditos de Ricota y obtené
un clip de audio del momento exacto en que se canta, listo para escuchar, descargar o
compartir. El índice cubre 101 canciones y unas 14.600 palabras cantadas, cada una con
su tiempo.

**[Abrir la app ↗](https://unaudio.marso.ar)** · [Código fuente](https://github.com/3ll34ndr0/redo)

## Por qué lo hice

unaudio (antes Extractos) es mi **proyecto de DevOps de punta a punta**: una aplicación
real llevada desde un commit hasta producción en Kubernetes, con GitOps, observabilidad
y seguridad incorporadas desde el principio y no agregadas después.

El objetivo es que **atraiga usuarios reales**. El tráfico real trae problemas reales
(carga, clips lentos, abusos, tiempos mal alineados, caídas), y en eso quiero trabajar:
resolverlos con mi experiencia y usarlos como banco de pruebas para herramientas nuevas.

## El flujo de DevOps

- **CI (GitHub Actions):** tests unitarios, después una prueba de humo del contenedor
  construido (solo lectura, sin root) y tests de navegador con Playwright antes de
  publicar nada.
- **Seguridad:** cada imagen se escanea con Trivy; los hallazgos van a GitHub code
  scanning, y cualquier vulnerabilidad alta o crítica que tenga arreglo bloquea el push
  y el despliegue. Límites de uso por visitante, sin guardar IPs, HTTPS con Cloudflare.
- **Entrega con GitOps:** la imagen va a GHCR, el CI commitea el nuevo tag en los
  manifiestos de Kubernetes y Argo CD lo despliega en un clúster k3s en un VPS.
- **Observabilidad:** métricas de Prometheus (búsquedas, clips, latencia, límites
  alcanzados), logs JSON estructurados y trazas de OpenTelemetry, recolectados por
  Grafana Alloy hacia Grafana Cloud. El dashboard también es código, aplicado con
  OpenTofu desde el CI.
- **Retroalimentación:** los visitantes pueden reportar un clip que no coincide y
  ajustar su inicio y su fin; los reportes se miden como métricas y corrigen los tiempos.

## Cómo se hacen los clips

La voz de cada canción se separa de la música con
[Demucs](https://github.com/facebookresearch/demucs), y después la letra se alinea
contra la pista de voz (alineación CTC con el modelo MMS de torchaudio). Los estribillos
que la letra omite se detectan y se agregan. En canciones etiquetadas a mano, el 93% de
los comienzos de verso caen a menos de 0,3 s. La app busca en un índice SQLite de esos
tiempos por palabra y corta los clips a pedido con ffmpeg.
